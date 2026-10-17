import test from 'node:test';
import assert from 'node:assert/strict';
import {FINAL_SCHEMA,validateFinalView,finalResults} from '../presentation/stage2/final-results.js';
// Deliberately synthetic schema fixture; never copied into a displayed evidence asset.
function fixture(){
 const sha='a'.repeat(64),m={mean:1,actor_mean_environment_cvar90:2,joint_actor_environment_cvar90:3};
 return {schema:FINAL_SCHEMA,status:'complete',evaluation_role:'final',source_files_verified:true,
  sources:{synthetic:{path:'test-only-not-measured.json',sha256:sha}},
  protocol:{protocol_sha256:sha,total_tapes:256,leaves:Array.from({length:8},(_,i)=>({probability:[1,8],per_tape_weight:1/256,seeds:Array.from({length:32},(_,j)=>10000+i*32+j),outcomes:[`test leaf${i}`]}))},
  groups:[10,11,12,13,14,16,24,32].map(orders=>({id:`g${orders}`,method_id:'test-only',config:{orders,horizon:orders===32?14400:5760,profile:'full'},manifest_sha256:sha,evaluation_sha256:sha,source_group_sha256:sha,actor_seeds:[7,13,29],expected_rows:768,actual_rows:768,environment_tapes:256,invalid:0,audit_passed:true,selected_frontier:true,probability_all_orders_fulfilled:.5,metrics:Object.fromEntries(['unfulfilled','total_tardiness_ticks','total_cost','carbon_kg'].map(k=>[k,{...m}]))})),primary_contrasts:[]};
}
test('pending/partial final imports never render provisional performance',()=>{
 assert.equal(validateFinalView(null).ready,false);
 const data=fixture();data.status='partial';data.groups[0].metrics.unfulfilled.mean=54321;
 assert.equal(validateFinalView(data).ready,false);assert.ok(!finalResults(data).includes('54321'));
 assert.match(finalResults(data),/still running or awaiting audit/);
});
test('final scope keeps actors inside256 factories and rejects development tapes/weights',()=>{
 const data=fixture(),result=validateFinalView(data);assert.equal(result.eligible.length,8);assert.equal(result.groups[0].environment_tapes,256);assert.equal(result.groups[0].actual_rows,768);
 assert.match(finalResults(data),/never 768 independent factories/);
 for(const mutate of [d=>d.protocol.leaves[0].seeds[0]=0,d=>d.protocol.leaves[0].seeds[0]=10032,d=>d.protocol.leaves[0].per_tape_weight*=3,d=>d.groups[0].environment_tapes=768,d=>d.groups[0].actor_seeds=[7,7,29],d=>d.groups.pop(),d=>d.evaluation_role='development']){
  const broken=fixture();mutate(broken);assert.throws(()=>validateFinalView(broken));
 }
});
test('unequal stratum probabilities remain true weights instead of equal leaves',()=>{
 const data=fixture();data.protocol.leaves[0].probability=[3,16];data.protocol.leaves[1].probability=[1,16];
 for(const leaf of data.protocol.leaves)leaf.per_tape_weight=leaf.probability[0]/leaf.probability[1]/32;
 assert.equal(validateFinalView(data).ready,true);assert.match(finalResults(data),/3\/16/);
});
test('invalid or missing factory executions cannot become valid-only performance',()=>{
 for(const mutate of [d=>d.groups[0].invalid=1,d=>d.groups[0].actual_rows--,d=>d.groups[0].audit_passed=false]){
  const data=fixture();mutate(data);assert.throws(()=>validateFinalView(data),/suppress performance/);
  delete data.groups[0].metrics;assert.equal(validateFinalView(data).groups[0].eligible,false);assert.match(finalResults(data),/Suppressed/);
 }
});
test('only complete two-contrast97.5 family can be called primary',()=>{
 const data=fixture(),contrast={label:'test only',metric:'missing',predeclared:true,interval:{family_size:2,individual_nominal_coverage:.975,environment_tapes:256,mean_difference:0,percentile_interval:[-1,1]}};
 data.primary_contrasts=[structuredClone(contrast),structuredClone(contrast)];assert.equal(validateFinalView(data).primary.length,2);assert.match(finalResults(data),/Coverage is approximate/);
 data.primary_contrasts[0].interval.individual_nominal_coverage=.95;assert.throws(()=>validateFinalView(data),/97.5/);
 data.primary_contrasts=[contrast];assert.throws(()=>validateFinalView(data),/exactly two/);
});
test('simulation size differs from classical encoded size and missing cost is explicit',()=>{
 const data=fixture();data.quantum_scope={max_simulated_qubits:5,max_encoded_variables:23,classical_fallback_calls:2};
 data.cost_ledger={measured_cpu_seconds:3600,allocated_cpu_hours:null,training_cpu_hours:null,gpu_hours:0,unmeasured_worker_failures:0,scope:'Test-only accounting'};
 assert.match(finalResults(data),/5 qubits/);assert.match(finalResults(data),/23 variables/);assert.match(finalResults(data),/unavailable/);
 data.quantum_scope.max_simulated_qubits=23;assert.throws(()=>validateFinalView(data),/simulation and encoding/);
});
test('audited completed cohorts can be published while whole campaign remains partial',()=>{
 const data=fixture();data.status='partial';data.completed_cohorts_verified=true;data.completed_cohorts=['test-only'];data.missing_cohorts=['pending-test-only'];
 const result=validateFinalView(data);assert.equal(result.ready,true);assert.equal(result.status,'partial');assert.match(finalResults(data),/PARTIAL FINAL CAMPAIGN/);assert.match(finalResults(data),/Not yet included in this export: pending-test-only/);
});

test('imported interim final evidence retains every audited source and fixed selection',async()=>{
 const {readFileSync}=await import('node:fs'),{createHash}=await import('node:crypto');
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url)));
 const report=JSON.parse(readFileSync(new URL('../'+data.sources.strict_final_report.path,import.meta.url)));
 assert.ok(Number.isFinite(Date.parse(data.source_report_artifact_modified_utc)));
 // Git checkout timestamps are not artifact identity. The source bytes are
 // verified by the retained SHA-256 assertions below, including on Vercel.
 if(data.status==='partial')assert.match(finalResults(data),/Not yet included in this export/);else assert.ok(!finalResults(data).includes('Not yet included in this export:'));assert.ok(!finalResults(data).includes('Still pending:'));
 assert.equal(data.status,report.cohort_scope);assert.equal(data.completed_cohorts.length,Object.keys(report.inputs).length);assert.deepEqual(data.missing_cohorts,report.missing_cohorts);
 const result=validateFinalView(data);assert.equal(result.groups.length,report.groups);assert.equal(result.eligible.length,report.groups);
 assert.equal(result.groups.reduce((sum,g)=>sum+g.actual_rows,0),report.executions);
 assert.equal(result.groups.find(g=>g.selected_frontier&&g.config.orders===12).method_id,'static-grid-12');
 assert.equal(result.groups.find(g=>g.selected_frontier&&g.config.orders===16).method_id,'cem6-2026-16');
 for(const source of Object.values(data.sources))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+source.path,import.meta.url))).digest('hex'),source.sha256,source.path);
 assert.equal(data.primary_contrasts.length,2);assert.ok(data.primary_contrasts.every(c=>c.interval.percentile_interval[0]<0&&c.interval.percentile_interval[1]>0));
 assert.equal(data.quantum_scope.max_simulated_qubits,5);assert.ok(data.quantum_scope.max_encoded_variables>5);
 const n32=result.groups.find(g=>g.selected_frontier&&g.config.orders===32);
 assert.ok(n32.primary_certificate.weighted_primary_optimum_attainment>n32.probability_all_orders_fulfilled);
 assert.equal(n32.primary_certificate.secondary_optimality_gap,null);
});
test('final replay files preserve exact source JSON and predeclared tape/actor without outcome selection',async()=>{
 const {readFileSync}=await import('node:fs'),{createHash}=await import('node:crypto'),{gunzipSync}=await import('node:zlib');
 const records=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/final-first-replay-index.json',import.meta.url)));
 for(const row of records){
  const compressed=readFileSync(new URL('../presentation/stage2/'+row.viewer_path.slice(2),import.meta.url));
  assert.equal(createHash('sha256').update(compressed).digest('hex'),row.trace_sha256);
  const original=readFileSync(new URL('../'+row.source_path,import.meta.url));assert.deepEqual(gunzipSync(compressed),original);
  assert.equal(createHash('sha256').update(original).digest('hex'),row.source_trace_sha256);
  const sidecar=JSON.parse(readFileSync(new URL('../'+row.evidence_path,import.meta.url)));
  assert.equal(sidecar.predeclared_first_tape,true);assert.equal(sidecar.activity_data_changed,false);assert.equal(sidecar.fresh_independent_check.valid,true);assert.equal(sidecar.fresh_independent_check.terminal_requirements_met,true);
  const manifest=JSON.parse(readFileSync(new URL('../'+row.source_path.replace(/traces\/[^/]+$/,'manifest.json'),import.meta.url)));
  assert.equal(row.seed,manifest.protocol.payload.leaves[0].seeds[0]);assert.equal(row.actor,manifest.actor_seeds[0]);
  const trace=JSON.parse(original);assert.equal(trace.horizon_ticks,row.config.horizon);assert.equal(trace.metrics.shipped,row.config.orders);assert.ok(trace.metrics.total_tardiness_ticks>0);
 }
});
test('all-zero/all-one outcome bootstrap cannot appear as exact probability confidence',()=>{
 const data=fixture(),g=data.groups[0];g.probability_all_orders_fulfilled=0;
 g.exploratory_frontier_intervals={all_orders_fulfilled_probability:{mean:0,percentile_interval_95:[0,0]}};
 assert.match(finalResults(data),/No observed success; percentile bootstrap does not resolve boundary uncertainty/);
 assert.ok(!finalResults(data).includes('95% exploratory [0, 0]'));
 g.exploratory_frontier_intervals.all_orders_fulfilled_probability={mean:0,percentile_interval_95:null,boundary_probability_bound:{one_sided_nominal_coverage:.95,interval:[0,.01809]}};
 assert.equal(validateFinalView(data).ready,true);assert.match(finalResults(data),/95% one-sided boundary bound/);
});
test('complete final import preserves declared MPC regressions, rare PPO scope and overlapping cost ledger',async()=>{
 const {readFileSync}=await import('node:fs'),{createHash}=await import('node:crypto');
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url)));
 assert.equal(data.status,'complete');assert.equal(data.completed_cohorts.length,10);assert.deepEqual(data.missing_cohorts,[]);assert.equal(data.groups.length,74);assert.equal(data.groups.reduce((s,g)=>s+g.actual_rows,0),23552);assert.equal(data.paired_contrasts.length,41);
 const paired=n=>data.paired_contrasts.find(c=>c.id===`mpc-vs-selected-cheap-${n}`);
 assert.ok(paired(12).missing.mean_difference<0&&paired(16).missing.mean_difference<0&&paired(24).missing.mean_difference>0);
 assert.match(finalResults(data),/MPC retains both improvements and regressions/);
 assert.match(finalResults(data),/Preselected classical controllers/);assert.match(finalResults(data),/QAOA results come from separate matched comparisons/);assert.match(finalResults(data),/hybrid was tested only on TRAIN data and rejected/);
 assert.equal(data.method_annotations.length,1);assert.match(data.method_annotations[0].behavior_observation,/3 → 1 → 3/);assert.match(data.method_annotations[0].limit,/excluded from all 256-tape estimates/);
 const cost=data.cost_ledger,a=cost.research_accounting;assert.equal(cost.gpu_hours,0);assert.equal(a.physical_qpu_calls,0);assert.ok(Math.abs(cost.allocated_cpu_hours-70.41777777777777)<1e-10);assert.ok(cost.allocated_cpu_hours<a.research_completed_allocated_cpu_hours);assert.ok(a.research_running_reported_allocated_cpu_hours>0);assert.equal(a.as_of_utc,'2026-10-17T01:22:27.410937+00:00');
 const archived=data.sources.accounting_ledger_snapshot;assert.equal(createHash('sha256').update(readFileSync(new URL('../'+archived.path,import.meta.url))).digest('hex'),a.inputs['output/stage2-search/compute-ledger.json']);
 assert.match(finalResults(data),/were running at this accounting snapshot/);assert.match(finalResults(data),/overlapping scopes are not additive/);
});
test('nonzero proof replay is separate, selected posthoc,32required/31shipped and never an extra final sample',async()=>{
 const {readFileSync}=await import('node:fs'),{createHash}=await import('node:crypto'),{gunzipSync}=await import('node:zlib');
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url))),p=data.proof_replay;
 assert.equal(data.replays.length,2);assert.ok(data.replays.every(r=>r.predeclared_first_tape));assert.equal(p.predeclared_first_tape,false);assert.equal(p.posthoc_audit_only,true);assert.equal(p.excluded_from_estimates,true);assert.equal(p.orders,32);assert.equal(p.shipped,31);assert.equal(p.necessary_missing_lower_bound,p.checked_missing_upper_bound);assert.equal(p.secondary_optimality_gap,null);
 const bytes=readFileSync(new URL('../presentation/stage2/'+p.viewer_path.slice(2),import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),p.trace_sha256);
 const original=readFileSync(new URL('../'+p.source_path,import.meta.url));assert.deepEqual(gunzipSync(bytes),original);assert.equal(createHash('sha256').update(original).digest('hex'),p.source_trace_sha256);
 const trace=JSON.parse(original);assert.equal(trace.metrics.orders,32);assert.equal(trace.metrics.shipped,31);assert.equal(trace.metrics.all_orders_fulfilled,false);
 for(const [viewer,source]of [[p.declaration_viewer_path,'declaration'],[p.certificate_viewer_path,'necessary_bound'],[p.report_viewer_path,'report']])assert.equal(createHash('sha256').update(readFileSync(new URL('../presentation/stage2/'+viewer.slice(2),import.meta.url))).digest('hex'),p.sources[source].sha256);
 const html=finalResults(data);assert.match(html,/POSTHOC AUDIT ONLY/);assert.match(html,/original frozen evaluation row remains in the 256-tape result/);assert.match(html,/32 required \/31 shipped|32 required \/ 31 shipped/);assert.equal(data.groups.reduce((sum,g)=>sum+g.actual_rows,0),23552);
});
test('lazy proof loader preserves explicit audit-only flag for normal and presentation status labels',async()=>{
 const {readFileSync}=await import('node:fs'),{fetchLinkedTrace}=await import('../presentation/stage2/trace-loader.js');
 const p=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/posthoc-proof-replay-index.json',import.meta.url)));
 const bytes=readFileSync(new URL('../presentation/stage2/'+p.viewer_path.slice(2),import.meta.url)),sidecar=JSON.parse(readFileSync(new URL('../'+p.sources.sidecar.path,import.meta.url)));
 const loaded=await fetchLinkedTrace(p.viewer_path,'http://viewer.local/stage2/',async url=>String(url).endsWith('.gz')?new Response(bytes):Response.json(sidecar));
 assert.equal(loaded.provenance.viewer_replay.posthoc_audit_only,true);assert.match(loaded.provenance.viewer_replay.seed_role,/excluded from 256-tape estimates/);assert.equal(loaded.metrics.shipped,31);assert.equal(loaded.metrics.orders,32);
});
