//! osil-opt — OSIL semantic optimizer.
//!
//! Thesis under test: a transformation that LLVM must REFUSE for lack of a
//! proof becomes legal when OSIL-SIR *declares* the semantic regime. The
//! optimizer never rediscovers loop structure; it selects a realization from
//! the declared semantic optimization space.
//!
//! NO BINDER. Sources are combinators (`range`/`repeat`/`zip`), so a loop nest
//! is a ground term without unrolling — cf. Glenside's access patterns, and
//! unlike Diospyros, which fully unrolls (docs/research/U6). At TSVC's
//! LEN_1D=32000 unrolling is infeasible; here the e-graph is O(1) in extent.

use egg::*;
use std::collections::BTreeMap;

mod emit;
mod sir;

define_language! {
    pub enum Osil {
        Num(i64),

        // ---- array-producing sources (binder-free combinators) ----
        "range"  = Range([Id; 2]),  // (range a n)      — array `a`, length n
        "repeat" = Repeat([Id; 2]), // (repeat k n)     — n copies of scalar k
        "zip"    = Zip([Id; 4]),    // (zip op a b n)   — elementwise op(a,b)

        // ---- OSIL-SIR: what the computation IS ----
        "reduce" = Reduce([Id; 2]), // (reduce op source)

        // ---- OSIL-CIR: how it is computed ----
        "chain"  = Chain([Id; 2]),  // sequential fold
        "lanes"  = Lanes([Id; 4]),  // (lanes op source w i) — w*i independent chains
        "powi"   = PowI([Id; 2]),   // (powi k n)  — closed form, O(1)
        "scale"  = Scale([Id; 2]),  // (scale k n) — closed form, O(1)

        Symbol(Symbol),
    }
}

/// Rewrites are GUARD-GATED DATA, not code (ADR-0009).
///
/// Two INDEPENDENT guards, licensing different things:
///   numeric_semantics = reassociable
///       licenses reordering a reduction into independent chains (`lanes`).
///   closed_form = permitted
///       licenses replacing an operation SEQUENCE with a closed form whose
///       implementation error is bounded but different in kind (`powi`).
///       Reassociation alone does NOT license this — a library `powf` is not
///       a reordering of multiplies — so it gets its own guard.
fn rules(guards: &BTreeMap<String, String>) -> Vec<Rewrite<Osil, ()>> {
    let g = |k: &str| guards.get(k).map(String::as_str).unwrap_or("");

    // Always legal: any reduction is realizable as a sequential fold.
    let mut rs: Vec<Rewrite<Osil, ()>> =
        vec![rewrite!("reduce-to-chain"; "(reduce ?op ?s)" => "(chain ?op ?s)")];

    if g("numeric_semantics") == "reassociable" {
        // The realization SPACE, not one realization: NEON is 128-bit (4xf32)
        // so width is pinned; the number of interleaved accumulator chains is
        // free. Extraction chooses.
        for i in [1, 2, 4, 8] {
            rs.push(
                Rewrite::new(
                    format!("reduce-to-lanes-w4-i{i}"),
                    "(reduce ?op ?s)".parse::<Pattern<Osil>>().unwrap(),
                    format!("(lanes ?op ?s 4 {i})").parse::<Pattern<Osil>>().unwrap(),
                )
                .unwrap(),
            );
        }
    }

    if g("closed_form") == "permitted" {
        // A product of n identical factors has a closed form. This collapses
        // O(n) work to O(1) — an ASYMPTOTIC change, not a constant factor.
        rs.push(rewrite!("mul-repeat-closed";
            "(reduce mul (repeat ?k ?n))" => "(powi ?k ?n)"));
        rs.push(rewrite!("add-repeat-closed";
            "(reduce add (repeat ?k ?n))" => "(scale ?k ?n)"));
    }
    rs
}

// ---------------------------------------------------------------- realization

#[derive(Debug, Clone, PartialEq)]
pub enum Source {
    Range { arr: String },
    Repeat { val: String },
    Zip { op: String, a: String, b: String },
}

#[derive(Debug, Clone, PartialEq)]
pub enum Kind {
    Chain,
    Lanes { w: i64, i: i64 },
    PowI,
    Scale,
}

#[derive(Debug, Clone)]
pub struct Realization {
    pub kind: Kind,
    pub op: String,
    pub src: Source,
    pub n: i64,
    pub modeled: f64,
}

// Microarchitectural constants — DATA, not code.
//
// The model's FORM (below) is hand-written and auditable. Its two physical
// constants are read from calibration/constants.toml, fitted against measured
// ground truth by calibration/fit.py under a held-out pick-correctness gate.
// The fallbacks are the original unmeasured ASSUMPTION values, kept only so
// the tool runs before any calibration exists — it says so when it uses them.
const LIBM_CALL: f64 = 40.0; // one powf, amortized

#[derive(Debug, Clone, Copy)]
pub struct Constants {
    pub mul_latency: f64,
    pub lanes_per_cycle: f64,
    pub calibrated: bool,
}

impl Constants {
    fn load() -> Self {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("calibration/constants.toml");
        let Ok(text) = std::fs::read_to_string(&path) else {
            return Self { mul_latency: 4.0, lanes_per_cycle: 8.0, calibrated: false };
        };
        let get = |key: &str| -> Option<f64> {
            text.lines()
                .find(|l| l.trim_start().starts_with(key))?
                .split('=').nth(1)?
                .split('#').next()?
                .trim().parse().ok()
        };
        match (get("mul_latency_cycles"), get("lanes_per_cycle")) {
            (Some(m), Some(l)) => Self { mul_latency: m, lanes_per_cycle: l, calibrated: true },
            _ => Self { mul_latency: 4.0, lanes_per_cycle: 8.0, calibrated: false },
        }
    }
}

/// Cost of producing ONE element of the source (per-element work).
fn src_cost(s: &Source) -> f64 {
    match s {
        Source::Repeat { .. } => 0.0, // loop-invariant: no load, no work
        Source::Range { .. } => 1.0,  // one load
        Source::Zip { .. } => 2.0,    // two loads + one op
    }
}

/// Latency-bound reduction cost. A reduction's runtime is governed by the
/// longest dependence chain, not the operation count — which is why
/// interleaving matters and why `chain` is slow.
fn model(kind: &Kind, src: &Source, n: i64, c: Constants) -> f64 {
    let nf = n as f64;
    let per = src_cost(src);
    match kind {
        Kind::PowI | Kind::Scale => LIBM_CALL, // O(1) — independent of n
        Kind::Chain => nf * (c.mul_latency + per),
        Kind::Lanes { w, i } => {
            let chains = (*w * *i) as f64;
            let latency = (nf / chains) * c.mul_latency;
            let throughput = nf * (1.0 + per) / c.lanes_per_cycle;
            let combine = (chains - 1.0) * c.mul_latency;
            latency.max(throughput) + combine
        }
    }
}

fn leaf_num(eg: &EGraph<Osil, ()>, id: Id) -> Option<i64> {
    eg[id].nodes.iter().find_map(|n| match n {
        Osil::Num(v) => Some(*v),
        _ => None,
    })
}

fn leaf_sym(eg: &EGraph<Osil, ()>, id: Id) -> Option<String> {
    eg[id].nodes.iter().find_map(|n| match n {
        Osil::Symbol(s) => Some(s.to_string()),
        _ => None,
    })
}

/// Read a source e-class back into a `Source` + extent.
fn read_src(eg: &EGraph<Osil, ()>, id: Id) -> Option<(Source, i64)> {
    eg[id].nodes.iter().find_map(|n| match n {
        Osil::Range([a, n_]) => Some((
            Source::Range { arr: leaf_sym(eg, *a)? },
            leaf_num(eg, *n_)?,
        )),
        Osil::Repeat([k, n_]) => Some((
            Source::Repeat { val: leaf_sym(eg, *k)? },
            leaf_num(eg, *n_)?,
        )),
        Osil::Zip([o, a, b, n_]) => Some((
            Source::Zip {
                op: leaf_sym(eg, *o)?,
                a: leaf_sym(eg, *a)?,
                b: leaf_sym(eg, *b)?,
            },
            leaf_num(eg, *n_)?,
        )),
        _ => None,
    })
}

/// Enumerate every realization in the root e-class and score it.
///
/// Deterministic: candidates sort by (cost, debug form) — a total order — so
/// ties never resolve by hash iteration order. `egg` is built with its
/// `deterministic` feature for the same reason.
fn realizations(eg: &EGraph<Osil, ()>, root: Id, c: Constants) -> Vec<Realization> {
    let mut out: Vec<Realization> = vec![];
    for node in &eg[root].nodes {
        let r = match node {
            Osil::Chain([op, s]) => read_src(eg, *s).map(|(src, n)| Realization {
                kind: Kind::Chain,
                op: leaf_sym(eg, *op).unwrap_or_default(),
                src,
                n,
                modeled: 0.0,
            }),
            Osil::Lanes([op, s, w, i]) => match (leaf_num(eg, *w), leaf_num(eg, *i)) {
                (Some(w), Some(i)) => read_src(eg, *s).map(|(src, n)| Realization {
                    kind: Kind::Lanes { w, i },
                    op: leaf_sym(eg, *op).unwrap_or_default(),
                    src,
                    n,
                    modeled: 0.0,
                }),
                _ => None,
            },
            Osil::PowI([k, n_]) => match (leaf_sym(eg, *k), leaf_num(eg, *n_)) {
                (Some(val), Some(n)) => Some(Realization {
                    kind: Kind::PowI,
                    op: "mul".into(),
                    src: Source::Repeat { val },
                    n,
                    modeled: 0.0,
                }),
                _ => None,
            },
            Osil::Scale([k, n_]) => match (leaf_sym(eg, *k), leaf_num(eg, *n_)) {
                (Some(val), Some(n)) => Some(Realization {
                    kind: Kind::Scale,
                    op: "add".into(),
                    src: Source::Repeat { val },
                    n,
                    modeled: 0.0,
                }),
                _ => None,
            },
            _ => None, // `reduce` itself is UNREALIZED — never emittable
        };
        if let Some(mut r) = r {
            r.modeled = model(&r.kind, &r.src, r.n, c);
            out.push(r);
        }
    }
    out.sort_by(|a, b| {
        a.modeled
            .partial_cmp(&b.modeled)
            .unwrap()
            .then_with(|| format!("{:?}", a.kind).cmp(&format!("{:?}", b.kind)))
    });
    out
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: osil-opt <case.osil> [--emit out.c] [--pick <kind>]");
        std::process::exit(2);
    }
    let src = std::fs::read_to_string(&args[1]).expect("read case");
    let case = sir::parse(&src).expect("parse SIR");

    println!("== OSIL SIR ==");
    println!("  kernel   : {}", case.name);
    println!("  SIR term : {}", case.sir);
    println!("  guards   : {:?}", case.guards);

    let expr: RecExpr<Osil> = case.sir.parse().expect("parse SIR term");
    let rs = rules(&case.guards);
    println!("  admitted rewrites: {}", rs.len());

    let runner = Runner::default()
        .with_expr(&expr)
        .with_iter_limit(30)
        .with_node_limit(100_000)
        .run(&rs);

    let root = runner.egraph.find(runner.roots[0]);
    let consts = Constants::load();
    let cands = realizations(&runner.egraph, root, consts);

    println!("\n== semantic optimization space ==");
    println!(
        "  e-graph: {} classes, {} nodes, stop={:?}",
        runner.egraph.number_of_classes(),
        runner.egraph.total_number_of_nodes(),
        runner.stop_reason.as_ref().unwrap()
    );
    println!("  cost model: mul_latency={:.2} lanes_per_cycle={:.2}  [{}]",
        consts.mul_latency, consts.lanes_per_cycle,
        if consts.calibrated { "calibrated" } else { "UNCALIBRATED defaults" });
    println!("  {} valid realization(s):", cands.len());
    for (k, r) in cands.iter().enumerate() {
        println!(
            "    {} {:<24} modeled cost {:>10.0}",
            if k == 0 { "->" } else { "  " },
            format!("{:?}", r.kind),
            r.modeled
        );
    }

    // `--pick` overrides SELECTION only, never LEGALITY: it can choose any
    // realization already in the licensed space and cannot conjure one the
    // guards did not admit. Used by the harness to test the model's pick.
    let chosen = match args.iter().position(|a| a == "--pick") {
        Some(p) => {
            let want = &args[p + 1];
            cands
                .iter()
                .find(|r| format!("{:?}", r.kind).replace(' ', "").contains(want.as_str()))
                .unwrap_or_else(|| panic!("`{want}` not in the licensed space"))
                .clone()
        }
        None => cands.first().expect("no realization").clone(),
    };
    println!("  selected: {:?}", chosen.kind);

    if let Some(p) = args.iter().position(|a| a == "--emit") {
        let out = &args[p + 1];
        std::fs::write(out, emit::emit_c(&case, &chosen)).expect("write emit");
        println!("  emitted C -> {}", out);
    }
}
