# VQE for one-hot-constrained scheduling QUBOs: ranked literature review

Prepared 17 Oct 2026 for the catering VQE track. The companion table (53 rows, one per record) is `vqe_literature_table.csv`.

## 0. Scope, verification and deviations

- **Connectors.** No scholarly MCP connector is attached to this project; only Notion, Gmail, Calendar and Docs are. Every record was verified directly against the **Crossref REST API** (DOI resolves, and title, authors, venue, volume and pages match) and/or the **arXiv API** (id resolves, title and authors match). OpenAlex was not needed.
- **Depth of verification.**
  - 41 records: full text downloaded (open access or arXiv). Method fields were extracted from the full text with a structured extraction pass assisted by a language model.
  - 8 of those records: headline numbers were additionally grep-checked against the raw text by me (Kolotouros, Li, Amaro ×2, Wierichs NG, Matsuo, Egger, plus the τ table in the F-VQE paper).
  - 8 records: abstract only.
  - 4 records: metadata only, so their content is *not verified*. These are Kurowski 2023 (no open-access full text; publisher highlights only), Lavrijsen 2020, Fernández-Pendás 2022 and Bärtschi 2019. Roch 2023 is abstract-level. They are marked as such in `verified_via`.
  - Three records are arXiv preprints with no journal DOI in the arXiv metadata: Lee & Lau 2025, Bauer 2023 and Palackal 2023.
- **Seed-list corrections found during verification.**
  - Saleem 2023: the correct DOI is 10.1007/s42979-022-01638-**4**.
  - Tan 2021 is arXiv:2007.01774.
  - The "Fuchs 2022 LX-mixers" seed is two papers: *Constraint Preserving Mixers for QAOA* (Algorithms 15:202, 2022) and *LX-mixers for QAOA* (Quantum 8:1535, **2024**).
  - Sciorilli et al. is Nat. Commun. 16:476 (**2025**).
  - Alessandroni et al. "Big-M" is now npj QI 11:125 (2025).
  - Matsuo et al. was published in IEICE Trans. Inf. & Syst. E106-D (2023).
  - All other seed citations were confirmed as given.
- **Deviations.**
  - The time budget (~75 min) did not allow a manual, line-by-line read of all 41 full texts. Hyperparameter fields for rows I did not grep-check come from the model-assisted extraction, so treat them as **provisional** until checked against the PDF.
  - Nurse-scheduling and flow-shop VQE/QAOA searches on arXiv returned no relevant gate-model paper, so none is included.
  - No experiments were run.

## 1. Diagnosis that drives the ranking

Our loss is exact CVaR_α (Conditional Value-at-Risk: the mean energy of the lowest-energy fraction α of the probability mass) with α = 0.1. This loss is flat in any direction that moves probability *within* the lowest-α tail. Once P(opt) ≥ α, CVaR_α = E_opt and the gradient vanishes, so L-BFGS-B stops with P(opt) ≈ α. Barkoutsos et al. 2020 describe exactly this saturation: on hardware, runs with α = 10% and 25% "attain the corresponding α-level", and they recommend α ∈ [0.1, 0.25]. Amaro et al. 2022 (job shop) see the same effect, with a CVaR-VQE ground-state frequency of ≈59% at α = 0.5.

Mean energy (α = 1) does not saturate, but in our QUBO the penalty P (3e5–1e7) and the lexicographic weights (1…5e4) make the landscape stiff. Mean energy then mostly minimises clash probability and gets trapped (0/10 runs succeed).

The useful literature therefore offers four kinds of fix:

1. **Objectives that keep pushing after P(opt) ≥ α.** These are ascending CVaR, the Gibbs objective and filtering.
2. **Optimisers that escape the local minima** of the non-saturating objectives. These are natural gradient and imaginary-time evolution.
3. **Re-scaling of the energy or penalty**, so that non-saturating objectives become well-conditioned. These are the Big-M bound and Hamiltonian rescaling.
4. **Cheaper circuits.** These are layer and adaptive growth, and evidence that entanglement contributes little.

A unifying implementation note: almost every candidate objective has the form L = G(Σ_x p(x) g_x), where p(x) is the probability of bitstring x and g_x is a fixed function of its energy E_x. Its adjoint gradient is the mean-energy gradient with the diagonal observable diag(g_x), multiplied by G′. The exact-CVaR engine already does this with g_x = min(E_x − VaR_α, 0)/α, where VaR_α is the energy at the α-quantile. Only F-VQE (an amplitude overlap) and natural-gradient/VarQITE (which need the state Jacobian) require new engine features.

## 2. Ranked records (top 22)

Each entry gives the method, its headline result, and what our exact one-hot-sector engine must compute.

### 1. Kolotouros & Wallden 2022: Ascending-CVaR (evolving objective)
- **Citation.** *Phys. Rev. Research* 4, 023225. doi:10.1103/PhysRevResearch.4.023225; arXiv:2105.11766.
- **Method.**
  - The loss is CVaR_{α_t}, with α increased during training.
    - Linear schedule: α_{t+1} = α_t + λ, with λ ∈ [0.025, 0.045].
    - Sigmoid schedule: α_t = 1/(1 + e^{5 − λt}), with λ ∈ [0.3, 0.4].
    - Start at α_0 = 0.01 and finish at α = 1.
  - Shots K = 1000, scaled to K/α_t.
  - Optimiser: COBYLA, with at most 66 × n_params iterations.
  - Ansatz: RY+CZ hardware-efficient ansatz (p = 1), and QAOA with p = 1–6.
  - They prove that the global optimum is preserved along the schedule.
- **Benchmark.** Max-Cut, number partitioning and portfolio optimisation, 15–20 qubits, noiseless Aer simulation. Success means ≥10% overlap with the optimum.
- **Result (verified in text and Table IV).**
  - Max-Cut success: 96% (ascending) vs 84% (α = 0.1), 81% (α = 0.2) and 53% (mean energy).
  - Number partitioning, hardest set: 95% vs ~60% for the best constant CVaR.
  - Portfolio: 100% vs 1% for mean energy.
  - Average overlap with the optimum is up to ~10× higher.
- **Exact simulation.** The loss is a function of p(x) only, and our exact-CVaR engine is reused unchanged. Add an outer α-schedule with warm-started L-BFGS-B per stage. Effort: **low**.
- **Why rank 1.** It removes our saturation mechanism directly. It ends at mean energy, but starts inside the basin that CVaR found.

### 2. Li et al. 2020: Gibbs objective (+ ansatz architecture search)
- **Citation.** *Phys. Rev. Research* 2, 023074. doi:10.1103/PhysRevResearch.2.023074; arXiv:1909.07621.
- **Method.**
  - Loss: f = −log⟨e^{−ηE}⟩, where the average is over Born probabilities p(x).
  - η ≈ (E_0 − E_gs)^{−1}, with E_0 = 0.95·E_gs, which gives η = 20 for their O(1) Ising energies.
  - Ansatz: QAOA p = 1. Optimiser: Nelder–Mead, with initial angles drawn from U(0, 0.1).
  - Ansatz architecture search (AAS): greedy or beam removal of two-qubit gates.
- **Benchmark.** 1000 Ising instances on a 4×4 grid and on a complete graph K10, J ~ U(−1, 1). Exact wavefunction.
- **Result (verified).**
  - Gibbs alone: median relative improvement in P(E < 0.95·E_gs) of +10.8% (grid) and +8.6% (complete).
  - Gibbs + AAS: +44.4% and **+244.7%**, using 20.8% and 33.3% fewer two-qubit gates.
- **Exact simulation.** The loss is a function of p(x). It is smooth, so L-BFGS-B suits it; use log-sum-exp with E_ref = the best energy seen. **η must be re-scaled for us.** Choose η·(E_2nd − E_opt) ≈ 1–5 on the feasible spectrum (at our scales a raw-energy η would underflow), or apply it to rank- or log-transformed energies. For large η the loss approaches −log P(opt) + const, i.e. it directly maximises the probability of the optimum. Effort: **low**.

### 3. Amaro et al. 2022a: Filtering VQE (F-VQE)
- **Citation.** *Quantum Sci. Technol.* 7, 015021. doi:10.1088/2058-9565/ac3e54; arXiv:2106.10055.
- **Method.**
  - At step t, minimise C_t(θ) = ½‖ψ(θ) − F_tψ_{t−1}/‖F_tψ_{t−1}‖‖², which equals 1 − Re⟨ψ_{t−1}|F_t|ψ(θ)⟩/√⟨F_t²⟩.
  - F_t = f(H; τ) is a diagonal filter. Filters tested: inverse H^{−τ}, logarithm (−log H)^τ, exponential e^{−τH} (imaginary-time evolution), power (1−H)^τ, cos^τ H and Chebyshev. Energies are normalised to [E_0, 1].
  - τ is adapted at each step so that the gradient norm is about g_c = 0.1.
  - Optimiser: parameter-shift gradient descent, 70 steps.
  - Ansatz: RY + entangler hardware-efficient ansatz (p = 1…6), starting from |+⟩^n.
- **Benchmark.** Weighted 3-regular Max-Cut, 5–23 qubits, 25 instances per size. Hardware: Quantinuum H1, 9 qubits.
- **Result (verified).**
  - Hardware: approximation ratio 0.9844 ± 0.0062 and **P(ground state) = 0.928 ± 0.024** after 9 steps.
  - Simulation: F-VQE needs fewer steps than VQE or QAOA, with larger and more consistent approximation ratios.
- **Exact simulation.** The loss is an **amplitude** overlap with a frozen vector F_tψ_{t−1}. The adjoint seed is that vector, which is simpler than an energy gradient. Energies must be rescaled into (0, 1]: with our 1e7 penalties, a linear map would make every feasible state look alike, so use rank or log rescaling. Effort: **medium**, because it needs an outer loop and τ root-finding.

### 4. Amaro et al. 2022b: job-shop scheduling case study (VQE vs QAOA vs VarQITE vs F-VQE)
- **Citation.** *EPJ Quantum Technol.* 9, 5. doi:10.1140/epjqt/s40507-022-00123-4; arXiv:2109.03745.
- **Method.**
  - JSP QUBO (job, time, order and idle-slot penalties) from Nippon Steel data; sub-problems with N = 5–23 free qubits.
  - VQE and QAOA use CVaR with α = 0.5 (α = 0.2 in the appendix) and COBYLA.
  - VarQITE uses a McLachlan update.
  - F-VQE uses the inverse filter with adaptive τ.
  - Ansatz: hardware-efficient RY + CNOT, p = 1–2.
  - Shots: 1000 at N = 5, and 450–650 at larger N.
- **Result (verified).**
  - 5 qubits: F-VQE final P(gs) = **84%, 87% and 75%** on three IBM devices, vs ≈59% for CVaR-VQE (bounded near α).
  - Hardware scaling: P(gs) ≈ 80% (10 qubits), 70% (12), 60% (16) and **25% (23)**, with no error mitigation.
- **Exact simulation.** Same as #3. This is the closest scheduling analogue in the literature. Their encoding is penalty-only with no one-hot structure, so our sector restriction should help further.

### 5. Wierichs, Gogolin & Kastoryano 2020: natural gradient avoids local minima
- **Citation.** *Phys. Rev. Research* 2, 043246. doi:10.1103/PhysRevResearch.2.043246; arXiv:2004.14666.
- **Method.**
  - Optimisers compared: BFGS (SciPy), Adam (β = (0.9, 0.999), learning rate 0.02–0.06) and natural gradient (Fubini–Study metric, Tikhonov ε = 1e−4, learning rate 0.05–0.5).
  - Initial angles U[1e−4, 0.05].
  - Ansätze: QAOA-type for the transverse-field Ising model (TFIM), and a Trotterised ansatz for the XXZ model.
- **Result (verified).**
  - TFIM up to N = 40: natural gradient reaches the ground state from **all 20/20 starts at every size**, while BFGS and Adam fail beyond N ≈ 20.
  - With redundant layers: natural-gradient success stays ≥60%, BFGS falls below 50%, and Adam drops to 0%.
  - XXZ: natural gradient is less reliable.
- **Exact simulation.** Needs the quantum geometric tensor (QGT) G_ij = Re⟨∂_iψ|∂_jψ⟩ − ⟨∂_iψ|ψ⟩⟨ψ|∂_jψ⟩, i.e. the state Jacobian (n_par adjoint or forward passes per step). G does not depend on the loss, so it combines with the CVaR, ascending-CVaR or Gibbs gradient. Effort: **medium**.
- **Relevance.** Our L-BFGS-B corresponds to their BFGS, and our parameter count (tens to low hundreds) is in the range where BFGS failed.

### 6. Barkoutsos et al. 2020: CVaR objective (our baseline)
- **Citation.** *Quantum* 4, 256. doi:10.22331/q-2020-04-20-256; arXiv:1907.04769.
- **Method.**
  - CVaR_α = average of the lowest ⌈αK⌉ sampled energies, with α ∈ {1, 5, 10, 25, 50, 75, 100}%.
  - Ansatz: RY + all-to-all CZ, p = 0–2 (and QAOA p = 1–3). Optimiser: COBYLA. Hardware runs use 8192 shots.
- **Benchmark.** Six problem classes, 6–16 qubits, 340 instances.
- **Result.**
  - p = 2, α = 1%: ≥1% P(opt) on almost all instances within 50 normalised iterations, vs 60% of instances for α = 100%.
  - Recommended α: 0.1–0.25.
- **Exact simulation.** Already implemented. It is the control row for every hypothesis below.

### 7. Alessandroni et al. 2025 (arXiv 2023): the quantum Big-M problem
- **Citation.** *npj Quantum Inf.* 11, 125. doi:10.1038/s41534-025-01067-0; arXiv:2307.10379.
- **Method.**
  - Compares penalty weights. The standard M_ℓ1 = ‖Q‖_ℓ1 + δ is the same construction as our P = 1 + Σ|coeffs|. The alternative is M_SDP = f(x_feas) − f_conv + δ, built from an SDP relaxation plus a feasible point.
  - Solved with Trotterised annealing on hardware.
- **Result.** M_SDP raises P(opt) by **more than an order of magnitude** on IonQ Aria-1 (P(opt) > 0.3), whereas the M_ℓ1 distribution is close to uniform.
- **Exact simulation.** Changes the QUBO only. It matters most for the mean-energy, Gibbs, filter and VarQITE losses; CVaR mainly sees the ordering. Effort: **low**. Our P must still respect the lexicographic contract, so compute the tight bound from a CP-SAT or greedy feasible plan.

### 8. Lee & Lau 2025 (preprint): VarQITE for constrained QUBOs (multiple knapsack)
- **Citation.** arXiv:2504.12607.
- **Method.**
  - Imaginary-time evolution (QITE) with the imaginary Hamiltonian variational ansatz (iHVA), using unbalanced penalties λ1 = λ2 = 10.
  - **Hamiltonian rescaling** H/d with d ∈ {1, 10, 100, 1000} or d = ‖H‖; τ = 10 and N_τ ≈ 50–200 steps.
  - Baselines: ma-QAOA and HEA with BFGS.
- **Benchmark.** 68 instances, 9–13 qubits, exact simulation.
- **Result.**
  - Rescaled QITE+iHVA: 100% best-of-5 feasibility, 91.2% best-of-5 optimality, mean optimality rate 52.9%, mean optimality gap 0.31.
  - Comparison gaps: 0.64 (unscaled QITE), 3.47 (ma-QAOA) and 2.35 (HEA).
- **Exact simulation.** Same machinery as #9. Its main lesson for us is that **rescaling decides whether this works** when penalties are large.

### 9. McArdle et al. 2019: variational imaginary-time evolution (VarQITE)
- **Citation.** *npj Quantum Inf.* 5, 75. doi:10.1038/s41534-019-0187-2; arXiv:1804.03023.
- **Method.** McLachlan update Aθ̇ = C, with A_ij = Re⟨∂_iψ|∂_jψ⟩ and C_i = −Re⟨∂_iψ|H|ψ⟩. Euler step δτ = 0.01 (H2) or 0.225 (LiH). Tikhonov λ ∈ [1e−4, 1e−2], chosen by the L-curve.
- **Result.** On LiH (8 qubits, 137 parameters), VarQITE converges to the ground state faster and in a higher fraction of 100 trials than gradient descent.
- **Exact simulation.** VarQITE is natural gradient on mean energy, so it shares the QGT code with #5. Use it with rescaled H.

### 10. Díez-Valle, Porras & García-Ripoll 2021: entanglement and hardness in CVaR-VQE
- **Citation.** *Phys. Rev. A* 104, 062426. doi:10.1103/PhysRevA.104.062426; arXiv:2103.14479.
- **Method.**
  - CVaR with ρ = 0.1. L-BFGS-B for exact wavefunctions; SPSA with K = 3000 or 9000 shots.
  - Ansatz: RY + CZ in linear, circular or all-to-all patterns, or a product state.
  - Random QUBOs at N = 6–12; success means overlap ≥ 0.1.
- **Result.**
  - N = 12, exact: success 98–99% on easy problems and 55–61% on hard ones (Hamming-distance measure d_H ≥ 0.8).
  - 9000 shots: 46–57% on easy problems, 26–30% on hard ones.
  - **Entanglement gives only a marginal gain.**
- **Exact simulation.** Identical pipeline to ours. It motivates the H5 ablation below: drop or prune the inter-block controlled-Givens gates.

### 11. Matsuo et al. 2023 (arXiv 2020): problem-specific circuits from W-states for one-hot constraints
- **Citation.** *IEICE Trans. Inf. & Syst.* E106-D(11), 1772–1782. doi:10.1587/transinf.2023EDP7071; arXiv:2006.05643.
- **Method.**
  - Parameterised W-state blocks (constraint on one line), coupled through CNOT, CSWAP or Hop gates. The permutation-matrix circuit is *exactly* the feasible set.
  - Loss: mean energy. Optimisers: COBYLA (TSP) and Nelder–Mead (minimum vertex cover, MVC). 10 random starts, ≤400 iterations.
- **Benchmark.** 4-city TSP (16 qubits); 6-node MVC.
- **Result (verified).**
  - The exactly-feasible circuit reaches the global minimum **10/10** times; its parameter-sharing version reaches it 9/10.
  - The one-hot-only or partial circuits reach it 3–4/10 times.
  - The RY hardware-efficient ansatz never yields feasible answers.
- **Exact simulation.** Our A2 corresponds to their W-state circuits and our A3 to their coupled circuits. Their result implies that **clash-aware couplers**, which keep amplitude off clashing program pairs, could take the valid-sample rate towards 100%. Effort: medium–high.

### 12. Liu et al. 2022: Layer VQE
- **Citation.** *IEEE Trans. Quantum Eng.* 3, 1–20. doi:10.1109/TQE.2021.3140190; arXiv:2102.05566.
- **Method.**
  - Grow the hardware-efficient ansatz layer by layer. Train layer 0 (RY only) for k0 = 200 iterations, then add a layer initialised at identity and re-optimise.
  - Optimisers: SMO (Nakanishi-type) or COBYLA; 2000-shot estimates.
- **Benchmark.** k-community modularity, up to 40 qubits.
- **Result.** At 40 qubits with finite samples, 2-layer L-VQE has approximation ratio > 0.99 in 30.6% of runs, vs 0% for 2-layer plain VQE. Plain VQE gets worse as layers are added.
- **Exact simulation.** Trivial: identity-initialised controlled-Givens gates. It also starts from a configuration that is easy to optimise.

### 13. Zhu et al. 2022: ADAPT-QAOA
- **Citation.** *Phys. Rev. Research* 4, 033029. doi:10.1103/PhysRevResearch.4.033029; arXiv:2005.10258.
- **Method.**
  - Each layer adds the mixer from a pool with the largest gradient, −i⟨ψ|e^{iγH}[H, A_j]e^{−iγH}|ψ⟩. New γ_0 = 0.01. Optimiser: Nelder–Mead.
- **Benchmark.** Max-Cut, n = 6–10.
- **Result.** Converges in ~3 layers with **about half the CNOTs** and parameters of standard QAOA.
- **Exact simulation.** The gradient of a candidate gate inserted at angle 0 is ⟨ψ|[h_eff, A]|ψ⟩, where h_eff = diag(g_x) is the effective observable of the loss. One adjoint pass scores every candidate block-pair coupler.

### 14. Sack & Serbyn 2021: annealing-schedule initialisation (TQA)
- **Citation.** *Quantum* 5, 491. doi:10.22331/q-2021-07-01-491; arXiv:2101.05742.
- **Method.** Initialise the QAOA angles on a linear annealing ramp with δt ≈ 0.75 (0.55–1.10 depending on the ensemble). Optimiser: BFGS, stopping at gradient norm < 1e−5.
- **Result.** One run from TQA initialisation matches the best of 2^p random starts for p = 1–10 and N = 4–12.
- **Exact simulation.** Loss-agnostic. Replace "random + 0.2 rad noise" by a structured ramp.

### 15. Egger, Mareček & Woerner 2021: warm-starting quantum optimisation
- **Citation.** *Quantum* 5, 479. doi:10.22331/q-2021-06-17-479; arXiv:2009.10095.
- **Method.**
  - Initial state ⊗R_Y(2 arcsin√c*_i)|0⟩ from a QP or SDP relaxation c*, with regulariser ε (ε = 0.25 for Max-Cut), plus a matching mixer.
  - Optimiser: COBYLA with 10–30 restarts.
- **Result (verified).** On portfolio optimisation (6 qubits), P(opt) is **>5× higher** than standard QAOA for p = 1–5.
- **Exact simulation.** Per block, start from amplitudes √c*_k given by an LP relaxation, clipped to [ε, 1−ε], instead of the W-state.

### 16. Stokes et al. 2020: quantum natural gradient (QNG)
- **Citation.** *Quantum* 4, 269. doi:10.22331/q-2020-05-25-269; arXiv:1909.02108.
- **Method and result.** Block-diagonal or diagonal QGT, learning rate 0.01, 8192 shots. QNG reaches the minimum in ~50–100 steps, where vanilla gradient descent fails within 200.
- **Exact simulation.** A cheaper approximation for #5: the diagonal QGT is the per-generator variance.

### 17. Nakanishi, Fujii & Todo 2020: NFT / sequential minimal optimisation
- **Citation.** *Phys. Rev. Research* 2, 043158. doi:10.1103/PhysRevResearch.2.043158; arXiv:1903.12166.
- **Method.** Exact coordinate-wise minimisation from 3 evaluations, a·cos(θ − b) + c. No hyperparameters; 1024 shots.
- **Result.** Fidelity > 0.98 independent of initialisation, where BFGS, CG, Nelder–Mead, Powell and SPSA often fail. Robust down to 256 shots.
- **Exact simulation.** Each Givens or controlled-Givens angle enters p(x) as a + b·cos2θ + c·sin2θ. NFT is therefore exact for losses linear in p(x), and for Gibbs (a monotone transform of a linear functional). It is *not* exact for CVaR. This is the strongest finite-shot candidate.

### 18. Herman et al. 2023: constrained optimisation via quantum Zeno dynamics
- **Citation.** *Commun. Phys.* 6, 219. doi:10.1038/s42005-023-01331-9; arXiv:2209.15024.
- **Method.** Repeated projective measurement onto the feasible subspace, N_j = ⌈β_j²/η⌉. Compared with penalty QAOA (λ swept from 1e−4 to 1e2), with COBYLA. Includes a Zeno-enhanced L-VQE.
- **Result.**
  - The Zeno method beats penalty QAOA on all 14 portfolio instances, in both approximation ratio r and in-constraint probability.
  - Zeno L-VQE: r = 0.811–0.995 and in-constraint probability 0.914–0.9996.
- **Exact simulation.** Apply the projector onto clash-free states after each layer and renormalise, recording the survival probability as the postselection cost.

### 19. Wang et al. 2020: XY mixers
- **Citation.** *Phys. Rev. A* 101, 012320. doi:10.1103/PhysRevA.101.012320; arXiv:1904.09314.
- **Result.**
  - One-hot graph colouring with ring XY mixer and W-state start: P(opt) ≈ 0.2 at p = 1 and >0.6 at p = 3.
  - X mixer + penalty: approximation ratio ~0.2, even with the best α* = 1.7.
- **Relevance.** Validates our sector-preserving design. Their ring vs complete XY mixers offer a cheap topology ablation inside blocks.

### 20. Niroula et al. 2022: constrained QAOA (Dicke + XY) vs L-VQE on a trapped-ion device
- **Citation.** *Sci. Rep.* 12, 17171. doi:10.1038/s41598-022-20853-w; arXiv:2206.06290.
- **Result.** On H1-1 (20 qubits), XY-QAOA reaches approximation ratio ≤92.1% and in-constraint probability ≤91.4%. In noiseless simulation the in-constraint probability is 1 by construction, whereas penalty QAOA sits near 0.06.

### 21. Ostaszewski, Grant & Benedetti 2021: Rotosolve / Rotoselect
- **Citation.** *Quantum* 5, 391. doi:10.22331/q-2021-01-28-391; arXiv:1905.09692.
- **Method and result.** Closed-form coordinate updates (3 evaluations per gate); Rotoselect also chooses the generator. Both use fewer evaluations than Adam or SPSA.
- **Exact simulation.** Same applicability as NFT. Rotoselect gives a cheap structure search over gate types.

### 22. Zhou et al. 2020: QAOA performance and the INTERP/FOURIER heuristics
- **Citation.** *Phys. Rev. X* 10, 021067. doi:10.1103/PhysRevX.10.021067; arXiv:1812.01041.
- **Result.** Heuristic initialisation matches the best of 1000–40000 random BFGS starts. The number of random starts needed grows exponentially in p, roughly 0.42·2.63^p for unweighted 3-regular graphs.
- **Exact simulation.** Train 1 layer, then interpolate to 2–3 layers.

**Ranks 23–53** are in the CSV. They are context or low priority for our weakness:
- Threshold and Grover approaches: Golden 2021, Bärtschi 2020, Gilliam 2021.
- Penalty encodings: Montañez-Barrera 2024 (unbalanced penalties; inequality constraints, which we do not have), Roch 2023 (abstract only).
- Mixer gate cost: Fuchs 2022/2024 (LX mixers: one-hot mixer CNOT cost reduced, e.g. from 96 to 10).
- Ansatz and mixer design: Gard 2020 (particle-conserving A-gates, ≤3·C(n,m) CNOTs), Hadfield 2019, Saleem 2023, Chandarana 2022 (counter-diabatic QAOA), Palackal 2023 (FJSP permutation mixers; theory only).
- Optimiser benchmarks: Bonet-Monroig 2023 (tuned CMA-ES ≈ tuned SPSA; chemistry), Lavrijsen 2020 and Fernández-Pendás 2022 (both metadata only).
- Warm starts, growth and landscapes: Tate 2023, Skolik 2021, Grimsley 2019, Anschuetz 2022 (traps in shallow circuits).
- Gradients and shot-frugal optimisers: Wierichs 2022 (general parameter-shift rules), Kübler 2020 (iCANS), Sung 2020.
- Scheduling and encodings: Kurowski 2023, Venturelli 2015, Bauer 2023 (QITE), Tabi 2020, Glos 2022, Tan 2021, Sciorilli 2025 and Chancellor 2019 (encodings; qubit reduction rather than P(opt)), Bärtschi 2019 (Dicke-state preparation).

## 3. Testable hypotheses (predicted direction)

All hypotheses share the same protocol so that they can be compared:
- Control: the current A3 setup (2 layers, W-state + 0.2 rad noise, exact CVaR_0.1, L-BFGS-B adjoint).
- Instances: the same suite and the held-out case.
- Seeds: 10.
- Report: success rate (most probable valid sample, or best sample, equals the CP-SAT optimum), final P(opt), valid-sample rate, function and gradient evaluations, and 2-qubit gate count.

**H1 – Ascending CVaR removes the P(opt) ≈ α ceiling.** (Kolotouros 2022; Barkoutsos 2020)
- Setup: warm-started L-BFGS-B stages with α ∈ {0.1, 0.2, 0.35, 0.5, 0.75, 1.0}, or Kolotouros's sigmoid schedule (λ = 0.35, α_0 = 0.01).
- Prediction: median final P(opt) rises from 0.08–0.3 to **≥0.5**, and the valid-sample rate rises from 31–60% to **≥80%**, because α → 1 charges for all infeasible mass. Success should be ≥ control, with the held-out case at 10/10.
- Risk: the final α = 1 stage may drift into the mean-energy trap. Guard against it by keeping the best-P(opt) checkpoint.

**H2 – A Gibbs loss with η annealing outperforms fixed CVaR on P(opt), and matches or beats H1.** (Li 2020)
- Setup: L = −log Σ p(x)·exp(−η(E_x − E_best)), with η·ΔE_feasible ramped from ~0.5 to ~5. Here ΔE_feasible is the gap between the best and second-best feasible energies, or a lexicographic level.
- Prediction: P(opt) **≥0.5** with smoother convergence (fewer L-BFGS-B line-search failures). Success is equal to H1 at high η and lower if η is too large too early, because rare events make the loss flat.

**H3 – Rescaling the energy (tight P, then a monotone rank or log transform) makes non-saturating losses trainable.** (Alessandroni 2025; Lee & Lau 2025)
- Setup: replace P = 1 + Σ|coeffs| by P_tight = f(x_CP-SAT) − f_LB + 1. Additionally apply g(E) = log(1 + E − E_min), or the rank of E within the feasible sector, before the mean-energy / Gibbs / F-VQE loss.
- Prediction: mean-energy success rises from **0/10 to ≥5/10**. The ordering of plans and the CVaR optimum are unchanged, so the CVaR-only control is barely affected (a negative control).

**H4 – Imaginary-time-type updates (F-VQE with the inverse/exponential filter, or VarQITE/QNG with the exact QGT) give geometric growth of P(opt).** (Amaro 2022a/b; McArdle 2019; Wierichs 2020)
- Prediction: P(opt) **≥0.8** within ≤30 outer steps on the 31–35-variable cells, and success ≥ H1.
- Cost: about n_par extra statevector passes per step. Natural gradient on top of H1/H2 should recover the seeds that miss with L-BFGS-B (the held-out case goes from 9/10 to 10/10).

**H5 – Adaptive growth of inter-block couplers reduces circuit cost by ≥50% at equal success.** (Zhu 2022; Liu 2022; Díez-Valle 2021)
- Setup: start from A2 (intra-block Givens only) trained with the H1 or H2 loss. Score every candidate controlled-Givens coupler by |⟨ψ|[h_eff, A]|ψ⟩| at angle 0, add the top-k (k = 1–3) per round with identity initialisation, and stop when the loss improves by less than 1e−3·|E_opt|.
- Prediction: ≤50% of A3's controlled-Givens count at the same success. Díez-Valle predicts that the pure A2 + H1 configuration already reaches ≥ A3 + CVaR success on most cells.

**H6 – With finite shots, NFT/Rotosolve on the Gibbs loss beats SPSA and COBYLA.** (Nakanishi 2020; Ostaszewski 2021; Bonet-Monroig 2023; Kolotouros 2022)
- Setup:
  - Sampled Gibbs objective, optimised with NFT coordinate updates using 3 evaluations per angle, which is exact because each angle contributes a single frequency.
  - Sampled ascending CVaR with K/α_t shots, optimised with SPSA (a = 0.15, α = 0.602, c = 0.2, γ = 0.101 defaults, then tuned).
  - The same sampled ascending CVaR optimised with COBYLA.
  - Shot budget: 1e3–1e4 shots per evaluation.
- Prediction: NFT-Gibbs keeps ≥80% of its exact-simulation P(opt), while SPSA and COBYLA lose more. SPSA is expected to need a 3–10× larger total shot budget for the same success.
- Caveat: at large η the Gibbs estimator has high variance, so cap η·ΔE at about 3.

## 4. What the adjoint engine needs

| Loss / optimiser | Function of | New engine work |
|---|---|---|
| CVaR, ascending CVaR | p(x) | none (outer α loop) |
| Gibbs −log Σ p e^{−ηE} | p(x) | diagonal observable e^{−η(E−E_ref)}, chain factor −1/Z |
| Rank/log-rescaled mean | p(x) | diagonal observable g(E) |
| F-VQE (filter) | amplitudes (overlap with F ψ_{t−1}) | adjoint seeded with a fixed vector; outer loop + τ search |
| Zeno projection | amplitudes | projector after each layer + renormalisation |
| Natural gradient / VarQITE | state Jacobian ∂ψ/∂θ | QGT (n_par passes), regularised linear solve |
| ADAPT scoring | ⟨ψ|[h_eff, A]|ψ⟩ | one backward pass over the candidate pool |
| NFT/Rotosolve | p(x) (linear or monotone loss) | 3 loss evaluations per angle; no gradient |

## 5. References (verified; full metadata in `vqe_literature_table.csv`)

1. Kolotouros, I., Wallden, P. (2022). Evolving objective function for improved variational quantum optimization. *Phys. Rev. Research* 4, 023225. doi:10.1103/PhysRevResearch.4.023225. arXiv:2105.11766.
2. Li, L., Fan, M., Coram, M., Riley, P., Leichenauer, S. (2020). Quantum optimization with a novel Gibbs objective function and ansatz architecture search. *Phys. Rev. Research* 2, 023074. doi:10.1103/PhysRevResearch.2.023074. arXiv:1909.07621.
3. Amaro, D., Modica, C., Rosenkranz, M., Fiorentini, M., Benedetti, M., Lubasch, M. (2022). Filtering variational quantum algorithms for combinatorial optimization. *Quantum Sci. Technol.* 7, 015021. doi:10.1088/2058-9565/ac3e54. arXiv:2106.10055.
4. Amaro, D., Rosenkranz, M., Fitzpatrick, N., Hirano, K., Fiorentini, M. (2022). A case study of variational quantum algorithms for a job shop scheduling problem. *EPJ Quantum Technol.* 9, 5. doi:10.1140/epjqt/s40507-022-00123-4. arXiv:2109.03745.
5. Wierichs, D., Gogolin, C., Kastoryano, M. (2020). Avoiding local minima in variational quantum eigensolvers with the natural gradient optimizer. *Phys. Rev. Research* 2, 043246. doi:10.1103/PhysRevResearch.2.043246. arXiv:2004.14666.
6. Barkoutsos, P. Kl., Nannicini, G., Robert, A., Tavernelli, I., Woerner, S. (2020). Improving variational quantum optimization using CVaR. *Quantum* 4, 256. doi:10.22331/q-2020-04-20-256. arXiv:1907.04769.
7. Alessandroni, E., Ramos-Calderer, S., Roth, I., Traversi, E., Aolita, L. (2025). Alleviating the quantum Big-M problem. *npj Quantum Inf.* 11, 125. doi:10.1038/s41534-025-01067-0. arXiv:2307.10379.
8. Lee & Lau (2025) [surnames as listed by arXiv]. Solving constrained combinatorial optimization problems with variational quantum imaginary time evolution. arXiv:2504.12607 (preprint).
9. McArdle, S., Jones, T., Endo, S., Li, Y., Benjamin, S. C., Yuan, X. (2019). Variational ansatz-based quantum simulation of imaginary time evolution. *npj Quantum Inf.* 5, 75. doi:10.1038/s41534-019-0187-2. arXiv:1804.03023.
10. Díez-Valle, P., Porras, D., García-Ripoll, J. J. (2021). Quantum variational optimization: the role of entanglement and problem hardness. *Phys. Rev. A* 104, 062426. doi:10.1103/PhysRevA.104.062426. arXiv:2103.14479.
11. Matsuo, A., Suzuki, Y., Hamamura, I., Yamashita, S. (2023). Enhancing VQE convergence for optimization problems with problem-specific parameterized quantum circuits. *IEICE Trans. Inf. & Syst.* E106-D(11), 1772–1782. doi:10.1587/transinf.2023EDP7071. arXiv:2006.05643.
12. Liu, X., Angone, A., Shaydulin, R., Safro, I., Alexeev, Y., Cincio, L. (2022). Layer VQE. *IEEE Trans. Quantum Eng.* 3, 1–20. doi:10.1109/TQE.2021.3140190. arXiv:2102.05566.
13. Zhu, L., Tang, H. L., Barron, G. S., et al. (2022). Adaptive quantum approximate optimization algorithm for solving combinatorial problems on a quantum computer. *Phys. Rev. Research* 4, 033029. doi:10.1103/PhysRevResearch.4.033029. arXiv:2005.10258.
14. Sack, S. H., Serbyn, M. (2021). Quantum annealing initialization of the quantum approximate optimization algorithm. *Quantum* 5, 491. doi:10.22331/q-2021-07-01-491. arXiv:2101.05742.
15. Egger, D. J., Mareček, J., Woerner, S. (2021). Warm-starting quantum optimization. *Quantum* 5, 479. doi:10.22331/q-2021-06-17-479. arXiv:2009.10095.
16. Stokes, J., Izaac, J., Killoran, N., Carleo, G. (2020). Quantum natural gradient. *Quantum* 4, 269. doi:10.22331/q-2020-05-25-269. arXiv:1909.02108.
17. Nakanishi, K. M., Fujii, K., Todo, S. (2020). Sequential minimal optimization for quantum-classical hybrid algorithms. *Phys. Rev. Research* 2, 043158. doi:10.1103/PhysRevResearch.2.043158. arXiv:1903.12166.
18. Herman, D., Shaydulin, R., Sun, Y., et al. (2023). Constrained optimization via quantum Zeno dynamics. *Commun. Phys.* 6, 219. doi:10.1038/s42005-023-01331-9. arXiv:2209.15024.
19. Wang, Z., Rubin, N. C., Dominy, J. M., Rieffel, E. G. (2020). XY mixers: analytical and numerical results for QAOA. *Phys. Rev. A* 101, 012320. doi:10.1103/PhysRevA.101.012320. arXiv:1904.09314.
20. Niroula, P., Shaydulin, R., Yalovetzky, R., et al. (2022). Constrained quantum optimization for extractive summarization on a trapped-ion quantum computer. *Sci. Rep.* 12, 17171. doi:10.1038/s41598-022-20853-w. arXiv:2206.06290.
21. Ostaszewski, M., Grant, E., Benedetti, M. (2021). Structure optimization for parameterized quantum circuits. *Quantum* 5, 391. doi:10.22331/q-2021-01-28-391. arXiv:1905.09692.
22. Zhou, L., Wang, S.-T., Choi, S., Pichler, H., Lukin, M. D. (2020). Quantum approximate optimization algorithm: performance, mechanism, and implementation on near-term devices. *Phys. Rev. X* 10, 021067. doi:10.1103/PhysRevX.10.021067. arXiv:1812.01041.
23. Golden, J., Bärtschi, A., O'Malley, D., Eidenbenz, S. (2021). Threshold-based quantum optimization. *IEEE QCE 2021*, 137–147. doi:10.1109/QCE52317.2021.00030. arXiv:2106.13860.
24. Montañez-Barrera, J. A., Willsch, D., Maldonado-Romo, A., Michielsen, K. (2024). Unbalanced penalization. *Quantum Sci. Technol.* 9, 025022. doi:10.1088/2058-9565/ad35e4. arXiv:2211.13914.
25. Fuchs, F. G., Bassa, R. P. (2024). LX-mixers for QAOA. *Quantum* 8, 1535. doi:10.22331/q-2024-11-25-1535. arXiv:2306.17083.
26. Fuchs, F. G., Lye, K. O., Møll Nilsen, H., Stasik, A. J., Sartor, G. (2022). Constraint preserving mixers for the quantum approximate optimization algorithm. *Algorithms* 15, 202. doi:10.3390/a15060202. arXiv:2203.06095.
27. Gard, B. T., Zhu, L., Barron, G. S., et al. (2020). Efficient symmetry-preserving state preparation circuits for the VQE algorithm. *npj Quantum Inf.* 6, 10. doi:10.1038/s41534-019-0240-1. arXiv:1904.10910.
28. Hadfield, S., Wang, Z., O'Gorman, B., Rieffel, E. G., Venturelli, D., Biswas, R. (2019). From the QAOA to a quantum alternating operator ansatz. *Algorithms* 12, 34. doi:10.3390/a12020034. arXiv:1709.03489.
29. Bonet-Monroig, X., Wang, H., Vermetten, D., et al. (2023). Performance comparison of optimization methods on variational quantum algorithms. *Phys. Rev. A* 107, 032407. doi:10.1103/PhysRevA.107.032407. arXiv:2111.13454.
30. Chandarana, P., Hegade, N. N., Paul, K., et al. (2022). Digitized-counterdiabatic QAOA. *Phys. Rev. Research* 4, 013141. doi:10.1103/PhysRevResearch.4.013141. arXiv:2107.02789.
31. Saleem, Z. H., Tomesh, T., Tariq, B., Suchara, M. (2023). Approaches to constrained quantum approximate optimization. *SN Comput. Sci.* 4, 183. doi:10.1007/s42979-022-01638-4. arXiv:2010.06660.
32. Bärtschi, A., Eidenbenz, S. (2020). Grover mixers for QAOA. *IEEE QCE 2020*, 72–82. doi:10.1109/QCE49297.2020.00020. arXiv:2006.00354.
33. Kurowski, K., Pecyna, T., Słysz, M., Różycki, R., Waligóra, G., Węglarz, J. (2023). Application of quantum approximate optimization algorithm to job shop scheduling problem. *Eur. J. Oper. Res.* 310(2), 518–528. doi:10.1016/j.ejor.2023.03.013. (metadata only)
34. Tate, R., Farhadi, M., Herold, C., Mohler, G., Gupta, S. (2023). Bridging classical and quantum with SDP initialized warm-starts for QAOA. *ACM Trans. Quantum Comput.* 4, 1–39. doi:10.1145/3549554. arXiv:2010.14021.
35. Skolik, A., McClean, J. R., Mohseni, M., van der Smagt, P., Leib, M. (2021). Layerwise learning for quantum neural networks. *Quantum Mach. Intell.* 3, 5. doi:10.1007/s42484-020-00036-4. arXiv:2006.14904.
36. Wierichs, D., Izaac, J., Wang, C., Lin, C. Y.-Y. (2022). General parameter-shift rules for quantum gradients. *Quantum* 6, 677. doi:10.22331/q-2022-03-30-677. arXiv:2107.12390.
37. Grimsley, H. R., Economou, S. E., Barnes, E., Mayhall, N. J. (2019). An adaptive variational algorithm for exact molecular simulations on a quantum computer. *Nat. Commun.* 10, 3007. doi:10.1038/s41467-019-10988-2. arXiv:1812.11173.
38. Anschuetz, E. R., Kiani, B. T. (2022). Quantum variational algorithms are swamped with traps. *Nat. Commun.* 13, 7760. doi:10.1038/s41467-022-35364-5. arXiv:2205.05786.
39. Kübler, J. M., Arrasmith, A., Cincio, L., Coles, P. J. (2020). An adaptive optimizer for measurement-frugal variational algorithms. *Quantum* 4, 263. doi:10.22331/q-2020-05-11-263. arXiv:1909.09083.
40. Sung, K. J., Yao, J., Harrigan, M. P., et al. (2020). Using models to improve optimizers for variational quantum algorithms. *Quantum Sci. Technol.* 5, 044008. doi:10.1088/2058-9565/abb6d9. arXiv:2005.11011.
41. Lavrijsen, W., Tudor, A., Müller, J., Iancu, C., de Jong, W. (2020). Classical optimizers for noisy intermediate-scale quantum devices. *IEEE QCE 2020*, 267–277. doi:10.1109/QCE49297.2020.00041. arXiv:2004.03004. (metadata only)
42. Fernández-Pendás, M., Combarro, E. F., Vallecorsa, S., et al. (2022). A study of the performance of classical minimizers in the quantum approximate optimization algorithm. *J. Comput. Appl. Math.* 404, 113388. doi:10.1016/j.cam.2021.113388. (metadata only)
43. Bauer, N., Alam, K., Ostrowski, J., Siopsis, G. (2023). Combinatorial optimization with quantum imaginary time evolution. arXiv:2312.16664 (preprint).
44. Roch, C., Ratke, D., Nüßlein, J., Gabor, T., Feld, S. (2023). The effect of penalty factors of constrained Hamiltonians on the eigenspectrum in quantum annealing. *ACM Trans. Quantum Comput.* 4, 1–18. doi:10.1145/3577202. (abstract only; full text not accessible)
45. Palackal, L., Richter, L., Hess, M. (2023). Graph-controlled permutation mixers in QAOA for the flexible job-shop problem. arXiv:2311.04100 (preprint).
46. Venturelli, D., Marchand, D. J. J., Rojo, G. (2015). Quantum annealing implementation of job-shop scheduling. arXiv:1506.08479.
47. Gilliam, A., Woerner, S., Gonciulea, C. (2021). Grover adaptive search for constrained polynomial binary optimization. *Quantum* 5, 428. doi:10.22331/q-2021-04-08-428. arXiv:1912.04088.
48. Tabi, Z., El-Safty, K. H., Kallus, Z., et al. (2020). Quantum optimization for the graph coloring problem with space-efficient embedding. *IEEE QCE 2020*, 56–62. doi:10.1109/QCE49297.2020.00018. arXiv:2009.07314.
49. Glos, A., Krawiec, A., Zimborás, Z. (2022). Space-efficient binary optimization for variational quantum computing. *npj Quantum Inf.* 8, 39. doi:10.1038/s41534-022-00546-y. arXiv:2009.07309.
50. Tan, B., Lemonde, M.-A., Thanasilp, S., Tangpanitanon, J., Angelakis, D. G. (2021). Qubit-efficient encoding schemes for binary optimisation problems. *Quantum* 5, 454. doi:10.22331/q-2021-05-04-454. arXiv:2007.01774.
51. Sciorilli, M., Borges, L., Patti, T. L., et al. (2025). Towards large-scale quantum optimization solvers with few qubits. *Nat. Commun.* 16, 476. doi:10.1038/s41467-024-55346-z. arXiv:2401.09421.
52. Chancellor, N. (2019). Domain wall encoding of discrete variables for quantum annealing and QAOA. *Quantum Sci. Technol.* 4, 045004. doi:10.1088/2058-9565/ab33c2. arXiv:1903.05068.
53. Bärtschi, A., Eidenbenz, S. (2019). Deterministic preparation of Dicke states. *FCT 2019*, LNCS, 126–139. doi:10.1007/978-3-030-25027-0_9. arXiv:1904.07358. (metadata only)


Note: author initials in this list were typed from the author records and should be checked before formal citation; surnames, titles, venues, volumes, pages and DOIs were matched against Crossref/arXiv.
