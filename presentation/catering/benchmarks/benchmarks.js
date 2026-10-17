const labels={frozen:'Trained multi-angle XY',random_angles:'Random-angle search',xy_layerwise:'Plain XY · layerwise',start_only:'Initializer only',uniform_sector:'Uniform one-hot sampling'};
export function comparisonRows(data,caseId,budget){const split=['S2','S3'].includes(caseId)?'test':'train';return data.qaoa[split].table.filter(r=>r.case===caseId&&(r.budget===Number(budget)||r.budget===0));}
export function serviceRows(data,study,status){return data.veloxq.filter(r=>(study==='all'||(study==='noidle'?r.representation==='no-idle-deletion.v1':!r.representation?.includes('deletion')))&&(status==='all'||(status==='completed'?r.status==='completed':r.status!=='completed')));}
export function formatTuple(value){return value?`(${Array.isArray(value)?value:['U','W','B','R'].map(k=>value[k])})`:'—';}
const escape=value=>String(value??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function identityDetails(row){
 const identities=[['Source bundle',row.source_bundle_sha256],['Sampling bundle',row.sampling_bundle_sha256],['Packet',row.packet_sha256]];
 if(!row.source_bundle_sha256&&row.bundle_sha256)identities.unshift(['Bundle',row.bundle_sha256]);
 return `<details class="matrix-identities"><summary>Input identities</summary>${identities.filter(([,hash])=>hash).map(([label,hash])=>`<span class="small">${label} SHA-256</span><code>${escape(hash)}</code>`).join('')}</details>`;
}
const percent=value=>value==null?'—':`${(value*100).toFixed(2)}%`,seconds=value=>value==null?'—':`${value.toFixed(2)}s`;
if(typeof document!=='undefined'){
 const $=s=>document.querySelector(s);
 try{
  const response=await fetch('data.json');if(!response.ok)throw new Error('Result download failed');const data=await response.json();
  function renderQ(){const selected=$('#q-case').value,rows=comparisonRows(data,selected,$('#q-budget').value),reference=data.classical.find(r=>r.case===selected);
   $('#q-reference').innerHTML=`<strong>${escape(selected)} · ${reference.qubits} data qubits</strong> · offered-pool optimum ${formatTuple(reference.portfolio_optimum)}<br>Full-grid reference ${formatTuple(reference.raw_optimum)} — a broader choice set, shown separately.`;
   $('#q-rows').innerHTML=rows.map(r=>`<tr class="${r.config==='frozen'?'trained':''}"><td class="name">${labels[r.config]}<small class="small">${r.budget?r.budget+' loss evaluations':'No training'}</small></td><td class="number">${Math.round(r.success_rate*r.seeds)}/${r.seeds} seeds</td><td class="number">${percent(r.median_ground_probability)}</td><td class="number">${percent(r.median_valid_probability)}</td><td class="number">${formatTuple(r.best_tuple_over_seeds)}</td><td class="number">${seconds(r.median_wall_s)}</td></tr>`).join('');
   $('#q-rows').insertAdjacentHTML('beforeend',`<tr><td>Exact offered-pool reference</td><td>Certified optimum</td><td>—</td><td>100% (feasible reference)</td><td class="number">${formatTuple(reference.portfolio_optimum)}</td><td>—</td></tr>${reference.sa?`<tr><td>Literal-QUBO SA</td><td>Separate retained control</td><td>—</td><td>${reference.sa.valid_returns}/${reference.sa.raw_returns} returned states</td><td class="number">${formatTuple(reference.sa.best_metrics)}</td><td class="number">${seconds(reference.sa.timings?.total_s)}</td></tr>`:''}`);
  }
  function renderRuns(){const rows=data.qaoa_runs.filter(r=>($('#q-config').value==='all'||r.config===$('#q-config').value)&&($('#q-run-case').value==='all'||r.case===$('#q-run-case').value));
   $('#q-run-count').textContent=`${rows.length} of ${data.qaoa_runs.length} retained runs`;
   $('#q-run-rows').innerHTML=rows.map(r=>`<tr><td>${escape(r.case)} / ${escape(r.split)}</td><td>${labels[r.config]}</td><td class="number">${r.budget} / ${r.seed}</td><td class="number">${percent(r.ground_probability)}</td><td class="number">${formatTuple(r.best_valid_tuple)}</td><td class="number">${seconds(r.wall_s)}</td></tr>`).join('');
  }
  function renderV(){const rows=serviceRows(data,$('#v-study').value,$('#v-status').value);$('#v-count').textContent=`${rows.length} of ${data.veloxq.length} recorded attempts. Failed attempts remain visible.`;
   $('#v-rows').innerHTML=rows.map(r=>`<tr><td>${r.attempt} · ${escape(r.case)}<small class="small">${escape(r.job_id?.slice(0,8)||'No job ID')}</small></td><td class="name">${escape(r.representation||r.bundle)}${identityDetails(r)}</td><td class="number">${r.variables??'—'}${r.source_variables?`<small class="small">${r.source_variables}-bit source</small>`:''}</td><td class="number">${r.reps??'—'} × ${r.steps??'—'}</td><td class="number">${r.valid??'—'} / ${r.shots??'—'}</td><td class="number">${formatTuple(r.best)}</td><td class="number">${seconds(r.backend_s)} / ${seconds(r.wall_s)}${r.download_recovered?'<small class="small">Download recovered separately</small>':''}</td><td>${escape(r.status)}</td></tr>`).join('');
  }
  $('#q-case').onchange=renderQ;$('#q-budget').onchange=renderQ;$('#q-config').onchange=renderRuns;$('#q-run-case').onchange=renderRuns;$('#v-study').onchange=renderV;$('#v-status').onchange=renderV;
  function renderVQE(){const rows=data.vqe.grids[$('#vqe-grid').value];$('#vqe-count').textContent=`${rows.length} retained rows; failed/error rows remain included.`;$('#vqe-rows').innerHTML=rows.map(r=>`<tr><td>${escape(r.case)} / ${escape(r.seed)}</td><td class="name">${escape(r.tag||r.spec)}</td><td>${escape(r.loss)} ${escape(r.alpha)}</td><td>${escape(r.shot_hit_opt)}</td><td class="number">${r.p_opt?percent(Number(r.p_opt)):'—'}</td><td>${escape(r.nfev)}</td><td>${escape(r.error||r.status)}</td></tr>`).join('');}
  $('#quantum-comparison').innerHTML=data.vqe.primary_heldout.map(v=>{
   const qrows=[256,2048].map(b=>comparisonRows(data,v.case,b).find(r=>r.config==='frozen'));
   return qrows.map(q=>`<tr><td>${v.case} · QAOA p=3</td><td>${Math.round(q.success_rate*q.seeds)}/${q.seeds} seeds</td><td class="number">${percent(q.median_ground_probability)}</td><td class="number">${percent(q.median_valid_probability)}</td><td>${q.budget} loss evaluations</td><td>4,096</td></tr>`).join('')+`<tr class="trained"><td>${v.case} · VQE L2</td><td>${v.hits}/${v.seeds} seeds</td><td class="number">${percent(v.probability)}</td><td class="number">${percent(v.valid_probability)}</td><td>Median ${v.median_evaluations} adjoint evaluations<small class="small">${v.parameters.join('/')} parameters; ${v.median_shift_equivalents.toLocaleString()} legacy circuit heuristic (2 shifts/parameter)</small></td><td>${v.shots.map(n=>n.toLocaleString()).join('/')}</td></tr>`;
  }).join('');
  $('#vqe-grid').onchange=renderVQE;renderVQE();
  $('#vqe-plans').innerHTML=data.vqe.verification.checked_results.map(r=>`<tr><td>${r.case}</td><td>${r.valid_shots}/${r.shots}</td><td class="number">${formatTuple(r.best)}</td><td>${r.work.objective_evaluations}</td><td>${r.work.hardware_equivalent_circuits.toLocaleString()}</td></tr>`).join('');
  $('#source-list').innerHTML=data.source_files.map(s=>`<li>${escape(s.path)}<code>${escape(s.sha256)}</code></li>`).join('');
  renderQ();renderRuns();renderV();$('#load-status').textContent=`Loaded ${data.qaoa_runs.length} QAOA runs, ${data.veloxq.length} service attempts and ${data.source_files.length} source identities. No optimizer runs on this page.`;
 }catch(error){$('#load-status').textContent=`Unable to load results: ${error.message}. Reload to retry.`;}
}
