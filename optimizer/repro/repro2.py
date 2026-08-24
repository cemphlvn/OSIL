import re, subprocess, pathlib
KERNEL = re.compile(r'^(s\d|vif|vpv|vtv|vpvtv|vpvts|vpvpv|vtvtv|vsumr|vdotr|vbor)')
INC = "tsvc_withArgs/tsvc"
def rate(f, label):
    r = subprocess.run(["clang","-O3","-std=c99","-w","-mcpu=native",
        "-c",f,"-o","/dev/null",f"-I{INC}",
        "-Rpass=loop-vectorize","-Rpass-missed=loop-vectorize"],
        capture_output=True,text=True)
    if r.returncode!=0:
        print(f"  {label}: BUILD FAILED: {r.stderr.splitlines()[0][:120]}"); return None
    lines = pathlib.Path(f).read_text(errors="replace").splitlines()
    fn_at, cur = {}, None
    for n,ln in enumerate(lines,1):
        m=re.match(r'^(?:real_t|void|int)\s+(\w+)\s*\(', ln)
        if m: cur=m.group(1)
        fn_at[n]=cur
    vec=set()
    for line in r.stderr.splitlines():
        m=re.search(r':(\d+):\d+: remark: vectorized loop', line)
        if m:
            fn=fn_at.get(int(m.group(1)))
            if fn and KERNEL.match(fn): vec.add(fn)
    tot=len({f for f in fn_at.values() if f and KERNEL.match(f)})
    return dict(label=label, vec=vec, n=len(vec), tot=tot, pct=100*len(vec)/tot)
rs=[rate(f,l) for f,l in [
    ("var_A.c","A  as published (info withdrawn)"),
    ("var_B.c","B  + no-alias declared (restrict)"),
    ("var_C.c","C  + extent declared (const trip count)"),
    ("var_BC.c","BC + both declared"),
]]
rs=[r for r in rs if r]
print(f"  {'variant':<42}{'vec':>6}{'of':>5}{'rate':>8}{'recovered':>11}")
base=rs[0]
for r in rs:
    d=r['n']-base['n']
    print(f"  {r['label']:<42}{r['n']:>6}{r['tot']:>5}{r['pct']:>7.1f}%{('+%d'%d) if d else '-':>11}")
print(f"\n  ceiling: stock TSVC_2 (all info present)          64  151   42.4%")
if len(rs)>1:
    print(f"\n  newly vectorized by no-alias alone: {' '.join(sorted(rs[1]['vec']-base['vec']))}")
    print(f"  newly vectorized by extent alone  : {' '.join(sorted(rs[2]['vec']-base['vec']))}")
    print(f"  newly vectorized by both          : {' '.join(sorted(rs[3]['vec']-base['vec']))}")
