#!/usr/bin/env python3
"""G12 resolver: rungs 1-2 of the G1-enablement ladder.

Rung 1 — name resolution (the linker perspective): every `use` binds a
declared profile from the universe (profiles/**/*.oaas); a use binds the
profile id's TERMINAL SEGMENT as the flow's namespace (ecosystem.onnx ->
onnx::). Namespace collisions are index-time errors — the language-level
analog of dependency confusion (security control, not convenience).
Dataflow wiring: every edge source is an io name or a produced value;
declared outputs are produced.

Rung 2 — oracles: ecosystem namespaces check ops (name@version) against
registry/entries/<eco>.yaml operators; domain namespaces check ops against
operator/concept declarations in the profile's own directory. Pin
consistency: profile.oaas pins == VERSIONS pins.

Rung 3 (types/shapes) is OUT of scope, deliberately (ONNX precedent:
checker vs shape inference are separate).

Refusals: conformance/resolution/*.flow with `// MUST-FAIL-RESOLUTION:`
markers must parse but MUST fail resolution — the boundary obligation
applied voluntarily to a new acceptance layer.

Metric: RESOLUTION RATE = resolved references / total references
(north-star metric #1). Gate G12 requires 1.0 with zero errors.
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oaas_read import read_flow, read_vocab

MARKER = re.compile(r"^// MUST-FAIL-RESOLUTION\b", re.M)
XMARK = re.compile(r"^// EXPECTED-FAIL\b", re.M)


def build_universe():
    profiles, ns_map, dir_vocab, errors = {}, {}, {}, []
    for f in sorted(ROOT.glob("profiles/**/*.oaas")):
        v = read_vocab(f.read_text())
        d = str(f.parent.relative_to(ROOT))
        dv = dir_vocab.setdefault(d, {"operators": set(), "concepts": set()})
        dv["operators"].update(v["operators"])
        dv["concepts"].update(v["concepts"])
        for pid in v["profiles"]:
            kind = "ecosystem" if "profiles/ecosystem/" in str(f) else "domain"
            profiles[pid] = {"file": f, "dir": d, "kind": kind, "pins": v["pins"]}
            term = pid.split(".")[-1]
            if term in ns_map and ns_map[term] != pid:
                errors.append(f"namespace collision: {term!r} claimed by "
                              f"{ns_map[term]} and {pid} (dependency-confusion "
                              "control: terminal segments must be unique)")
            ns_map[term] = pid
    return profiles, ns_map, dir_vocab, errors


def read_registry():
    out = {}
    for y in sorted((ROOT / "registry" / "entries").glob("*.yaml")):
        name, ops = None, []
        for line in y.read_text().splitlines():
            m = re.match(r"name:\s*(\S+)", line)
            if m:
                name = m.group(1)
            m = re.match(r"operators:\s*\[(.*?)\]", line)
            if m:
                ops = [x.strip() for x in m.group(1).split(",") if x.strip()]
        if name:
            out[name] = ops
    return out


def read_versions_pins(path):
    pins = {}
    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        m = re.match(r"([\w. ]+?)\s*=\s*(\S+)", line)
        if m:
            pins[m.group(1).strip()] = m.group(2)
    return pins


def resolve_flow(text, profiles, ns_map, dir_vocab, registry):
    """Returns (errors, infos, refs_total, refs_resolved)."""
    flow = read_flow(text)
    errors, infos = [], []
    total = resolved = 0

    bound = {}                                   # namespace -> profile id
    for u in flow["uses"]:
        total += 1
        if u in profiles:
            resolved += 1
            bound[u.split(".")[-1]] = u
        else:
            hint = difflib.get_close_matches(u, profiles.keys(), 1)
            errors.append(f"DANGLING-USE: {u!r} not declared in the universe"
                          + (f" — did you mean {hint[0]!r}?" if hint else ""))

    io_names = {n for _, n, _, _, _ in flow["ios"]}
    produced = {d for *_, dsts in flow["edges"] for d in dsts}
    for srcs, ns, op, ver, dsts in flow["edges"]:
        total += 1
        if ns is None:
            errors.append(f"UNQUALIFIED-OP: {op!r} — ops must be "
                          "namespace-qualified through a use binding")
            continue
        if ns not in bound:
            hint = difflib.get_close_matches(ns, bound.keys(), 1)
            errors.append(f"UNBOUND-NAMESPACE: {ns!r} on op {op!r} — no use "
                          "binds it" + (f" (bound here: {sorted(bound)})"
                                        if bound else " (no uses bound)"))
            continue
        pid = bound[ns]
        p = profiles[pid]
        if p["kind"] == "ecosystem":
            oracle = registry.get(ns, [])
            want = f"{op}@{ver}" if ver is not None else op
            names = {o.split("@")[0] for o in oracle}
            if want in oracle or (ver is None and op in names):
                resolved += 1
            else:
                hint = difflib.get_close_matches(op, names, 1)
                errors.append(f"UNDECLARED-OP: {ns}::{want} not in registry "
                              f"oracle for {ns!r}"
                              + (f" — did you mean {hint[0]!r}?" if hint else ""))
        else:
            dv = dir_vocab.get(p["dir"], {"operators": set(), "concepts": set()})
            known = dv["operators"] | dv["concepts"]
            if op in known:
                resolved += 1
            else:
                hint = difflib.get_close_matches(op, known, 1)
                errors.append(f"UNDECLARED-OP: {ns}::{op} not declared in "
                              f"{p['dir']}/"
                              + (f" — did you mean {hint[0]!r}?" if hint else ""))
        for s in srcs:
            if s not in io_names and s not in produced:
                errors.append(f"BROKEN-WIRING: edge source {s!r} is neither an "
                              "io declaration nor produced by any edge")
    for role, n, *_ in flow["ios"]:
        if role == "output" and n not in produced:
            errors.append(f"BROKEN-WIRING: declared output {n!r} is never produced")
    consumed = {s for srcs, *_ in flow["edges"] for s in srcs}
    for d in sorted(produced - consumed - io_names):
        infos.append(f"unused value {d!r} (produced, never consumed, not an output)")
    return errors, infos, total, resolved


def main():
    profiles, ns_map, dir_vocab, errors0 = build_universe()
    registry = read_registry()
    failures = list(errors0)
    total = resolved = 0

    for f in sorted((ROOT / "conformance" / "corpus").glob("*.flow")):
        text = f.read_text()
        if XMARK.search("\n".join(text.splitlines()[:12])):
            continue
        errs, infos, t, r = resolve_flow(text, profiles, ns_map, dir_vocab, registry)
        total += t
        resolved += r
        status = "RESOLVE" if not errs else "FAIL"
        print(f"{status:8} {f.relative_to(ROOT)}"
              + "".join(f"\n         - {e}" for e in errs)
              + "".join(f"\n         · {i}" for i in infos))
        failures += [f"{f.name}: {e}" for e in errs]

    # pin consistency: profile.oaas is canonical; VERSIONS must mirror it
    for pf in sorted(ROOT.glob("profiles/ecosystem/*/profile.oaas")):
        vf = pf.parent / "VERSIONS"
        if not vf.exists():
            continue
        ppins = read_vocab(pf.read_text())["pins"]
        vpins = read_versions_pins(vf)
        for k, v in ppins.items():
            if vpins.get(k) != v:
                failures.append(f"PIN-DRIFT {pf.parent.name}: {k} = {v} "
                                f"(profile.oaas) vs {vpins.get(k)} (VERSIONS)")
        print(f"PINS-OK  {pf.relative_to(ROOT)} == VERSIONS"
              if not any(k for k, v in ppins.items() if vpins.get(k) != v)
              else f"PINDRIFT {pf.relative_to(ROOT)}")

    # resolution refusals: must parse, MUST fail resolution
    for f in sorted((ROOT / "conformance" / "resolution").glob("*.flow")):
        text = f.read_text()
        if not MARKER.search("\n".join(text.splitlines()[:12])):
            failures.append(f"{f.name}: refusal fixture lacks "
                            "// MUST-FAIL-RESOLUTION marker")
            continue
        errs, _, _, _ = resolve_flow(text, profiles, ns_map, dir_vocab, registry)
        if errs:
            print(f"REJECT   {f.relative_to(ROOT)}")
        else:
            failures.append(f"XPASS {f.name} — resolution accepts what it "
                            "must refuse (regression, never a ritual)")
            print(f"XPASS    {f.relative_to(ROOT)}")

    rate = resolved / total if total else 0.0
    print(f"\nresolution rate: {resolved}/{total} = {rate:.2f} "
          "(north-star metric #1; gate requires 1.00)")
    if failures or rate < 1.0:
        for x in failures:
            print(f"FAIL {x}", file=sys.stderr)
        sys.exit(1)
    print("Resolution contract satisfied: every reference finds its universal.")


if __name__ == "__main__":
    main()
