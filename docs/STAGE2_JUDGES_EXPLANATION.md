# Judge-facing explanation and requirement audit

**Current local entry, 17 October:** start with [the manufacturing recovery
specification and rubric evidence](STAGE2_ENTRY.md). It adds a complete residual
cell with 18–34 logical-qubit simulated QAOA and same-model certified references.
All 60 quantum TEST schedules are optimal; 57 measured states are exact QUBO
minima. Classical annealing reaches all 60 minima too. Offline SDK precision
audits and the fresh-run demo are separate from the older factory studies below.
The full factory's favorable classical results are not quantum-core outcomes.

Authority: the supplied [challenge PDF](../Quantum_Hackathon_2026_ERP_Challenge.pdf), SHA256 `821b7d47a02cdf1d1e5bacc730ad030683d37a56e282b98c4e221675b01d1e99`. Its Stage2 expectations on page3 were checked against the rendered page, not only extracted text. The narrative and requirement matrix were prepared before final evaluation. The separately labeled final audit-only proof illustration below was added afterward; it is not a population performance estimate. Organizer acceptance or completed submission is not asserted.

## The factual story

We start with the mandatory tiny flow shop, then build a synthetic pump factory where completing one product requires its housing, rotor and flange to meet physically at assembly. The24-known-order configuration has72 initial components and384 nominal manufacturing operations, before bounded repairs and urgent work, across15 machines,10 workers and four AGVs. The96-hour, one-minute model includes skills/calendars, portable tools and service, setups, wear/maintenance, batching, finite buffers/blocking, stock, transport/charging, energy, quality and revealed disruptions. An implemented feature, an exercised feature and a binding bottleneck are distinguished; this is not an industrially calibrated digital twin. See the [executable scope](../stage2/README.md) and [activity audit](STAGE2_ACTIVITY.md).

The classical simulator maintains that complete physical world. A controller sees public state and revealed events; it cannot choose using the hidden quality draws or future disruption branch. A separate checker reconstructs actual resource use, manufacturing, transport, energy and objective metrics from recorded execution against a fresh instance. A further [identity audit](../stage2/identity_audit.py) prevents renamed parts or invented replacements from redrawing quality. Selected candidate IDs must equal actually committed IDs. Paired-prefix tests try to falsify future-information leakage; passing them is evidence, not a theorem about every possible history.

The completed final record contains23,552 executions in74 method/context groups.
Each execution has its original anchored physical/identity checks. The later
independent audit rebuilds numerical anchors for every row and physically
replays the592 predeclared retained traces; it does **not** freshly replay all
23,552 executions. The other22,960 executions rely on their original per-row
checks and retained metrics. The full archive additionally reproduces all41
statistical contrasts and all592 retained replays in a clean NumPy-only runtime.
[Complete audit seal](../output/stage2-search/final-independent-audit/complete-audit-seal.json),
[portable reproduction and coverage](STAGE2_FULL_EVIDENCE_ARCHIVE.md).

At a dispatch boundary, a binary variable chooses an individually legal offered operation. Exclusive-resource conflicts and cumulative power constraints prevent incompatible combinations. The [QUBO proof](STAGE2_METHOD_AUDIT.md) uses a penalty larger than the sum of positive rewards, so its global minimum is feasible and reward-optimal **within that fixed candidate pool**, counting every slack bit. The reward is a local scheduling surrogate. We explicitly found that solving the wrong local reward more accurately can worsen the real factory, corrected an excessive batch bonus, and retained the regressions. This is a substantive modeling result rather than evidence that exact local optimization solves the global schedule.

Actual simulated QAOA samples drive checked extended-factory decisions. The integrated experiment caps circuits at five **total** bits and labels larger classical fallbacks; a separate larger saved-pool simulator measures scaling. These are decomposition choices, not a claim that the factory has been encoded losslessly into five qubits. Classical filtering, state maintenance, angle search, training and rollout costs remain real. The learned-CEM-time-policy/QAOA hybrid was actually tested and rejected for worse average fulfillment. We claim neither physical-QPU execution nor quantum advantage. The [method-selection record](STAGE2_METHOD_SELECTION.md) explains why strong statics and a cheap learned CEM schedule often beat more elaborate approaches.

## Formal requirement matrix

For the solution-quality criterion specifically, the later
[same-model comparison and quantified gap supplement](SOLUTION_QUALITY.md)
collects exact two/three-pump makespans, the four-pump interval and complete
realized-primary gap intervals across the unchanged final outcomes. Its stronger
compounded-risk certificate is posthoc and source-bound; it neither switches the
preselected controllers nor establishes quantum advantage or secondary optimality.

| Supplied requirement | Evidence and precise status |
|---|---|
|Working A and B are the eligibility gate; A requires a quantum algorithm on hardware **or simulator**; B permits any QUBO solver. [§4,p.2](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=2)|Both selected baseline files contain actual QAOA simulator results, independently checked at makespans4h/8h. [Current compact evidence](STAGE1_COMPACT.md), [selection](../output/stage1-selected.json), [A](../schedule_2x2.json), [B](../schedule_3x3.json). Technical evidence is present; jury acceptance is separate.|
|Official baseline JSON and integer-hour durations; Stage2 schema may differ. [§14,pp.6-7](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=6)|Root schedule JSONs retain the prescribed `instance`, actual `method`, `makespan`, `schedule` fields. Stage2's minute-grid event trace is a separate disclosed schema, not substituted for either baseline.|
|A realistic manufacturing extension, with integrated reduction/comparison/scaling. [§5,pp.2-4](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=3)|The executable physical factory, local dispatch QUBOs, same-model classical controls and retained quantum/scaling experiments form one workflow. The structural baseline reductions remain separately identified; they do not stand in for extended-model results.|
|Classical reference on the same model; disclose loss of optimum. [§5,p.3](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=3)|Full-model matched classical incumbents and exact frozen-pool comparisons exist. Deterministic CP fixtures explicitly disclose deactivated features. The unrestricted stochastic factory's global secondary gap remains unknown; a small reference or zero missing on a realized tape does not certify its full objective. [Proof scope](STAGE2_CLAIM_REGISTER.md).|
|Quantify the variable cost of added realism. [§5,p.3](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=3)|[26 declared variable families and actual local constraint ablations](STAGE2_REALISM_COSTS.md) include slack, couplers and classical filtering. Global linking, risk and nonanticipativity families are not fully compiled; no complete-global bit total or misleading millions-to-five ratio is claimed.|
|Report the smallest correct baseline3x3 QUBO. [§5,p.3](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=3)|Selected B uses three bits for all six common orders, with an independent full-machine-order optimum check. Its factorial cost construction already reveals the tiny optimum. A separate three-bit H8 deadline encoding retains five distinct machine orders. Their decoder, objective and minimality scopes must not be mixed. [Compact formulation](STAGE1_COMPACT.md), [claim register](STAGE2_CLAIM_REGISTER.md).|
|Public MIT Git repository, separated A/B/extension and both schedule files. [§6,p.4](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=4)|[MIT license](../LICENSE), code separation and root JSONs exist locally. Read-only GitHub metadata verified at00:42UTC on17October reports `isPrivate=true`, default branch `main`: the public-source condition is currently **not met**. A public viewer does not satisfy it. The user's Stage2 commit/push/deploy hold remains in force; this audit authorizes no publication.|
|Dated Development Log, precise Project Design, runnable README. [§§6-8,pp.4-5](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=4)|[Log](../DEVELOPMENT_LOG.md), [design](../PROJECT_DESIGN.md), [README](../README.md) and detailed model/research records exist. Final consistency with the frozen selected code/results still needs the release cross-check. File presence alone is not completeness.|
|AI use allowed, disclosed, understood and defended. [§12,p.6](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=6)|README contains an explicit AI-use disclosure. The team still must understand and explain the formulations, proofs, restrictions and rejected approaches; that human requirement cannot be certified by tests.|
|Video up to five minutes; live presentation up to three minutes plus roughly two minutes Q&A. [§§9-10,pp.4-5](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=5)|A local replay/presentation interface exists. Completed recording, valid video link and a rehearsed live slot are not established by this audit. Replay alone is not a fresh solver launch.|
|Team declaration, Google Form and deadline. [§§6,13,p.4/6](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=4)|The supplied deadline is18October2026,15:00 UTC+2; live presentations start18:00 UTC+2. Team lock-in, submission-form URL/receipt and assigned jury slot remain unverified here. No message, submission or publication is authorized by this document.|
|VeloxQ-specific assessment/prize. [§§11,15-16,pp.6-8](../Quantum_Hackathon_2026_ERP_Challenge.pdf#page=7)|Distinct from mandatory A simulator eligibility. No selected VeloxQ result is claimed. A token, CPU/GPU allocation or generic QUBO execution is not evidence of effective service integration.|

Open consistency item from this audit: the [Project Design opening paragraph](../PROJECT_DESIGN.md) still describes VeloxQ as the plan for B and leads with earlier fixed-horizon methods, while its later compact-formulation paragraph and the actual selected artifacts correctly show QAOA for both baselines. README's project-material description also still calls that document a planned solver interface. These are unresolved release-document discrepancies to recheck with the Stage1 document owner, not reasons to alter the preserved historical log or claim a new backend result.

## Literature and methodological choices

The provided [Zhang, Lo Bianco and Beck paper](../literature/papers/zhang2022.pdf) motivates QUBO-guided neighborhoods plus classical CP repair. Its rank proposals can form cycles when combined naively; plain assignment alone is polynomial. Its Digital Annealer is explicitly a classical SA-based device, and communication time is excluded from its reported budget (PDFp.6,printedp.409). We borrow the division of labor, not a claim of quantum speedup or a ready solver for our transport/BOM/energy factory. [Method audit and primary references](STAGE2_METHOD_AUDIT.md).

PPO, CEM time schedules, exact/SA/uniform local controls and independently sampled MPC are actually compared. A pretrained scheduling checkpoint was identified, but its action graph/physical model differs and transfer benefit was not demonstrated; no saved weights are credited as free training for this factory. All relevant costs and negatives stay visible. [Pretraining audit](STAGE2_RECENT_LITERATURE.md), [selection/domain/budget comparison](STAGE2_METHOD_SELECTION.md).

Novelty is scoped to this project's integrated model, mechanisms, auditable experiments and diagnosed tradeoffs. Learned neighborhood choice with conventional solver repair is already established by [Wu et al.,NeurIPS2021](https://papers.nips.cc/paper_files/paper/2021/hash/fc9e62695def29ccdb9eb3fed5b4c8c8-Abstract.html), and QUBO-guided scheduling plus CP by [Zhang et al.,ICAPS2022](https://ojs.aaai.org/index.php/ICAPS/article/view/19826). A separate [July2026 restoration preprint](https://arxiv.org/abs/2607.29544) explicitly describes CPU-SA local QUBOs, a feasibility-preserving decoder and physical-network replay; only its primary abstract was checked here, not independently reproduced. These precedents rule out presenting generic decomposition or an algorithm portfolio as our invention. They do not certify transfer, our full model, or a quantum benefit. A bounded literature search cannot establish absence of prior work.

Decomposition moves work into classical candidate construction, feasibility filtering and decoding; it does not erase that work. Our costs therefore include complete episodes and checks, reward-construction preprocessing, exact-expectation angle search, inference, training/teacher preparation and rollout planning. Nested solver/angle timers are not additive. A zero local auxiliary-bit cost for a prefiltered constraint is not a zero global encoding or computation cost. [Explicit accounting/scope](STAGE2_REALISM_COSTS.md), [actual budgets](STAGE2_METHOD_SELECTION.md).

The completed deterministic four-pump reference follow-up is **FEASIBLE1541**,
with solver-reported lower bound1524: its unknown optimum lies in **[1524,1541]
minutes**. This is not a17-minute known optimality gap or a bound on the full
stochastic factory. The unchanged CP domain permits booking an empty parked AGV
before a future pump exists. The raw trace retains its stock identity-audit
rejection; a separate narrowly scoped physical-encounter audit passes. An
explicit derived witness delays that one booking from1382 to the pump's birth
at1420, preserving every operation, physical leg, pickup/drop and recomputed
metric. That derived witness passes the original physical, terminal and stock
identity checks. The broader CP lower bound also bounds this stricter domain;
equality of the two domains' optima is not claimed.
[Completed reference and audit provenance](STAGE2_REFERENCE_MULTI.md).

At03:16UTC on17October, finished research jobs including failures total
431.9967 allocated CPU-hours, with no running jobs or recorded GPU use. This
includes the70.4178 allocated CPU-hour final campaign and the31.8844 allocated
CPU-hour reference follow-up; those subsets and measured process/episode CPU
times must not be added again. These are compute allocations, not a hardware
speedup or financial-price estimate.
[Immutable accounting snapshot](../output/stage2-search/final-compute-0316-summary.json).

## An audit-only example of a nonzero optimum

An unfulfilled order can be mathematically unavoidable in this fixed model. On the32-demand,240-hour realization at seed10020, the mandatory final pump `P32/pump/1` has first-inspection uniform0.0076995277, below even the least-risk legal assembly floor of approximately0.01. Wear and compounded history cannot reduce that floor. Its sole repair has uniform0.0054374787, below the fixed repair-risk floor of approximately0.02. Both comparisons retain a conservative rounding margin. Thus this pump must fail both inspections, and the audited action domain allows no final-pump replacement or alternative identity to redraw quality. Any legal schedule can ship at most31 of the32 demands.

The unchanged frozen policy has an independently checked execution shipping31. Therefore the minimum missing count is exactly one: a necessary lower bound and an executed upper bound coincide, `L=U=1`. This certifies the **primary fulfillment objective on that one realized tape**. It certifies neither the best deadline debt/cost, all-tape performance, a96-hour solution nor universal policy optimality. Future keyed draws are offline proof inputs, never controller observations.

This realized-tape proof uses literal deterministic hash-derived draws and needs
no assumption that QA keys are statistically independent. The separate
[idealized probability ceiling](STAGE2_IDEAL_QUALITY_CEILING.md) explicitly assumes
independent uniform potential draws; it is not a proven property of the hash
generator or an achievable controller success rate.

This witness was selected post hoc by the recorded rule “first ascending final seed with positive attained lower bound.” That diagnostic rule was declared before exactly one fixed-policy audit rerun; the rerun reproduces every original metric and retains the original physical/source hashes. It is an explanation of the existing result, not a new policy search. The audit-only replay is excluded from the256-tape estimates and from the eight predeclared first-tape/first-actor visual/activity traces. [Declaration and checked witness report](../output/stage2-search/final-independent-audit/nontrivial-proof-seed10020/report.json), [independently reconstructed necessary bound](../output/stage2-search/final-independent-audit/nontrivial-proof-seed10020/independently-reconstructed-necessary-bound.json).

## Three-minute live structure; five-minute video

The current local preview uses the [factory presentation on4187](http://127.0.0.1:4187/stage2/?present=1).
Use that running preview, or start it with `PORT=4187 npm run dev` when that port
is free. Without `PORT`, `npm run dev` defaults to4173; follow the URL printed by
the server if choosing another port. Rehearse a fresh, small full-rule solver launch separately from the larger retained replay; the [Stage2 run instructions](../stage2/README.md) distinguish the reproducibility baseline from the selected strongest policy. Import actual selected Stage1 replays, not the viewer's organizer illustrations. Check the loaded trace's method/source/cutoff before attaching any experimental claim to it.

| Live time | Show and explain |
|---|---|
|0:00-0:25|Launch/result and the two actual mandatory baseline schedules; state the compact encoding's scope.|
|0:25-1:10|Follow one pump's actual housing/rotor/flange, a finite-buffer or scarce-worker conflict, and recorded assembly consumption.|
|1:10-1:50|Show one coupled local QUBO, total core+slack bits, the sampled action and its actual committed operation.|
|1:50-2:30|Show declared classical controls and one modeling lesson: the batch-reward correction or physical kit recovery, including failures and compute cost.|
|2:30-3:00|Explain what the checker/proofs establish, the unknown full-policy gap, and why small quantum execution is not an advantage claim.|

The five-minute video can additionally walk through `spec.py`, `dispatch.py`/`qubo.py`, the independent checker and the dated development decisions, while showing an actual launch and result as required. The schematic viewer explains recorded events; geometry is not an independently calibrated plant, animation is not solver execution, inspection is not shipment, and an incomplete cutoff remains incomplete. [Visualization evidence and limitations](STAGE2_VISUALIZATION.md).
