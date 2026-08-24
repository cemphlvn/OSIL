//! C emission from a selected realization.
//!
//! Every emitted file carries a provenance header naming the guard that
//! licensed the realization. This is the auditability difference against
//! `-ffast-math`: fast-math is a global, unscoped compiler flag that licenses
//! every reassociation in the translation unit and records nothing. Here the
//! licence is per-realization, declared in the SIR, and reproduced in the
//! artifact — you can read the output and see WHY it was legal.

use crate::sir::Case;
use crate::{Kind, Realization, Source};

/// C operator and identity element for a declared reduction operator.
fn op_c(op: &str, suffix: &str) -> (&'static str, String) {
    match op {
        "mul" => ("*", format!("1.0{suffix}")),
        "add" => ("+", format!("0.0{suffix}")),
        other => panic!("supported reduction ops are mul/add, got `{other}`"),
    }
}

fn binop_c(op: &str) -> &'static str {
    match op {
        "mul" => "*",
        "add" => "+",
        "sub" => "-",
        other => panic!("supported zip ops are mul/add/sub, got `{other}`"),
    }
}

/// The C expression for the source element at `i + off`.
fn elem(src: &Source, off: i64) -> String {
    match src {
        Source::Repeat { val } => val.clone(), // loop-invariant: no index
        Source::Range { arr } => format!("{arr}[i + {off}]"),
        Source::Zip { op, a, b } => {
            let o = binop_c(op);
            format!("({a}[i + {off}] {o} {b}[i + {off}])")
        }
    }
}

/// Parameter list implied by the source shape.
fn signature(src: &Source, cty: &str) -> String {
    match src {
        Source::Repeat { val } => format!("{cty} {val}, int n"),
        Source::Range { arr } => format!("const {cty} * restrict {arr}, int n"),
        Source::Zip { a, b, .. } => format!(
            "const {cty} * restrict {a}, const {cty} * restrict {b}, int n"
        ),
    }
}

pub fn emit_c(case: &Case, r: &Realization) -> String {
    let elem_ty = case
        .constraints
        .get("element_type")
        .map(String::as_str)
        .unwrap_or("f32");
    let (cty, suffix, size, powf) = match elem_ty {
        "f64" => ("double", "", 8usize, "pow"),
        _ => ("float", "f", 4usize, "powf"),
    };
    let (o, id) = op_c(&r.op, suffix);
    let n = r.n;

    // FP CONTRACTION is a declared licence, not a compiler flag.
    // Emitted as a SCOPE-LOCAL pragma rather than -ffp-contract, so the
    // licence applies exactly where the SIR declared it and nowhere else --
    // finer-grained than any translation-unit flag can express. Fusing a
    // multiply and add into one FMA rounds once instead of twice, so it
    // changes the result and therefore needs its own guard.
    let contract = case.guards.get("fp_contraction")
        .map(|v| v == "permitted").unwrap_or(false);

    let licence = case
        .guards
        .iter()
        .map(|(k, v)| format!("//   {k} = {v}"))
        .collect::<Vec<_>>()
        .join("\n");

    let (realization, body) = match &r.kind {
        Kind::Chain => (
            "chain (sequential fold — requires no guard)".to_string(),
            format!(
"    {cty} acc = {id};
    for (int i = 0; i < {n}; ++i) acc = acc {o} {e};
    return acc;",
                e = elem(&r.src, 0)
            ),
        ),

        Kind::PowI => {
            let k = match &r.src {
                Source::Repeat { val } => val.clone(),
                _ => panic!("powi realization requires a `repeat` source"),
            };
            (
                "closed form (O(1) — collapses the loop entirely)".to_string(),
                format!("    return {powf}({k}, (({cty}){n}));"),
            )
        }

        Kind::Scale => {
            let k = match &r.src {
                Source::Repeat { val } => val.clone(),
                _ => panic!("scale realization requires a `repeat` source"),
            };
            (
                "closed form (O(1) — collapses the loop entirely)".to_string(),
                format!("    return {k} * (({cty}){n});"),
            )
        }

        Kind::Lanes { w, i: il } => {
            let bytes = size * *w as usize;
            let decls = (0..*il)
                .map(|k| {
                    format!(
                        "    vec_t acc{k} = {{ {} }};",
                        vec![id.clone(); *w as usize].join(", ")
                    )
                })
                .collect::<Vec<_>>()
                .join("\n");
            let step = w * il;
            let updates = (0..*il)
                .map(|k| {
                    let load = (0..*w)
                        .map(|l| elem(&r.src, k * w + l))
                        .collect::<Vec<_>>()
                        .join(", ");
                    if contract {
                        format!("        acc{k} = acc{k} {o} (vec_t){{ {load} }};")
                    } else {
                        format!("        {{ vec_t v = {{ {load} }}; acc{k} = acc{k} {o} v; }}")
                    }
                })
                .collect::<Vec<_>>()
                .join("\n");
            let fold_acc = (1..*il)
                .map(|k| format!("    acc0 = acc0 {o} acc{k};"))
                .collect::<Vec<_>>()
                .join("\n");
            let combine = (0..*w)
                .map(|l| format!("acc0[{l}]"))
                .collect::<Vec<_>>()
                .join(&format!(" {o} "));
            (
                format!(
                    "lanes width={w} interleave={il} ({} independent chains{})",
                    w * il,
                    if contract { ", fp contraction licensed" } else { "" }
                ),
                format!(
"    typedef {cty} vec_t __attribute__((vector_size({bytes})));
{decls}
    int i = 0;
    for (; i + {step} <= {n}; i += {step}) {{
{updates}
    }}
    // combine the independent chains — itself a reassociation, same licence
{fold_acc}
    {cty} r = {combine};
    // remainder, in declaration order
    for (; i < {n}; ++i) r = r {o} {e};
    return r;",
                    e = elem(&r.src, 0),
                ),
            )
        }
    };

    format!(
"// GENERATED by osil-opt — do not edit.
// kernel       : {name}
// SIR term     : {sir}
// realization  : {realization}
// modeled cost : {cost:.0}
// licensed by  :
{licence}
//
// Provenance: TSVC_2 (github.com/UoB-HPC/TSVC_2, BSD-3-Clause).
// The proof obligation the compiler could not discharge is DECLARED above,
// not inferred.

#include <math.h>

{cty} osil_{name}({sig}) {{
{pragma}    (void)n;
{body}
}}
",
        name = case.name,
        sir = case.sir,
        cost = r.modeled,
        sig = signature(&r.src, cty),
        pragma = if contract { "    #pragma clang fp contract(fast)\n" } else { "" },
    )
}
