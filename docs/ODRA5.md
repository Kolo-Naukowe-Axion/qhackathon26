# ODRA5 Stage 1 hardware route

**User hold, 16 October 2026:** stop ODRA5 use and connectivity work for now. Continue Stage 1 locally, with VeloxQ also on hold. The material below records earlier preparation; it is not authorization to resume hardware work.

The 2×2 QAOA uses four logical qubits, fitting ODRA5's five-qubit IQM Spark. The existing 3×3 models use 30 or 39 variables and do not fit a direct five-qubit circuit. Proposed hardware run: QAOA for A, with VeloxQ still planned for B.

The [WCSS manual](https://man.e-science.pl/pl/odra5), updated 28 September 2026, requires a PWr/VPN-KDM network route, an active quantum service and a personal IQM API token. SSH is a valid execution route but does not replace token authentication. Required IQM client: 35.0.3. WCSS documents Python 3.12+ for its compute sessions.

Read-only checks confirmed the existing `wcss` SSH login, Axion quantum Unix membership, an active “Axion kwanty 1” service, and Axion CPU association `hpc-iwowoj-1781179048`. No other grant is substituted. No IQM token was configured in the local or SSH environment. The ODRA5 public URL redirected to e-science from the login host; that is not a successful QPU connection.

## Offline preparation

IQM 35.0.3 requires a different Qiskit version from the simulator environment. Keep it separate:
```sh
uv venv --python 3.11 .venv-odra
uv pip sync --python .venv-odra/bin/python requirements-odra.lock.txt
.venv-odra/bin/python -m solver.odra --output output/new-odra-proxy
```

This uses the official local `IQMFakeAdonis` noise model: a star-topology proxy, not ODRA5's current calibration or physical execution. Compilation searches eight routing seeds and minimizes CZ count/depth, then checks all logical measurement probabilities including physical ancilla marginalization. Qubit objects are resolved after circuit copying because removing measurement registers can reorder the qubit list. Counts use classical register order.

Compare circuit depths: p=1 used 11 native CZ gates/depth 22; p=3 used 39 CZ/depth 73; p=5 used 67 CZ/depth 123. Their 1,024-shot proxy feasible rates were about 19.8%, 31.0% and 19.1%, respectively. These are illustrative noise-model outcomes, not live ODRA5 predictions. The p=3 circuit is the current balanced candidate; an initial p=1/p=3 hardware comparison would be useful. The ideal p=5 simulator baseline remains available.

## SSH execution

Use a permitted Axion compute session according to WCSS instructions. Install dependencies once there, not inside every batch job. Copy `solver/`, `instances/`, and the chosen source run's evidence. Keep your own token outside the repository; load it as `IQM_TOKEN`. Set `IQM_SERVER_URL` to the exact dashboard endpoint and `IQM_COMPUTER` if required.

```sh
python -m solver.odra --submit --source-run output/stage1/qaoa-2x2-bfgs-p3 --output output/odra5-physical
```

The explicit remote command reads the live architecture, compiles for that target, checks logical probabilities, records native QASM/plan, submits once, saves its job id immediately, and retains raw counts plus validated schedule. `--resume` retrieves the saved job without changing the original circuit/calibration evidence. Only actual feasible physical samples justify a hardware method label in the final schedule.

No physical ODRA5 result has been obtained yet. The simulator baseline remains valid independently of hardware access.

The client bundle was copied over SSH to `~/qhackathon26-stage1` on the existing `wcss` account. Its dedicated `.venv` is installed and verified on Python 3.12.13 with IQM 35.0.3; the uploaded p=3 QAOA evidence also passes verification there. An interactive session on the verified Axion CPU allocation reached ODRA5 and received HTTP 401, confirming the route while authentication remains missing. Both short allocations ended cleanly. The IQM dashboard still redirected to e-science in the local browser, so no personal token could be created yet; no token or quantum job is fabricated.
