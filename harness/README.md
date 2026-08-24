# harness/ -- CausalFork Phase C model-free fork harness

Gate context: EXPERIMENTS.md GF0 rule 3 ("a mock/model-free fork harness must
demonstrate our infrastructure can hold future noise equal across restored
branches before any backend claim"). This package is that proof and doubles as
the adapter contract the EVOKE backend must satisfy at integration time.

Run:
    python harness/run_tests.py

Files:
    fork_harness.py   core (no deps beyond stdlib; uses numpy if importable)
    run_tests.py      self-tests (8), plain asserts, nonzero exit on failure
    artifacts/example/  regenerated auditable twin-run manifest on each
                      fully passing run (safe to overwrite; it is derived)

Adapter contract EVOKE must satisfy (each item maps to a passing test):
  1. All branch-relevant randomness flows through ONE restorable generator.
     Any draw bypassing it is instrumented and flagged (unseeded-hazard test).
  2. Fork snapshot = generator state + world state + ordered draw log,
     deepcopied with aliasing checks (isolation + shallow-copy-detector tests).
  3. Branch configs byte-identical EXCEPT the prompt schedule, proven by
     config hashes in the manifest (draw order is content-conditional).
  4. Coupling asserted on logged per-draw NOISE hashes in draw order --
     never pixels, never seeds alone (injection-modes test).
  5. Draw-order divergence raises/loudly flags DESYNC_DRAW_ORDER instead of
     silently comparing misaligned noises (desync test).
  6. Twin runs are deterministic given (config, seed, fork point, mode):
     reruns reproduce byte-identical manifests (reproducibility test).

Seed policy vocabulary: strict-coupled | prefix-shared-seed-matched |
uncontrolled (only the first and last are exercised here).

Known simulation stand-ins (to be replaced by real upstream equivalents):
  torch.Generator        -> random.Random (Mersenne Twister)
  torch tensors          -> numpy float64 vectors (pure-Python fallback)
  global-RNG bypass      -> random.SystemRandom draws ledgered as unmanaged