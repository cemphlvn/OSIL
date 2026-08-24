import json, re, pathlib, collections
none = json.load(open("none_set.json"))
src = pathlib.Path("TSVC_2/src/tsvc.c").read_text(errors="replace")
dep = none.get("CLASS-2 dependence", []) + none.get("CLASS-2 recognition", [])
cat = collections.defaultdict(list)
for fn in dep:
    m = re.search(rf'^real_t {re.escape(fn)}\(.*?\n\{{(.*?)initialise_arrays', src, re.S | re.M)
    note = ""
    if m:
        cs = [l.strip().lstrip('/').strip() for l in m.group(1).splitlines()
              if l.strip().startswith('//')]
        note = " / ".join(c for c in cs if c)
    cat[note or "<no comment>"].append(fn)
print(f"  {len(dep)} Class-2 loops in the None set, by TSVC's OWN stated purpose:\n")
for note, fns in sorted(cat.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(fns):3d}  {note[:88]}")
    print(f"       {' '.join(sorted(fns))}")
