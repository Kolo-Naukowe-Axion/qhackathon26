import { teachingMatrix, matrixEnergy } from './model.js';

export function matrixLesson() {
  return `<section class="matrix-lesson" aria-labelledby="matrix-title">
    <h3 id="matrix-title">3. Where does the matrix come from?</h3>
    <p><strong>We build it from the penalties above.</strong> The processing-time table is the input. The QUBO matrix Q is our encoding of the allowed starts and the rules those choices must obey. The solver receives Q; it does not invent it.</p>
    <div class="matrix-pipeline"><span>Durations</span><b>→</b><span>Start choices</span><b>→</b><span>Penalties</span><b>→</b><span>Expand & collect</span><b>→</b><strong>Q</strong></div>
    <p>A matrix is a table of numbers indexed by pairs of bits. First fix the variable order. For A at H = 4, the pruned one-hot encoding has eight start choices:</p>
    <div class="table-scroll"><table class="matrix-starts"><caption>Bit order fixes the meaning of every row and column</caption><thead><tr><th>Operation</th><th>First choice</th><th>Second choice</th></tr></thead><tbody><tr><th>Z1 · turning</th><td>x₀: start 0 h</td><td>x₁: start 1 h</td></tr><tr><th>Z1 · milling</th><td>x₂: start 2 h</td><td>x₃: start 3 h</td></tr><tr><th>Z2 · turning</th><td>x₄: start 0 h</td><td>x₅: start 1 h</td></tr><tr><th>Z2 · milling</th><td>x₆: start 1 h</td><td>x₇: start 2 h</td></tr></tbody></table></div>
    <h4>Expand one penalty by hand</h4>
    <div class="formula">(x₀ + x₁ − 1)²<br />= x₀² + x₁² + 2x₀x₁ − 2x₀ − 2x₁ + 1<br />= 1 − x₀ − x₁ + 2x₀x₁<small>Binary bits obey x² = x. This square enforces one start for Z1’s turning.</small></div>
    <p>So add <strong>−1</strong> at Q₀₀, <strong>−1</strong> at Q₁₁, <strong>+2</strong> at Q₀₁, and <strong>+1</strong> to the separate constant c. Do that for all four operations. Then add <strong>+1</strong> for every machine-overlap pair and every precedence-violating pair. Contributions to the same entry are added.</p>
    <div class="formula">E(x) = c + xᵀQx = c + ΣᵢΣⱼ Qᵢⱼxᵢxⱼ<small>xᵀ is the row version of the bit vector x. A diagonal entry multiplies xᵢ² = xᵢ; an off-diagonal entry multiplies a pair.</small></div>
    <div class="matrix-workbench">
      <div class="workbench-heading"><strong>A / BUILD THE ACTUAL 8 × 8 MATRIX</strong><span>H = 4 h</span></div>
      <div class="matrix-stages" role="group" aria-label="Matrix construction stage"><button data-matrix-stage="1" aria-pressed="false">1 · Exactly once</button><button data-matrix-stage="2" aria-pressed="false">2 · + Machines</button><button data-matrix-stage="3" aria-pressed="true">3 · + Precedence</button></div>
      <p class="fine" id="matrix-stage-note"></p>
      <label class="matrix-convention">Storage convention <select id="matrix-convention"><option value="upper">Upper triangular Q</option><option value="symmetric">Symmetric Q</option></select></label>
      <div class="matrix-layout"><div class="matrix-scroll" tabindex="0" role="region" aria-label="QUBO matrix, scroll horizontally if needed"><div id="matrix-grid"></div></div><aside class="matrix-inspector" aria-live="polite"><span class="overline">SELECT A CELL</span><strong id="matrix-cell-title"></strong><p id="matrix-cell-reason"></p></aside></div>
      <div class="matrix-key"><span class="once">Exactly once</span><span class="machine">Machine conflict</span><span class="precedence">Job precedence</span></div>
      <div id="matrix-calculation" class="matrix-calculation" aria-live="polite"></div>
    </div>
    <p>The displayed sample selects x₁, x₃, x₄ and x₆: Z1 turns at 1 h and mills at 3 h; Z2 turns at 0 h and mills at 1 h. Its diagonal terms sum to −4, its selected pair terms sum to 0, and c = 4. Thus <strong>E = 4 − 4 + 0 = 0</strong>: the schedule is feasible.</p>
    <details><summary>Why do symmetric matrices have halves?</summary><p>In xᵀQx, both Qᵢⱼxᵢxⱼ and Qⱼᵢxⱼxᵢ are included. Our upper-triangular convention stores the full pair coefficient once. A symmetric convention splits it in half between the two mirrored cells. For a polynomial term +x₀x₄, use Q₀₄ = 1 and Q₄₀ = 0, or Q₀₄ = Q₄₀ = 0.5. Both give exactly the same energy. Putting 1 in both cells would accidentally double that penalty.</p><p>The offset c does not affect which bitstring minimizes the energy, so it can be stored separately or omitted by a solver. Include it when claiming that feasible energy is zero.</p></details>
    <details><summary>How did the earlier four-qubit QAOA matrix work?</summary><p>The next chapter explains the compact encoding. Each operation’s two start indicators become one bit: x₀ = 1 − a, x₁ = a; x₂ = 1 − b, x₃ = b; x₄ = 1 − c, x₅ = c; x₆ = 1 − d, x₇ = d. Here c is a bit name; the constant energy offset is written separately below.</p><p>The six machine-conflict products are x₀x₄ + x₀x₅ + x₁x₅ + x₂x₆ + x₂x₇ + x₃x₇. The two precedence-conflict products are x₁x₂ + x₅x₆. Substitute the compact indicators into those conflicts and collect terms. The exactly-one penalties have already been enforced by the two-choice encoding, so remove them first.</p><div class="formula">Turning conflicts = 1 − a + ac<br />Milling conflicts = 1 − b + bd<br />Precedence conflicts = a(1 − b) + c(1 − d)<br /><strong>Total E = 2 − b + c − ab + ac + bd − cd</strong></div><p>With bit order [a,b,c,d], the upper-triangular matrix and separate offset are:</p><pre class="compact-matrix">         a   b   c   d
    a [  0  −1   1   0 ]
Q = b [  0  −1   0   1 ]   offset = 2
    c [  0   0   1  −1 ]
    d [  0   0   0   0 ]</pre><p>For [a,b,c,d] = [1,1,0,0], E = 2 − 1 − 1 = 0. This 4 × 4 matrix represents four binary variables; it is not the quantum operator’s 16 × 16 matrix. QAOA converts these coefficients into cost-phase gates. The classical annealer receives a binary quadratic model, not a quantum circuit.</p></details>
    <h3>Which object has which dimensions?</h3>
    <p>Use <strong>B = number of binary variables</strong> here, rather than number of jobs. In direct QAOA, B is also the logical qubit count. The small coefficient matrix and the large quantum operator describe different things.</p>
    <div class="table-scroll"><table class="dimension-table"><caption>General dimensions and the retained four-qubit A comparison</caption><thead><tr><th scope="col">Object</th><th scope="col">General size</th><th scope="col">A: B = 4</th><th scope="col">What we store</th></tr></thead><tbody>
      <tr><th scope="row">Binary assignment x</th><td>B × 1</td><td>4 bits</td><td>One bit per decision variable</td></tr>
      <tr><th scope="row">QUBO coefficient matrix Q</th><td>B × B</td><td>4 × 4</td><td>Linear coefficients + sparse pair coefficients + separate offset</td></tr>
      <tr><th scope="row">Quantum cost operator H<sub>C</sub></th><td>2<sup>B</sup> × 2<sup>B</sup></td><td>16 × 16</td><td>Only its 2<sup>B</sup> diagonal energies</td></tr>
      <tr><th scope="row">Whole-register circuit operator U</th><td>2<sup>B</sup> × 2<sup>B</sup></td><td>16 × 16</td><td>A sequence of local gates, not the full dense matrix</td></tr>
      <tr><th scope="row">Quantum state |ψ⟩</th><td>2<sup>B</sup> × 1</td><td>16 complex amplitudes</td><td>A statevector in the classical simulator</td></tr>
      <tr><th scope="row">Probabilities and cost vector</th><td>2<sup>B</sup> each</td><td>16 real values each</td><td>Used to compute expected energy</td></tr>
      <tr><th scope="row">Local RZ / RX gate</th><td>2 × 2</td><td>2 × 2</td><td>A one-qubit gate, applied to the larger state</td></tr>
      <tr><th scope="row">Local RZZ gate</th><td>4 × 4</td><td>4 × 4</td><td>A two-qubit gate, applied to the larger state</td></tr>
    </tbody></table></div>
    <div class="formula">H<sub>C</sub> = diag(E(0000), E(0001), …, E(1111))<br />⟨E⟩ = Σ<sub>x</sub> |ψ<sub>x</sub>|² E(x)<small>Each basis bitstring labels one possible assignment. H has one energy per assignment, whereas Q has one coefficient per pair of variables. Gates implement the cost up to scaling and an irrelevant constant global phase.</small></div>
    <p><strong>So yes, a 2<sup>B</sup> × 2<sup>B</sup> operator exists mathematically. Our selected baseline does not build or store that dense matrix.</strong> In <code>solver/quantum.py</code>, <code>costs</code> is a length-2<sup>B</sup> NumPy array, <code>Statevector.from_instruction()</code> computes the state from local gates, and <code>probabilities @ costs</code> computes the expectation. The QAOA runner currently refuses B &gt; 12.</p>
    <div class="table-scroll"><table class="dimension-table"><caption>The encodings in this project</caption><thead><tr><th scope="col">Encoding</th><th scope="col">B</th><th scope="col">Q</th><th scope="col">Quantum operator, if mapped to B qubits</th></tr></thead><tbody><tr><th scope="row">A · one-hot teaching model</th><td>8</td><td>8 × 8</td><td>256 × 256</td></tr><tr><th scope="row">A · retained domain-wall QAOA</th><td>4</td><td>4 × 4</td><td>16 × 16, implicit</td></tr><tr><th scope="row">B · retained one-hot classical annealer</th><td>39</td><td>39 × 39</td><td>No quantum register or operator used</td></tr><tr><th scope="row">B · alternative compact model</th><td>30</td><td>30 × 30</td><td>2³⁰ × 2³⁰ only if quantum-mapped; not run by our QAOA simulator</td></tr><tr><th scope="row">A · selected order QAOA</th><td>1</td><td>1 × 1</td><td>2 × 2, implicit</td></tr><tr><th scope="row">B · selected order QAOA</th><td>3</td><td>3 × 3</td><td>8 × 8, implicit</td></tr></tbody></table></div>
    <p>A hypothetical dense whole-register matrix needs O(4<sup>B</sup>) numbers. Our statevector simulator needs O(2<sup>B</sup>) amplitudes, so simulation is still exponential even though we avoid the dense operator. The retained 39-bit classical annealer works directly with the sparse QUBO; it does not enumerate or store 2³⁹ quantum amplitudes. A physical QPU likewise does not store a classical amplitude array.</p>
    <details><summary>Where are these coefficients in our code and files?</summary><p><code>solver/stage1.py → build_qubo()</code> reads the jobs and durations, builds the start windows, expands exactly-one terms, and adds conflict-pair coefficients. <code>domain_wall()</code> performs the compact substitution. The exported <code>model.json</code> stores <code>linear</code> (the diagonal), <code>quadratic</code> ([i,j,coefficient] triples), <code>offset</code> and variable meanings. It is the sparse form of the same matrix.</p><p><code>to_dimod()</code> passes those coefficients to a binary quadratic model for the classical solver. The QAOA path converts the BQM to Ising form; our Qiskit cost mapping uses x = (1 − Z)/2. The selected order models come from <code>solver/sequence.py → build_sequence_qubo()</code>: A has 1 variable, B has 3. The next chapter gives their polynomials. The earlier time-indexed models and this 8-variable teaching matrix remain comparison material.</p></details>
  </section>`;
}

export function mountMatrixLesson(container) {
  let stage = 3, symmetric = false, selected = [0, 1];
  const bits = [0, 1, 0, 1, 1, 0, 1, 0];
  const $ = selector => container.querySelector(selector);
  function render() {
    const { starts, matrix, reasons, offset } = teachingMatrix(stage, symmetric);
    const descriptions = starts.map((v, i) => `x${i}: ${v.job}/${v.machine} starts ${v.start} h`);
    $('#matrix-stage-note').textContent = ['','Only the four exactly-one squares are included. Machine and route conflicts are not yet penalized.','Machine-overlap penalties are now included; route precedence is still missing.','Complete one-hot feasibility model: exactly-once, machine capacity and job precedence.'][stage];
    $('#matrix-grid').innerHTML = `<table class="qubo-matrix"><caption>Q · ${symmetric ? 'symmetric' : 'upper triangular'} · constant offset ${offset}</caption><thead><tr><th scope="col">Q</th>${starts.map((_, i) => `<th scope="col">x${i}</th>`).join('')}</tr></thead><tbody>${matrix.map((row, i) => `<tr><th scope="row">x${i}</th>${row.map((q, j) => `<td><button class="matrix-entry ${reasons[i][j][0]?.kind || 'empty'}" aria-pressed="${selected[0] === i && selected[1] === j}" aria-label="Q ${i},${j} equals ${q}; ${descriptions[i]}; ${descriptions[j]}" data-matrix-cell="${i},${j}">${q < 0 ? '−' + -q : q}</button></td>`).join('')}</tr>`).join('')}</tbody></table>`;
    const [i, j] = selected;
    $('#matrix-cell-title').textContent = `Q[${i}, ${j}] = ${matrix[i][j]}`;
    const source = reasons[i][j];
    let explanation = source.map(r => r.text).join(' ');
    if (!source.length) explanation = !symmetric && i > j ? 'This lower-triangle cell is zero because each pair is stored only once, above the diagonal. Select its mirrored cell to inspect the pair.' : 'No included penalty contributes to this pair. A zero entry does not require either bit to be zero.';
    if (symmetric && i !== j && matrix[i][j]) explanation += ' This cell holds half of the polynomial coefficient; the mirrored cell holds the other half.';
    $('#matrix-cell-reason').textContent = explanation;
    const diagonal = matrix.reduce((s, row, k) => s + row[k] * bits[k], 0);
    const energy = matrixEnergy(matrix, bits, offset), pair = energy - offset - diagonal;
    $('#matrix-calculation').innerHTML = `<span>SAMPLE x = [${bits.join(', ')}]</span><strong>E = ${offset} + (${diagonal}) + ${pair} = ${energy}</strong><small>offset + diagonal terms + pair terms · ${stage === 3 ? 'complete model: feasible' : 'partial model; zero energy is not yet a feasibility certificate'}</small>`;
    container.querySelectorAll('[data-matrix-cell]').forEach(button => button.addEventListener('click', () => { selected = button.dataset.matrixCell.split(',').map(Number); render(); container.querySelector(`[data-matrix-cell="${selected.join(',')}"]`).focus({ preventScroll: true }); }));
    container.querySelectorAll('[data-matrix-stage]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.matrixStage) === stage)));
  }
  container.querySelectorAll('[data-matrix-stage]').forEach(button => button.addEventListener('click', () => { stage = Number(button.dataset.matrixStage); render(); }));
  $('#matrix-convention').addEventListener('change', event => { symmetric = event.target.value === 'symmetric'; render(); });
  render();
}
