# Start here

Open **index.html** in a modern browser. It is the complete, portable learning guide: no server, internet connection, installation or account is needed. Keep or share that one file to preserve the equations and interactive labs.

Read chapters 01–06 in order. Chapter 02 explains what each bit means and walks through encoding, flattening and decoding before introducing the general QUBO formula. Chapter 03 builds penalties from counts, explains their names and shows every multiplication in the exactly-one expansion. Its optional algebra transformation workshop can wait until after chapter 04; 07 generalises encodings; 08 develops objectives and extensions; 09–12 connect the model to Ising, quantum mechanics, QAOA and solver mechanisms. Chapter 13 works through the supplied instance, 14 contains sixteen exercises with worked solutions, and 15 is a reference sheet.

The guide distinguishes physical postulates, definitions/conventions, model assumptions, derivations, imported mathematical results and algorithm choices. Quantum starting rules and omitted proofs are named at the point of use; “given here” does not mean prior knowledge is expected.

Chapter 10 starts with the physical motivation and the distinction between a candidate’s cost and the probability of generating it. It then gives a beginner walkthrough: measurement results, amplitudes versus probabilities, notation, phase, and interference. Its embedded four-step visual can include or omit the sign-change gate, showing both outcomes with all arithmetic. The register notation is expanded using all four two-qubit basis vectors before introducing the compact general sum and 2^N dimension. Chapter 11 introduces the QAOA workflow and its parameters in words, with a step-by-step purpose/effect/limitation table before presenting the circuit formulas. Chapter 10 explicitly discusses why quantum is an optional search mechanism and what evidence would be needed to justify using it.

Four additional visuals are embedded beside their explanations: complex-amplitude arrows with probability/phase controls; a Bloch sphere connected to complex arrows, global phase and three measurement settings; a 1–4 qubit register explorer separating basis vectors from the whole state; and an exact two-qubit QAOA layer with phase/mixer steps and simulated measurements. A static diagram shows the classical feedback loop. All eight labs run locally inside the portable HTML.

Use **Show all solutions** when reviewing, or open answers individually while studying. On a narrow screen use **Contents** for navigation. Wide equations and tables scroll inside their own regions. Ordinary browser printing uses a dedicated layout and expands the answers; no PDF file is bundled.

## Reproducibility

The mathematical audit uses the standard library and imports the existing repository builder:

```sh
python3 docs/learning-methods/audit.py
```

The visual calculations have a separate check against independent matrix formulas:

```sh
node docs/learning-methods/check-visuals.cjs
```

That writes `visual-audit-report.json`, including the checked source hash. The build verifies that the report matches `visuals.js` and embeds both audit reports.

To edit and rebuild, change `guide.md`, `style.css`, `labs.js`, or `visuals.js`. If changing `visuals.js`, run its check before rebuilding. In a Python environment of your choice:

```sh
python3 -m pip install -r docs/learning-methods/requirements-build.txt
python3 docs/learning-methods/build.py
```

Build packages are not needed by the reader. The audit report and quality record document verification and its limits. The source tutorial and the repository's existing presentation files were preserved.

The Bloch visual starts with a genuinely complex amplitude, (1+i)/2. Chapter 09 explicitly connects ordinary output bits to Z eigenvalues. Chapter 10 separates classical bit labels from amplitude coordinates and builds the four-entry joint vector from two familiar one-qubit vectors. Chapter 12 distinguishes a best-found candidate from a certified optimum, explaining lower bounds and the limits of local or restricted proofs.
