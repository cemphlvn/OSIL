// Replay-pin fixture: dead-store elimination is an EMITTER promise, not just an
// analysis result. The removed store is replayed once, after the loop, and that
// replay reads the POST-loop state.
//
// Reduced from opus src/analysis.c:915 (the tonality-memory shift). Found by
// pointing the shipped chooser at a repository this project did not author.
// See repo-pins/README.md.
//
// The loop is CORRECT AS WRITTEN. The pin is that dead-store does not fire.
void shift_v0(float *m, float *b, int n)
{
    for (int i = 0; i < n; i++) {
        m[i + 24] = m[i + 16];      // S0: overwritten by S1 -- EIGHT iterations
        m[i + 16] = m[i + 8];       //     later, and read by S0 itself before
        m[i + 8]  = m[i];           //     then. Not dead, and not replayable.
        m[i]      = b[i];
    }
}
