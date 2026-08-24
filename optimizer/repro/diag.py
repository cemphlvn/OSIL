import re, subprocess, pathlib, sys
LOST = "s124 s1279 s243 s254 s255 s271 s2711 s2712 s273 s3251 s4117 s443".split()
def reasons(f, inc):
    r = subprocess.run(["clang","-O3","-std=c99","-w","-mcpu=native","-c",f,"-o","/dev/null",
        f"-I{inc}","-Rpass=loop-vectorize","-Rpass-analysis=loop-vectorize"],
        capture_output=True,text=True)
    lines = pathlib.Path(f).read_text(errors="replace").splitlines()
    fn_at, cur = {}, None
    for n,ln in enumerate(lines,1):
        m=re.match(r'^(?:real_t|void|int)\s+(\w+)\s*\(', ln)
        if m: cur=m.group(1)
        fn_at[n]=cur
    out={}
    for line in r.stderr.splitlines():
        m=re.search(r':(\d+):\d+: remark: (.*?)(?:\[|$)', line)
        if not m: continue
        fn=fn_at.get(int(m.group(1)))
        if fn: out.setdefault(fn,[]).append(m.group(2).strip())
    return out
stock = reasons("TSVC_2/src/tsvc.c","TSVC_2/src")
withd = reasons("var_BC.c","tsvc_withArgs/tsvc")
print(f"  {'loop':<9}{'stock TSVC_2':<26}{'withArgs + both declarations'}")
for fn in LOST:
    s = stock.get(fn,["<none>"]); w = withd.get(fn,["<none>"])
    sv = "VECTORIZED" if any("vectorized loop" in x for x in s) else s[0][:24]
    wv = "VECTORIZED" if any("vectorized loop" in x for x in w) else w[0][:56]
    print(f"  {fn:<9}{sv:<26}{wv}")
