# Quality record — 17 October 2026

## Teaching design

Visual thesis: a quiet paper-and-ink textbook, with one green accent, generous line spacing, restrained navigation, and mathematical diagrams that explain decisions.

Content plan: orient the reader, establish the general model, derive transformations, state guarantees, expose exceptions, apply them to labelled examples, and test understanding through exercises.

Interaction thesis: reading progress and active chapter position maintain orientation; expandable answers support recall before review; eight local labs expose the relation between representations, phases and probabilities, and schedules and energies. No decorative animation or external imagery is needed to explain this material.

## Revision passes

1. **Source and scope audit.** Read the supplied HTML; separated scheduling, algebra, encoding, algorithm and experimental-evidence layers. Inspected the repository builder and instance data. Preserved the supplied source and unrelated workspace changes.
2. **General reconstruction.** Used operations and precedence arcs so the core model covers fixed-route job shops, then identified the source builder's narrower implemented scope. Derived windows, penalties, matrix conventions, horizon search, domain-wall indicators, Ising coefficients and QAOA actions before giving numerical examples.
3. **Completeness pass.** Added binary simplification versus quadratization versus constrained linearisation; product-auxiliary truth tables and weight guarantees; slack encoding and its complete coefficient example; max/absolute-value objectives; higher resource capacities; outages, lags, alternatives, setup adjacency and transport; CP/MILP mechanisms; VQE and filtering; asymmetric-penalty limitations; and Johnson's special-case conditions.
4. **Notation and prerequisites pass.** Separated processing times from QAOA depth, horizon from Hamiltonian, and pair coefficients from the offset. Defined summation/product notation, logarithms and ceilings, graphs, matrix multiplication, conjugate transpose, eigenvalues, amplitudes, operators and interference. Distinguished valid codewords, feasible schedules and optimal schedules throughout. Separated the inspected domain-wall word from the rank selected in the comparison lab.
5. **Mathematical audit.** Nine groups passed. Checks include 5,804 exhaustive small-model scheduling assignments; 1,268 QUBO/Ising evaluations; 164 domain-wall states on weighted conflict graphs; 636 equality/slack evaluations; signed cubic quadratizations and constrained linearisation; 49 one-qubit circuit angle pairs; source-instance optima/counts; matrix examples; annealing deltas; and residual substitution. The full report records the exact scope. General statements also have in-text arguments; finite checks are not substitutes for proofs.
6. **Browser and layout pass.** Inspected opening typography, aligned derivations, equations, interactive controls and mobile navigation in a real browser. Repaired converter-generated multi-line MathML so derivations use real alignment tables. Contained long inline formulas. Confirmed no horizontal page overflow at narrow-phone, phone and tablet review widths (effective content widths 345, 375 and 753 CSS pixels) and at desktop width. Tested all four scheduling presets, a manual bit change, the three phase presets, fixed-choice and invalid domain-wall states, and showing/hiding every exercise solution. The print-scale typography was inspected at A4 content width, with no overflowing equations, tables or inline formulas in that preview.
7. **Packaging pass.** Embedded styles, script, mathematical markup and audit data in one HTML file. Checked local anchors, duplicate IDs, MathML XML validity, JavaScript syntax, unconverted math tokens, and absence of external runtime assets. Build and audit scripts accompany the editable source.

## Reader-feedback revision

The initial notation reference introduced later concepts too tersely. Replaced it with a core scheduling table and an optional later-symbols table with chapter links. Expanded the horizon/makespan distinction, set/cardinality distinction, single-bit versus operation-group distinction, and flattening explanation. Gave each scheduling penalty weight its own row, expanded its abbreviation, distinguished fixed coefficients from solver decisions, and reinforced the explanation where the complete model is first assembled. A further revision responds to the reader's lack of prior exposure: chapter 02 now introduces bit meaning, a complete operation/time lookup, encoding and decoding, machine metadata, and the general unequal-group index map before the QUBO formula. Chapter 03 explains the name and input of each penalty, builds the exactly-once penalty from a count, and displays all 25 products in a four-choice bracket square before collecting terms and generalising. The notation P_once consistently denotes the total across operations. The advanced transformation workshop is expandable so it does not interrupt the first construction.

Expanded intermediate steps also cover window cardinalities, matrix multiplication, domain-wall cancellation and invalid words, the wall-weight argument, binary indicators, all slack coefficients, Ising substitution, quantum amplitudes and phases, one-bit QAOA probabilities, annealing deltas, and the worked domain-wall polynomial. Conflict energy is named E_conflict to avoid confusion with schedule completion time.

The latest audit passes ten groups, including a new beginner walkthrough check: all 256 assignments of the eight-bit teaching example, reversible equal- and unequal-group lookups, 255 arbitrary-size exactly-one assignments, and 186 full-matrix evaluations. These checks verify arithmetic and representations; they do not establish that an explanation will be clear to every reader. The broad mathematical scope and the original source examples remain present.

The revised five-row product expansion was checked in the live reading edition. A rendering issue caused tiny vertical scrollbars beside short inline formulas; the inline containers now provide more line height and suppress vertical scrolling while retaining horizontal scrolling for wide formulas.

## Verification boundaries

The print-scale check is a layout preview, not a certified paginated PDF; no PDF is delivered. The native in-app print dialog could not be inspected, so the reading edition uses a solution-review control rather than an in-page print launcher. Normal browser printing retains the print stylesheet and answer-expansion hooks.

The guide demonstrates and audits local mathematics. It does not launch remote backends, claim quantum advantage, reproduce historical optimiser percentages, or implement every scheduling extension. Generalisation in the text does not add those features to the source solver.

## Quantum introduction integrated after reader feedback

Chapter 10 now begins with an explicit connection to the existing scheduling bits, what a circuit and measurement produce, the meaning of ket notation, real amplitudes and their squared probabilities, the reason for 1/sqrt(2), and phase before general complex notation. The Hadamard/sign-change/Hadamard example shows every substitution, cancellation and normalisation step. The embedded fourth lab displays signed amplitudes beside probabilities, supports forward/backward steps, and compares including versus omitting the sign change. It explicitly represents hypothetical measurement probabilities without measuring between gates. Hadamard is named H_Had in equations to distinguish it from the scheduling deadline H.

The later general theory remains: complex amplitudes are additionally explained as mathematical arrows; multi-qubit amplitudes label whole bitstrings; an entanglement example is distinguished from classical correlation. Chapter 11 now introduces the candidate, cost, cost angle, mixer angle, layers, repeated samples and classical feedback before circuit exponentials. The teaching example is explicitly distinguished from a scheduling benchmark and from QAOA's mixer.

The mathematical audit now has eleven passing groups, adding both gate paths, 65 relative phases and 100 complex inputs, including normalization, H-H identity and global-phase invariance. In-browser checks confirmed all four walkthrough stages, unchanged 50/50 probabilities after the sign change, the two opposite final outcomes, backward navigation and no horizontal page or lab overflow at the review width. These checks verify the mechanics; they do not certify individual learning outcomes.

## Physical motivation and register notation revision

Added the distinction between a physical quantum system, outcome probabilities, and scheduling costs. The amplitude-as-directed-contribution picture is explicitly an analogy; the Born rule is identified as a physical postulate, and squared magnitude is distinguished from an ordinary complex square. The explanation does not infer quantum advantage from interference alone.

Replaced the abrupt N-qubit formula with a progression from complete candidate strings to a joint register, all four explicit two-qubit basis vectors, scalar-times-vector expansion, a labelled unequal-weight example with zero coefficients, coordinate-order independence, and the general 2^N counting argument. The normalization sum is unpacked as a sum of probabilities rather than each coefficient being one. The QAOA bridge explains why implementable cost terms guide phases without first identifying the optimum, and why tuning and performance evidence remain necessary.

Extended the existing quantum audit group to check the printed basis reconstruction, probabilities (0, 3/4, 1/4, 0), coordinate permutations and complete outcome counts for 1–6 qubits. The total remains eleven groups.

## Starting rules, derivations and algorithm motivation

Added an explicit reading contract distinguishing physical postulates, definitions/conventions, model assumptions, derivations, imported mathematical results and algorithm choices. “Given here” supplies a rule rather than assuming prior knowledge. Point-of-use markers identify the Born rule, pure-state representation, ideal projective measurement, composition by tensor product and closed-system unitary evolution. The guide states when deeper physical derivations, hardware control, measurement interpretations or general theorem proofs are outside scope.

Hadamard and Pauli gates are identified as chosen transformations with defined actions. Normalization is explained as a consequence of the Born rule and probability normalization. Euler's identity, Hermitian diagonalization, exponential action on eigenstates, commuting exponentials, Schrödinger evolution, half-angle gate conventions and the quantum adiabatic theorem have named provenance and proof/scope boundaries. These additions distinguish a mathematical gate construction from the device's natural Hamiltonian and scheduling time.

The new quantum motivation section explains why a classical scheduling problem can use a quantum search mechanism without requiring one or establishing an advantage. The QAOA purpose table gives each step's immediate effect, reason for using it and practical limit. Added the explicit reason the standard mixer alone cannot improve the all-plus state's uniform probabilities, and audited it for 1–6 qubits at five angles (30 cases). The total remains eleven audit groups.

## Visual checkpoints added to the reading guide

Added three interactive visuals beside the relevant chapter explanations: (1) two complex-amplitude arrows with probability and relative-phase controls, distinguishing direction from squared length; (2) a 1–4 qubit register explorer with a selected basis vector, separate whole-state amplitudes, joint probabilities and individual-qubit marginals; (3) one exact two-qubit QAOA layer reusing the invented polynomial from chapter 02, with unchanged costs, cost-phase and mixer stages, angle controls, contrasting presets, and simulated batches of 100 fresh measurements. A static ordered diagram explains the classical feedback loop. The total is seven local labs.

The examples explicitly separate mathematical amplitude planes from physical directions and a Bloch sphere, state-vector predictions from hardware measurements, state preparation from inspection, and quantum state information from a joint probability histogram. Coordinate wrapping preserves labelled order. Sample statistics reset when the circuit changes.

The actual JavaScript math is checked by `check-visuals.cjs`: 175 amplitude/phase cases, 120 register-state cases, 289 circuit angle pairs against an independent full mixer matrix, three angle presets, two deterministic sampling checks, and a joint-distribution comparison with equal individual marginals. The checker writes a report with a SHA-256 source hash; the build verifies the hash and embeds the report with the mathematical audit. Finite checks do not prove computational advantage.

Browser checks exercised phase rotation at fixed probabilities, an amplitude-zero endpoint, four-qubit uniform and selected-basis states, the correlated two-qubit state, unchanged probabilities after cost phases, both mixer presets, zero angles, sample batches and clearing stale samples. Inspected the amplitude, register and QAOA layouts. No horizontal page or lab overflow at desktop, 375 and 320 effective CSS-pixel widths. Temporary viewport overrides were reset. All explanations and numerical examples retain a noninteractive reading path when JavaScript is disabled.

The cost/probability section now explicitly answers whether frequent measurement implies correctness: it does not. It traces the intended connection through algorithm design and cost feedback, uses both two-qubit presets as counterexamples to automatic correctness, and preserves independent scheduling validation as the acceptance criterion.

## Bloch geometry, coordinate meaning and guarantee boundaries

Added a genuine projected Bloch sphere beside its two complex-amplitude planes. The initial state uses amplitudes 1/sqrt(2) and (1+i)/2. Tilt and relative phase controls, complex/real/pole presets and a common-phase toggle distinguish probability balance, relative phase and unobservable global phase. X/Y/Z measurement settings use separate freshly prepared copies. A camera-view control changes only the drawing. The text identifies the pure-state/Born/composition postulates, derives the two-angle representation, expands non-real squared magnitudes, and explains measurement-basis changes. The sphere is explicitly limited to a single pure qubit.

Added a point-of-use explanation of ordinary bit labels versus Z eigenvalues, and a one-bit cost-preservation example. A new beginner bridge distinguishes bit values from amplitude coordinates and explicitly multiplies the two one-qubit basis vectors to obtain the four-entry joint basis vector. It explains why zero amplitude in every slot is not the definite-zero state, and separates coordinate-order convention from the tensor-product composition rule.

The optimality section now separates correctness of the model from success of a search. It derives lower/upper bounds and gap certificates, gives an invented worked bound example, explains the special zero-penalty feasibility certificate, and limits any certificate to its declared domain and objective. It does not import changing Stage 2 benchmark numbers into the portable methods guide.

The actual Bloch calculation code passes 325 angle pairs, each checked with and without global phase against independent amplitude-level basis-change gates, plus the complex initial example and six axis poles. The visual source hash is refreshed before rebuilding. There are eight local labs.

Browser verification covered the complex starting state, unchanged X/Y/Z predictions under common phase, the +i state, both definite-bit poles and viewpoint-only rotation. The sphere, arrows and controls were inspected on desktop and at 375/320 CSS-pixel viewport widths without horizontal page or lab overflow. Viewport overrides were reset. The final packaging check validates MathML, local anchors, unique IDs and absence of external runtime assets.

The final tensor-product revision places preparation, gate evolution and measurement on a shared timeline, distinguishing an N-qubit register, 2^N amplitude coordinates and an N-bit measured result. The individual-qubit section separates fixed classical encoding metadata, local measurement summaries, joint correlations and the repeated two-entry action of a local gate. It explicitly adds probabilities when grouping distinct complete outcomes, and identifies reduced density matrices as the general local-summary formalism outside the pure-register calculation path.
