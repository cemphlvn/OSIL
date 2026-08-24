# Reproduce the N=1 slice end to end.
#   make all   — emit, build, differential-test, benchmark, accuracy
CC      ?= clang
CFLAGS  ?= -O3 -march=native
OPT      = ../target/debug/osil-opt
CASE     = ../cases/s312-reassociable.osil
ILV      = 1 2 4 8

.PHONY: all emit clean baseline-proof
all: bench accuracy
	@echo "=== benchmark ==="; ./bench
	@echo; echo "=== accuracy vs f64 truth ==="; ./accuracy

# Evidence that the baseline is genuinely a refusal, not a slow choice.
baseline-proof:
	@echo "--- clang -O3 on the scalar loop:"
	@$(CC) $(CFLAGS) -c kernel_scalar.c -o /dev/null \
	   -Rpass-analysis=loop-vectorize 2>&1 | grep 'not vectorized' || true
	@echo "--- clang -O3 -ffast-math on the SAME source:"
	@$(CC) $(CFLAGS) -ffast-math -c kernel_fastmath.c -o /dev/null \
	   -Rpass=loop-vectorize 2>&1 | grep 'vectorized loop' || true

emit:
	@cd .. && cargo build -q
	@for i in $(ILV); do \
	  $(OPT) $(CASE) --force-interleave $$i --emit osil_i$$i.c >/dev/null; \
	  sed -i '' "s/osil_s312(/osil_s312_i$$i(/" osil_i$$i.c; \
	done

k_scalar.o: kernel_scalar.c ; $(CC) $(CFLAGS) -c $< -o $@
k_fm.o:     kernel_fastmath.c ; $(CC) $(CFLAGS) -ffast-math -c $< -o $@
harness.o:  harness.c ; $(CC) $(CFLAGS) -c $< -o $@
acc.o:      accuracy.c ; $(CC) $(CFLAGS) -c $< -o $@

OSILOBJ = $(addprefix k_i,$(addsuffix .o,$(ILV)))
$(OSILOBJ): k_i%.o: osil_i%.c ; $(CC) $(CFLAGS) -c $< -o $@

bench: emit k_scalar.o k_fm.o $(OSILOBJ) harness.o
	$(CC) k_scalar.o k_fm.o $(OSILOBJ) harness.o -o $@ -lm
accuracy: emit k_scalar.o k_i1.o k_i8.o acc.o
	$(CC) k_scalar.o k_i1.o k_i8.o acc.o -o $@ -lm

clean: ; rm -f *.o bench accuracy osil_i*.c
