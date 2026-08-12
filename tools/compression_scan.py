#!/usr/bin/env python3
"""Compression scan: the system's size through the compression-ecosystem lens.

The founding text's caveat is normative here: "The compression is not mainly
fewer bytes... it is compressing a configuration/action space into a
higher-order semantic declaration." So size is reported on a LADDER:
bytes -> tokens -> productions -> concepts. A compression claim must name its
rung; byte ratios are the crudest rung and are reported honestly even when
unflattering (tiny graphs: protobuf beats text).

Axes:
  A. interop — native .onnx bytes vs .flow projection text, passthrough split
     out (needs onnx; run via `just compress`).
  B. corpus ladder — bytes / tokens / productions per fixture.
  C. cover direction — greedy minimal covering set of fixtures over the
     production inventory ("the corpus's books") + redundancy profile.
  D. name direction — recurring token n-grams across fixtures = unnamed
     compression opportunities (candidate concepts/sugar; PROPOSE-ONLY).

Writes conformance/compression/baselines.yaml and
docs/reports/compression-<date>.md.
"""
import datetime
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oaas_check import tokenize, Parser, ALL_PRODUCTIONS

MARKER = re.compile(r"^// EXPECTED-FAIL\b", re.M)


def fixture_stats():
    rows = []
    for p in sorted((ROOT / "conformance" / "corpus").iterdir()):
        if p.suffix not in (".oaas", ".flow"):
            continue
        src = p.read_text()
        if MARKER.search("\n".join(src.splitlines()[:12])):
            rows.append((p.stem, p.suffix, len(src.encode()), None, None))
            continue
        toks = [t for t in tokenize(src) if t.kind != "eof"]
        cov = set()
        parser = Parser(tokenize(src), cov, set())
        (parser.parse_flow_document if p.suffix == ".flow"
         else parser.parse_oaas_document)()
        rows.append((p.stem, p.suffix, len(src.encode()), len(toks), cov))
    return rows


def greedy_cover(rows):
    universe = set(ALL_PRODUCTIONS)
    remaining, chosen = set(universe), []
    pool = {stem: cov for stem, _, _, _, cov in rows if cov}
    while remaining:
        stem = max(pool, key=lambda s: len(pool[s] & remaining))
        gain = pool[stem] & remaining
        if not gain:
            break
        chosen.append((stem, sorted(gain)))
        remaining -= gain
    return chosen, remaining


def redundancy(rows):
    counts = {p: 0 for p in ALL_PRODUCTIONS}
    for _, _, _, _, cov in rows:
        for p in (cov or ()):
            counts[p] += 1
    return counts


def ngrams(rows):
    grams = {}
    for stem, suffix, _, _, cov in rows:
        if cov is None:
            continue
        src = (ROOT / "conformance" / "corpus" / f"{stem}{suffix}").read_text()
        texts = [t.text for t in tokenize(src) if t.kind != "eof"]
        seen = set()
        for n in range(3, 9):
            for i in range(len(texts) - n + 1):
                g = tuple(texts[i:i + n])
                if g in seen:
                    continue
                seen.add(g)
                idents = sum(1 for x in g if x[0].isalpha() or x[0] == "_")
                if idents >= 2:
                    grams.setdefault(g, set()).add(stem)
    cands = sorted(((g, fs) for g, fs in grams.items() if len(fs) >= 3),
                   key=lambda kv: (-len(kv[0]), -len(kv[1])))

    def is_sub(small, big):
        return any(big[i:i + len(small)] == small
                   for i in range(len(big) - len(small) + 1))

    kept = []
    for g, fs in cands:
        if any(is_sub(g, k) and fs <= kfs for k, kfs in kept):
            continue
        kept.append((g, fs))
    kept.sort(key=lambda kv: -(len(kv[0]) * len(kv[1])))
    return kept[:8]


def interop_axis():
    try:
        import onnx  # noqa: F401
    except ImportError:
        return None
    from onnx_roundtrip import export_flow
    out = []
    cases_dir = ROOT / "conformance" / "interop" / "onnx" / "cases"
    for case_path in sorted(cases_dir.glob("*.py")):
        spec = importlib.util.spec_from_file_location(case_path.stem, case_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        model = mod.make_model()
        native = len(model.SerializeToString())
        text, passthrough = export_flow(model)
        tbytes = len(text.encode())
        ttoks = len([t for t in tokenize(text) if t.kind != "eof"])
        pbytes = len(json.dumps(passthrough).encode())
        out.append({"case": case_path.stem, "native_bytes": native,
                    "flow_bytes": tbytes, "flow_tokens": ttoks,
                    "passthrough_bytes": pbytes})
    return out


def main():
    today = datetime.date.today().isoformat()
    rows = fixture_stats()
    parsed = [r for r in rows if r[4]]
    total_bytes = sum(r[2] for r in rows)
    total_toks = sum(r[3] for r in parsed)
    chosen, uncovered = greedy_cover(rows)
    red = redundancy(rows)
    fat = sorted(red.items(), key=lambda kv: -kv[1])[:5]
    thin = [p for p, c in red.items() if c == 1]
    names = ngrams(rows)
    interop = interop_axis()

    lines = [f"# Compression report — {today}",
             "Rung discipline: every claim names its ladder rung "
             "(bytes -> tokens -> productions -> concepts).", "",
             "## B. Corpus ladder",
             f"- {len(rows)} fixtures ({len(rows) - len(parsed)} expected-fail, "
             f"excluded from parse rungs)",
             f"- bytes: {total_bytes} · tokens: {total_toks} · "
             f"productions: {len(ALL_PRODUCTIONS)} (all fired)", "",
             "## C. Cover direction — the corpus's 'books'",
             f"Greedy covering set: {len(chosen)} fixtures cover all "
             f"{len(ALL_PRODUCTIONS)} productions"
             + (f" (UNCOVERED: {sorted(uncovered)})" if uncovered else "") + ":"]
    for stem, gain in chosen:
        lines.append(f"- {stem}  (+{len(gain)}: {', '.join(gain[:6])}"
                     + ("…" if len(gain) > 6 else "") + ")")
    lines += ["", f"Redundancy: fattest productions {fat}; "
              f"single-witness productions ({len(thin)}): "
              f"{', '.join(sorted(thin)[:12])}"
              + ("…" if len(thin) > 12 else ""), "",
              "## D. Name direction — unnamed recurring patterns (PROPOSE-ONLY)"]
    if names:
        for g, fs in names:
            lines.append(f"- `{' '.join(g)}` — {len(fs)} fixtures "
                         f"({', '.join(sorted(fs)[:4])}"
                         + ("…" if len(fs) > 4 else "") + ")")
    else:
        lines.append("- none above threshold (>=3 fixtures)")
    lines += ["", "## A. Interop axis (native vs projection, per ONNX case)"]
    if interop is None:
        lines.append("- skipped: onnx not importable (run `just compress`)")
    else:
        for r in interop:
            lines.append(
                f"- {r['case']}: native {r['native_bytes']}B | flow text "
                f"{r['flow_bytes']}B / {r['flow_tokens']} tokens | passthrough "
                f"{r['passthrough_bytes']}B | text/native = "
                f"{r['flow_bytes'] / r['native_bytes']:.2f}, "
                f"(text+passthrough)/native = "
                f"{(r['flow_bytes'] + r['passthrough_bytes']) / r['native_bytes']:.2f}")
        lines += ["",
                  "Reading (rung honesty): the identity-bearing text is what OAAS",
                  "owns; constants ride the sanctioned passthrough, so tiny graphs",
                  "pay a byte-rung premium. The representational claim lives at the",
                  "concept rung (naming subgraphs), exactly as the founding text's",
                  "caveat states — byte ratios are reported, never headlined."]
    report = ROOT / "docs" / "reports" / f"compression-{today}.md"
    report.write_text("\n".join(lines) + "\n")

    base = ["# compression baselines (agent-maintained; regression = representations",
            "# silently getting less compact). Rung named per metric.",
            f"date: {today}",
            f"corpus: {{fixtures: {len(rows)}, bytes: {total_bytes}, "
            f"tokens: {total_toks}, productions: {len(ALL_PRODUCTIONS)}}}",
            f"covering_set: [{', '.join(s for s, _ in chosen)}]"]
    if interop:
        base.append("interop:")
        for r in interop:
            base.append(f"  - {json.dumps(r)}")
    (ROOT / "conformance" / "compression").mkdir(exist_ok=True)
    (ROOT / "conformance" / "compression" / "baselines.yaml").write_text(
        "\n".join(base) + "\n")

    print(f"corpus: {len(rows)} fixtures, {total_bytes}B, {total_toks} tokens, "
          f"{len(ALL_PRODUCTIONS)} productions")
    print(f"covering set: {len(chosen)} fixtures "
          f"({', '.join(s for s, _ in chosen)})")
    print(f"naming candidates: {len(names)}")
    if interop:
        for r in interop:
            print(f"interop {r['case']}: text/native "
                  f"{r['flow_bytes'] / r['native_bytes']:.2f}, +passthrough "
                  f"{(r['flow_bytes'] + r['passthrough_bytes']) / r['native_bytes']:.2f}")
    print(f"report: {report.relative_to(ROOT)}; baselines written")


if __name__ == "__main__":
    main()
