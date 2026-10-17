# Mathematical and quality verification receipts

17 October 2026. Fresh local verification of frozen V3 inputs. No training,
VeloxQ submission, QPU call, model migration or artifact replacement.

- `mathematics.json`: 13 small-bundle coefficient, penalty, Ising, physical-pair
  and exact-sector audits; complete-cell independent physical subset audit;
  final-incumbent re-encoding and exact quality comparisons.
- `retained-verification.json`: 965 hashes, 152,340 returned bitstrings,
  467,003 recounted sample frequencies and eight final plans verified.
- `verification.json`: final pass counts, code hashes, test environments,
  review summary and explicit no-migration/no-service flags.
- `core-tests.log`: 51 cases, 50 pass and one optional Qiskit skip in the
  lightweight environment. Includes the new adversarial/validation regressions.
- `circuit-test.log`: dedicated Qiskit equivalence test passes in the SDK
  environment, covering logical, native and routed statevectors.
- `adapter-tests.log`: 66 offline pytest cases pass, with three existing SDK
  deprecation warnings. Fake service responses are not real backend calls.
- `stage1-A.json`, `stage1-B.json`: selected actual quantum evidence verifies
  feasible optimal makespans 4h/8h; official root schedules match those sources.

The static build and all 138 site tests passed; no site behavior was changed in
this audit. Tests of mathematical correctness do not establish quantum advantage
or full-grid optimality of a restricted portfolio.

The independently recomputed final-pool comparison finds 6/8 incumbents optimal
on that final offered domain. All eight still trail the raw-grid optimum and
all final-step controls tie their run's quantum outcome. See
[quality analysis](../../docs/CATERING_QUALITY.md) and
[active design/proofs](../../PROJECT_DESIGN.md).

The only domain-code fixes reject unsupported future/malformed outages,
unrevealed active demand and invalid snapshot times. All frozen instance files,
QUBO coefficients, variable orders, hashes and schedules remain unchanged.
Method owners can finish existing runs with their existing source snapshots.

Reproduce into fresh output files:

```sh
.venv-stage2/bin/python -m catering.audit_math --output output/NEW-MATH-AUDIT.json
.venv-stage2/bin/python -m catering.verify_meals \
  output/catering-foundation-v3 output/catering-paired-pilot-v1 \
  output/catering-complete-cell-v3 --output output/NEW-RETAINED-CHECK.json
.venv-stage2/bin/python -m unittest discover -s tests/catering -p 'test_[!v]*.py' -v
.venv/bin/python -m unittest discover -s tests/catering -p test_meal_circuit.py -v
.venv/bin/python -m pytest tests/catering/test_veloxq_adapter.py -q
```

The SDK environment needs the optional Qiskit/adapter packages and pytest;
the foundation dependencies alone intentionally omit those packages.
