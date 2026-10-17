# Quality record — 17 October 2026

## Teaching design

Visual thesis: a quiet paper-and-ink textbook, with one green accent, generous line spacing, restrained navigation, and mathematical diagrams that explain decisions.

Content plan: orient the reader, establish the general model, derive transformations, state guarantees, expose exceptions, apply them to labelled examples, and test understanding through exercises.

Interaction thesis: reading progress and active chapter position maintain orientation; expandable answers support recall before review; three local labs expose the relation between representations, phases and probabilities, and schedules and energies. No decorative animation or external imagery is needed to explain this material.

## Revision passes

1. **Source and scope audit.** Read the supplied HTML; separated scheduling, algebra, encoding, algorithm and experimental-evidence layers. Inspected the repository builder and instance data. Preserved the supplied source and unrelated workspace changes.
2. **General reconstruction.** Used operations and precedence arcs so the core model covers fixed-route job shops, then identified the source builder's narrower implemented scope. Derived windows, penalties, matrix conventions, horizon search, domain-wall indicators, Ising coefficients and QAOA actions before giving numerical examples.
3. **Completeness pass.** Added binary simplification versus quadratization versus constrained linearisation; product-auxiliary truth tables and weight guarantees; slack encoding and its complete coefficient example; max/absolute-value objectives; higher resource capacities; outages, lags, alternatives, setup adjacency and transport; CP/MILP mechanisms; VQE and filtering; asymmetric-penalty limitations; and Johnson's special-case conditions.
4. **Notation and prerequisites pass.** Separated processing times from QAOA depth, horizon from Hamiltonian, and pair coefficients from the offset. Defined summation/product notation, logarithms and ceilings, graphs, matrix multiplication, conjugate transpose, eigenvalues, amplitudes, operators and interference. Distinguished valid codewords, feasible schedules and optimal schedules throughout. Separated the inspected domain-wall word from the rank selected in the comparison lab.
5. **Mathematical audit.** Nine groups passed. Checks include 5,804 exhaustive small-model scheduling assignments; 1,268 QUBO/Ising evaluations; 164 domain-wall states on weighted conflict graphs; 636 equality/slack evaluations; signed cubic quadratizations and constrained linearisation; 49 one-qubit circuit angle pairs; source-instance optima/counts; matrix examples; annealing deltas; and residual substitution. The full report records the exact scope. General statements also have in-text arguments; finite checks are not substitutes for proofs.
6. **Browser and layout pass.** Inspected opening typography, aligned derivations, equations, interactive controls and mobile navigation in a real browser. Repaired converter-generated multi-line MathML so derivations use real alignment tables. Contained long inline formulas. Confirmed no horizontal page overflow at narrow-phone, phone and tablet review widths (effective content widths 345, 375 and 753 CSS pixels) and at desktop width. Tested all four scheduling presets, a manual bit change, the three phase presets, fixed-choice and invalid domain-wall states, and showing/hiding every exercise solution. The print-scale typography was inspected at A4 content width, with no overflowing equations, tables or inline formulas in that preview.
7. **Packaging pass.** Embedded styles, script, mathematical markup and audit data in one HTML file. Checked local anchors, duplicate IDs, MathML XML validity, JavaScript syntax, unconverted math tokens, and absence of external runtime assets. Build and audit scripts accompany the editable source.

## Verification boundaries

The print-scale check is a layout preview, not a certified paginated PDF; no PDF is delivered. The native in-app print dialog could not be inspected, so the reading edition uses a solution-review control rather than an in-page print launcher. Normal browser printing retains the print stylesheet and answer-expansion hooks.

The guide demonstrates and audits local mathematics. It does not launch remote backends, claim quantum advantage, reproduce historical optimiser percentages, or implement every scheduling extension. Generalisation in the text does not add those features to the source solver.
