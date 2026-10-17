import {escapeHTML as esc} from './model.js';
const n=(x,d=0)=>Number(x).toLocaleString('en',{maximumFractionDigits:d});
export function summarizeMixer(bundle,caseId,layers=2){
 const source=bundle.mixer,cell=source.cases.find(c=>c.case_id===caseId);
 if(!cell)return null;
 const original=bundle.cases.find(c=>c.id===caseId);
 if(cell.master.pool_sha256!==original.trajectory.pool_sha256)throw Error('Mixer pool mismatch');
 const rows=cell.results.filter(r=>r.label.startsWith('uniform')||r.layers===layers).map(r=>{
  const circuit=source.audit.rows.find(a=>a.case===caseId&&a.method===r.label&&a.seed===r.seed&&a.layers===layers);
  if(!r.label.startsWith('uniform')&&(!circuit?.valid||circuit.qubits!==cell.master.variables))throw Error('Missing matched circuit audit');
  if(r.shots!==source.protocol.shots||r.conditional_exact_energy!==original.trajectory.restricted_exact_objective)throw Error('Mismatched mixer budget/objective');
  if(r.label==='qaoa_xy'&&r.makespan_invariant_leakage>1e-14)throw Error('One-hot leakage');
  return{...r,circuit,pool_optimum_sampled:r.energy===r.conditional_exact_energy};
 });
 const methods=['uniform_all_bits','uniform_onehot','qaoa_x','qaoa_xy'];
 for(const method of methods){const seeds=rows.filter(r=>r.label===method).map(r=>r.seed).sort((a,b)=>a-b);if(JSON.stringify(seeds)!==JSON.stringify(source.protocol.seeds))throw Error('Missing mixer actor');}
 return{rows,master:cell.master,layers,seeds:source.protocol.seeds,methods};
}
function probabilityPlot(s){
 const max=Math.min(1,Math.max(.05,Math.ceil(Math.max(...s.rows.map(r=>r.exact_hit_probability))*24)/20)),y=p=>153-p/max*115;
 const onehot=s.rows.find(r=>r.label==='uniform_onehot').exact_hit_probability,uniform=s.rows.find(r=>r.label==='uniform_all_bits').exact_hit_probability;
 return `<svg class="mixer-probability" viewBox="0 0 730 200" role="img" aria-label="Restricted-pool minimum sample probabilities for all three seeds"><text x="0" y="14">PER-SAMPLE POOL-MINIMUM PROBABILITY</text>${[0,max/2,max].map(p=>`<path class="gantt-grid" d="M65 ${y(p)}H700"/><text x="0" y="${y(p)+4}">${n(100*p,1)}%</text>`).join('')}<path d="M65 ${y(onehot)}H700" stroke="#a36f35" stroke-dasharray="5 4"/><path d="M65 ${y(uniform)}H700" stroke="#8b9aa2" stroke-dasharray="2 3"/>${s.seeds.map((seed,i)=>{const x=150+i*230,a=s.rows.find(r=>r.label==='qaoa_x'&&r.seed===seed),b=s.rows.find(r=>r.label==='qaoa_xy'&&r.seed===seed);return `<path d="M${x} ${y(a.exact_hit_probability)}V${y(b.exact_hit_probability)}" stroke="#91a7b3" stroke-width="2"/><circle cx="${x}" cy="${y(a.exact_hit_probability)}" r="5" fill="#7d8b93"/><circle cx="${x}" cy="${y(b.exact_hit_probability)}" r="6" fill="#315e72"/><text x="${x+12}" y="${y(b.exact_hit_probability)+4}">${n(100*b.exact_hit_probability,2)}%</text><text x="${x}" y="180" text-anchor="middle">SEED ${seed}</text>`;}).join('')}</svg>`;
}
export function mixerView(bundle,caseId,layers=2){
 const s=summarizeMixer(bundle,caseId,layers),protocol=bundle.mixer.protocol,audit=bundle.mixer.audit;
 if(!s)return '<p>No restricted master was built for this failed parent-generation case. No mixer result is invented.</p>';
 const m=s.master,patterns=Array.from({length:m.makespan_bits},(_,i)=>Array.from({length:m.makespan_bits},(_,j)=>i===j?'1':'0').join(''));
 const names={uniform_all_bits:'Uniform, all bits',uniform_onehot:'Uniform, one-hot',qaoa_x:'QAOA X',qaoa_xy:'QAOA XY'};
 return `<div class="mixer-heading"><div><span class="eyebrow">${m.orders} PUMPS / ${m.operations} OPERATIONS / ${m.variables}-BIT RESTRICTED POOL</span><h3>Preserve one-hot. Keep resource penalties.</h3><p>The ${m.trajectory_choice_bits} order-choice bits use X rotations. The ${m.makespan_bits}-bit makespan register starts in a uniform W state and mixes along an XY chain, retaining exactly one selected end time.</p></div><label>QAOA layers<select id="mixer-layers"><option value="1"${layers===1?' selected':''}>p1</option><option value="2"${layers===2?' selected':''}>p2</option></select></label></div><div class="mixer-register" aria-label="Allowed makespan-register basis states">${patterns.map(bits=>`<code>|${bits}⟩</code>`).join('<span>↔</span>')}<small>Uniform W preparation included in audited gate counts</small></div><p><strong>Only the makespan one-hot constraint is preserved.</strong> Incompatible trajectory pairs still carry resource-conflict penalties. The ${m.variables}-bit pool remains a restriction of the raw cell; its earlier measured objective loss remains.</p>
 ${probabilityPlot(s)}<div class="legend"><span><i style="background:#315e72"></i>XY mixer</span><span><i style="background:#7d8b93"></i>X mixer</span><span><i style="background:#a36f35"></i>Uniform one-hot control</span><span><i style="background:#8b9aa2"></i>Unrestricted uniform</span></div><p>${protocol.angle_evaluations} exact simulated expectation evaluations optimize angles per QAOA run, followed by ${protocol.shots} final Born samples. These are not ${protocol.angle_evaluations} physical shots. The one-hot uniform control uses the same valid-register subspace with no angle optimization. All three seeds are retained; no inferential or runtime advantage is established.</p>
 <div class="table-scroll"><table><thead><tr><th>Method / seed</th><th>One-shot pool optimum</th><th>Best of ${protocol.shots} hits optimum?</th><th>Decoded valid?</th><th>Compiled CX</th><th>Logical depth</th><th>QASM</th></tr></thead><tbody>${s.rows.map(r=>`<tr><td>${names[r.label]} / ${r.seed}</td><td class="num">${n(100*r.exact_hit_probability,4)}%</td><td>${r.pool_optimum_sampled?'Yes':'No'}</td><td>${r.decoded_valid?'Yes':'No'}</td><td class="num">${r.circuit?n(r.circuit.compiled_gates.cx??0):'—'}</td><td class="num">${r.circuit?n(r.circuit.compiled_depth):'—'}</td><td>${r.circuit?`<a href="./planning-data/${esc(r.circuit.qasm_file)}" download>QASM ↗</a>`:'Classical control'}</td></tr>`).join('')}</tbody></table></div>
 <p>${audit.circuits} actual X/XY circuits independently match Qiskit ${esc(audit.qiskit_version)} probabilities (maximum error ${audit.max_probability_error.toExponential(2)}), including logical transpilation (maximum error ${audit.max_transpilation_error.toExponential(2)}). Basis ${audit.basis.map(esc).join('/')} · optimization level ${audit.optimization_level} · ${esc(audit.connectivity)}. Counts include W-state preparation. Fewer CX gates may coexist with greater depth; no device execution time follows from these logical counts. No physical QPU or device-calibrated noise claim.</p>`;
}
export function mountMixer(root,bundle,caseId,layers=2,onChange=()=>{}){
 const container=root.querySelector('#planning-mixer');if(!container)return;
 container.innerHTML=mixerView(bundle,caseId,layers);
 container.querySelector('#mixer-layers')?.addEventListener('change',e=>{const next=Number(e.target.value);onChange(next);mountMixer(root,bundle,caseId,next,onChange);});
}
