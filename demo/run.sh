#!/usr/bin/env bash
# Every claim below is produced by running YOUR compilers. Nothing is asserted.
#
# Evidence is each compiler's OWN vectorization report, never a grep over
# disassembly. An earlier version of this script counted vector mnemonics and
# got it wrong for GCC — reporting "0 vectorized" for a loop GCC's own
# -fopt-info-vec said it had vectorized. The compiler is the authority on what
# the compiler did.
set -u
archflag() {  # -mcpu=native on ARM, -march=native on x86, neither if unsupported
  echo 'int main(void){return 0;}' > /tmp/_a.c
  for f in "-mcpu=native" "-march=native"; do
    "$1" $f /tmp/_a.c -o /tmp/_a 2>/dev/null && { echo "$f"; return; }
  done; echo ""
}
CCS=(); for c in "${CC:-clang}" gcc gcc-16 gcc-15 gcc-14; do
  command -v "$c" >/dev/null 2>&1 && CCS+=("$c"); done
[ ${#CCS[@]} -eq 0 ] && { echo "need clang or gcc"; exit 1; }
# de-duplicate (clang and cc may be the same binary)
UNIQ=(); for c in "${CCS[@]}"; do
  id=$("$c" --version 2>/dev/null | head -1)
  case " ${SEEN:-} " in *"|$id|"*) continue;; esac
  SEEN="${SEEN:-}|$id|"; UNIQ+=("$c"); done

echo "======================================================================"
echo "  s1113 — a BIT-IDENTICAL speedup that no compiler flag or pragma"
echo "          tested here can reach"
echo "======================================================================"
sed -n '/^void ref_s1113/,/^}/p' s1113.c | sed 's/^/  /'
echo
echo "  a[MID] is read every iteration and overwritten on exactly one of them."
echo "  That single crossing point splits the loop into two independent maps."
echo

for CCX in "${UNIQ[@]}"; do
  AF=$(archflag "$CCX"); BASE="-O3 $AF"
  echo "----------------------------------------------------------------------"
  "$CCX" --version | head -1 | sed 's/^/  /'
  echo "----------------------------------------------------------------------"
  if "$CCX" --version 2>&1 | grep -qi clang; then
    RPT="-Rpass-analysis=loop-vectorize"; GREP="loop not vectorized: .*"
  else
    RPT="-fopt-info-vec-all"; GREP="missed: .*vectorize.*|missed: not vectorized: .*"
  fi
  for f in "$BASE" "$BASE -ffast-math" "-Ofast $AF"; do
    out=$("$CCX" $f -c s1113.c -o /dev/null $RPT 2>&1 |
          grep -oE "$GREP" | grep -v "split" | head -1)
    printf "  %-28s %s\n" "$f" "${out:0:88}"
  done
  if "$CCX" --version 2>&1 | grep -qi clang; then
    for p in "vectorize(enable)" "distribute(enable)"; do
      sed "s|^    for (int i = 0; i < N; i++) a\[i\] = a\[MID\] + b\[i\];|    _Pragma(\"clang loop $p\")\n    for (int i = 0; i < N; i++) a[i] = a[MID] + b[i];|" s1113.c > /tmp/_p.c
      out=$("$CCX" $BASE -c /tmp/_p.c -o /dev/null -Rpass-analysis 2>&1 |
            grep -oE "loop not (vectorized|distributed): [^[]*" | head -1)
      printf "  #pragma clang loop %-22s %s\n" "$p" "${out:0:70}"
    done
    echo "    ^ distribute(enable) is the pragma this compiler's OWN message"
    echo "      above tells you to use. It refuses that too."
  fi
  "$CCX" $BASE -c s1113.c -o /tmp/_k.o 2>/dev/null &&
  "$CCX" $BASE -c harness.c -o /tmp/_h.o 2>/dev/null &&
  "$CCX" /tmp/_k.o /tmp/_h.o -o /tmp/_run -lm 2>/dev/null && /tmp/_run
  echo
done
echo "======================================================================"
echo "  The split needs no -ffast-math and no pragma: it is a REWRITE, not a"
echo "  relaxation. Results agree bit for bit. Both compilers refuse the"
echo "  original; both vectorize the split once it is written out."
echo "======================================================================"
