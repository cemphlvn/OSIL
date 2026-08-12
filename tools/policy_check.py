#!/usr/bin/env python3
"""Policy agreement loop (G8): the self-hosted policy vs the skill layer.

GOVERNANCE.md declares that improvable/*/SKILL.md frontmatter must agree with
profiles/domain/agent/repo-policy.oaas — "a standing loop, mechanical once G2
lands." This is that loop. It parses the actors OUT OF THE OAAS TEXT (the
policy is checked as the language, not as prose) and compares:

  1:1     every skill has an actor of the same name (human roles exempt);
          every non-exempt actor has a skill.
  scope   every skill scope path is covered by an actor scope path
          (prefix cover; file-granular paths covered by their directory —
          GAP-5, pinned by corpus 022, will tighten this).
  verbs   skill verbs == actor verbs, as sets.

Exit nonzero on any disagreement. Wired into `just test`.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oaas_check import tokenize

HUMAN_ROLES = {"spec-editor"}   # policy roles with no skill counterpart


def parse_actors(path):
    toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
    actors, i = {}, 0

    def word(k=0):
        t = toks[i + k] if i + k < len(toks) else None
        return t.text if t and t.kind == "ident" else None

    while i < len(toks):
        if toks[i].kind == "ident" and toks[i].text == "actor":
            name = toks[i + 1].text
            i += 2
            assert toks[i].text == "{"
            i += 1
            fields = {"scope": [], "verbs": []}
            while toks[i].text != "}" or toks[i].kind != "op":
                w = toks[i].text
                if w in ("scope", "verbs", "invariants", "ratify"):
                    i += 2  # keyword + "{"
                    items, cur = [], None
                    while not (toks[i].kind == "op" and toks[i].text == "}"):
                        t = toks[i]
                        if t.kind == "ident":
                            if cur is not None and t.start == cur[1]:
                                cur = (cur[0] + t.text, t.end)      # adjacency
                            else:
                                if cur:
                                    items.append(cur[0])
                                cur = (t.text, t.end)
                        elif t.kind == "op" and t.text == "/":
                            if cur is not None and t.start == cur[1]:
                                cur = (cur[0] + "/", t.end)
                            # non-adjacent slash cannot occur (R003 rejects it)
                        elif t.kind == "op" and t.text == ",":
                            if cur:
                                items.append(cur[0])
                                cur = None
                        i += 1
                    if cur:
                        items.append(cur[0])
                    if w in fields or w in ("invariants", "ratify"):
                        fields[w] = items
                    i += 1  # closing "}"
                else:
                    i += 1
            actors[name] = fields
        i += 1
    return actors


def parse_frontmatter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r"(\w[\w-]*):\s*\[(.*)\]", line)
        if km:
            fm[km.group(1)] = [x.strip() for x in km.group(2).split(",") if x.strip()]
        else:
            km = re.match(r"(\w[\w-]*):\s*(\S.*)", line)
            if km:
                fm[km.group(1)] = km.group(2).strip()
    return fm


def covered(skill_path, actor_paths):
    # prefix cover; file-granular skill paths covered by their directory
    # (GAP-5: policy scopes are directory-granular until dotted path_ref lands)
    for a in actor_paths:
        if skill_path == a or skill_path.startswith(a):
            return True
    return False


def main():
    actors = parse_actors(ROOT / "profiles" / "domain" / "agent" / "repo-policy.oaas")
    skills = {}
    for sk in sorted((ROOT / "improvable").iterdir()):
        f = sk / "SKILL.md"
        if f.exists():
            skills[sk.name] = parse_frontmatter(f)

    problems = []
    for name, fm in skills.items():
        if name not in actors:
            problems.append(f"skill {name!r} has NO actor in repo-policy.oaas")
            continue
        act = actors[name]
        for p in fm.get("scope", []):
            if not covered(p, act["scope"]):
                problems.append(f"{name}: skill scope {p!r} not covered by "
                                f"actor scope {act['scope']}")
        sv, av = set(fm.get("verbs", [])), set(act["verbs"])
        if sv != av:
            problems.append(f"{name}: verbs disagree — skill {sorted(sv)} "
                            f"vs actor {sorted(av)}")
    for name in actors:
        if name not in skills and name not in HUMAN_ROLES:
            problems.append(f"actor {name!r} has no skill and is not an "
                            "exempt human role")

    print(f"actors: {len(actors)} ({len(HUMAN_ROLES)} human-exempt) · "
          f"skills: {len(skills)}")
    if problems:
        for p in problems:
            print(f"DISAGREE {p}", file=sys.stderr)
        sys.exit(1)
    print("Policy agreement satisfied: skills and self-hosted actors are 1:1; "
          "scopes covered; verbs equal.")


if __name__ == "__main__":
    main()
