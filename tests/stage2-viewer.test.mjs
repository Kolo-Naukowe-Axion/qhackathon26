import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {summarizeGrid,summarizeTooling,mountResearch} from '../presentation/stage2/research.js';
import {summarizeRecovery,summarizeHorizons,summarizePrimary} from '../presentation/stage2/frontier.js';
import {summarizeObjective} from '../presentation/stage2/objective.js';
import {fetchLinkedTrace} from '../presentation/stage2/trace-loader.js';
import {summarizeConfirmation} from '../presentation/stage2/objective-confirmation.js';
import {SCHEMA,blueprint,fixture,normalizeTrace,snapshot,machineStatus,unitGenealogy,resourceOccupancy,deadlineEvidence,escapeHTML} from '../presentation/stage2/model.js';

test('blueprint has no measured or invented activities',()=>{
 const trace=blueprint();assert.equal(trace.resources.machines.length,15);assert.equal(trace.resources.agvs.length,4);assert.equal(trace.resources.workers.length,10);assert.equal(trace.provenance.kind,'blueprint');assert.equal(trace.operations.length,0);assert.deepEqual(trace.metrics,{});
});
test('synthetic fixture stays explicitly unvalidated',()=>{
 const trace=fixture();assert.equal(trace.provenance.kind,'synthetic');assert.equal(trace.validation.status,'not_validated');assert.ok(trace.operations.length>0);
});
test('half-open operations finish before boundary starts',()=>{
 const trace=fixture();assert.ok(snapshot(trace,1).active.some(row=>row.id==='H-T'));assert.ok(!snapshot(trace,5).active.some(row=>row.id==='H-T'));assert.ok(snapshot(trace,5).completed.some(row=>row.id==='H-T'));
});
test('batch members move only at pickup and assembly consumes parents',()=>{
 const trace=normalizeTrace({schema:SCHEMA,horizon_ticks:20,resources:{machines:[{id:'H1'},{id:'A1'}]},operations:[{id:'heat',unit_ids:['h','r'],unit_id:'h',machine_id:'H1',start:0,end:4},{id:'assemble',unit_ids:['pump'],unit_id:'pump',parent_unit_ids:['h','r'],process:'ASSEMBLY',machine_id:'A1',start:10,end:13}],moves:[{id:'m',unit_id:'h',agv_id:'AGV1',from:'H1',to:'A1',start:4,pickup_tick:6,drop_tick:9,end:9}]});
 assert.equal(snapshot(trace,5).location.get('h'),'H1');assert.equal(snapshot(trace,6).location.get('h'),'AGV1');assert.equal(snapshot(trace,9).location.get('h'),'A1');assert.equal(snapshot(trace,10).location.has('h'),false);assert.equal(snapshot(trace,12).location.has('pump'),false);assert.equal(snapshot(trace,13).location.get('pump'),'A1');assert.equal(machineStatus(trace,'H1',5).state,'output held');assert.deepEqual(unitGenealogy(trace,'pump').parents,['h','r']);assert.equal(unitGenealogy(trace,'r').operations[0].id,'heat');
 assert.deepEqual(resourceOccupancy(trace,5).buffers.find(row=>row.machine_id==='H1').output,['h','r']);assert.deepEqual(resourceOccupancy(trace,5).buffers.find(row=>row.machine_id==='A1').reserved,['h']);assert.deepEqual(resourceOccupancy(trace,9).buffers.find(row=>row.machine_id==='A1').reserved,[]);assert.deepEqual(resourceOccupancy(trace,9).buffers.find(row=>row.machine_id==='A1').input,['h']);
});
test('malformed display inputs cannot silently become runs',()=>{
 assert.throws(()=>normalizeTrace({schema:'wrong'}),/Unsupported/);assert.throws(()=>normalizeTrace({schema:SCHEMA,resources:{machines:[]},operations:[{machine_id:'X',start:0,end:1}]}),/Unknown machine/);assert.throws(()=>normalizeTrace({schema:SCHEMA,horizon_ticks:2,resources:{machines:[{id:'M'}]},operations:[{machine_id:'M',start:1,end:3}]}),/beyond/);assert.equal(escapeHTML('<script>"&'), '&lt;script&gt;&quot;&amp;');
});
test('automatic processing releases its worker while holding the tool',()=>{
 const trace=normalizeTrace({schema:SCHEMA,horizon_ticks:20,resources:{machines:[{id:'F1'}]},operations:[{id:'mill',unit_id:'housing',machine_id:'F1',start:1,end:15,worker_ids:['W1'],worker_intervals:[{worker_id:'W1',start:1,end:4}],tool_ids:['kit']}]});
 assert.equal(resourceOccupancy(trace,3).workers.length,1);assert.equal(resourceOccupancy(trace,4).workers.length,0);assert.equal(resourceOccupancy(trace,4).tools.length,1);
});
test('research view derives its frontier from frozen, hash-matched measured artifacts',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 assert.equal(evidence.schema,'stage2-research-evidence.v1');
 for(const source of Object.values(evidence.sources)){
  const bytes=readFileSync(new URL(`../${source.path}`,import.meta.url));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),source.sha256,source.path);
 }
 const grid=summarizeGrid(evidence.data.grid);assert.equal(grid.runs,2688);assert.equal(grid.valid,2688);
 assert.deepEqual(grid.orders,[3,6,8,12,16,24,32]);
 const load8=grid.best.find(row=>row.orders===8);assert.equal(load8.policy_id,'w6-eco-lease1-priority');assert.equal(load8.complete_runs,8);
 assert.ok(grid.best.find(row=>row.orders===24).mean_unfulfilled>0);
 assert.equal(evidence.data.bounds.full_model_infeasibility_proven,false);
 for(const [name,data]of Object.entries(evidence.data))if(name.startsWith('tiny_')){
  assert.equal(data.exact.status,'OPTIMAL');assert.equal(data.exact.validation.valid,true);assert.equal(data.heuristic_validation.valid,true);assert.equal(data.comparison.flagship_global_gap,null);
 }
 assert.equal(evidence.data.quantum.physical_quantum_executed,false);assert.ok(evidence.data.quantum.runs.every(run=>run.selected_makespan===8&&!run.official_validator_errors.length));
 assert.equal(evidence.data.rank_three_model.decoder.derived_c,'1-a+a*b');
 assert.equal(evidence.data.rank_three_model.variables.length,3);
 assert.deepEqual(evidence.data.rank_three_verification.retained_good_original_states,[73,292,438,502,511]);
 assert.equal(evidence.data.rank_three_root_audit.valid,true);
 assert.equal(evidence.data.rank_three_quantum.physical_quantum_executed,false);
 assert.equal(evidence.data.rank_three_quantum.aggregate[0].uniform_ideal_deadline_probability,5/8);
});
test('later tool policy cohort stays paired, selection-labeled and separate from TRAIN',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 const groups=summarizeTooling(evidence.data.tooling_validation);
 assert.ok(groups.every(group=>group.valid));
 const load12=groups.find(group=>group.orders===12),[before,after]=load12.variants;
 assert.deepEqual([before.shipped,after.shipped,after.orders],[191,208,210]);
 assert.deepEqual([before.complete,after.complete,after.runs],[8,14,16]);
 assert.deepEqual([before.relocations,after.relocations],[1114,96]);
 assert.deepEqual(after.seeds,Array.from({length:16},(_,i)=>100+i));
 assert.ok(evidence.data.tooling_selection.selected.every(row=>row.selection_role.startsWith('VALIDATION selection')));
 const corrupted=structuredClone(evidence.data.tooling_validation);corrupted.groups[1].rows[0].valid=false;
 assert.equal(summarizeTooling(corrupted)[1].valid,false,'invalid rows must suppress the group, never be dropped');
 const unmatched=structuredClone(evidence.data.tooling_validation);unmatched.groups[1].rows[0].seed=999;
 assert.equal(summarizeTooling(unmatched)[1].valid,false,'different tapes cannot become a paired comparison');
});
test('larger tiny references preserve negative searches and unresolved optimum intervals',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 const rows=evidence.data.multi_reference.rows;
 const n2=rows.find(row=>row.pumps===2&&row.attendance==='automatic');
 assert.equal(n2.optimum_proven,true);assert.equal(n2.best_checked_upper_bound_ticks,863);assert.equal(n2.best_certified_lower_bound_ticks,863);
 const n3=rows.find(row=>row.pumps===3&&row.attendance==='full');
 assert.equal(n3.optimum_proven,false);assert.equal(n3.best_checked_upper_bound_ticks,2984);assert.equal(n3.best_certified_lower_bound_ticks,2953);
 assert.equal(n3.cp_runs.find(run=>run.budget_seconds===600).incumbent_ticks,3066);
 const n4=rows.find(row=>row.pumps===4&&row.attendance==='automatic');
 assert.equal(n4.constructive_upper_bound_ticks,1732);assert.equal(n4.optimum_proven,false);
 assert.equal(n4.best_certified_lower_bound_ticks,1524);assert.equal(n4.best_reported_cp_lower_bound_ticks,1524);
 assert.equal(n4.best_checked_upper_bound_ticks,1541);
 const n4Long=n4.cp_runs.find(run=>run.budget_seconds===3600);
 assert.equal(n4Long.status,'FEASIBLE');assert.equal(n4Long.incumbent_ticks,1732);assert.equal(n4Long.cp_lower_bound_ticks,1400);
 const parallel=n4.cp_runs.find(run=>run.workers===16);
 assert.equal(parallel.status,'FEASIBLE');assert.equal(parallel.incumbent_ticks,1567);assert.equal(parallel.cp_lower_bound_ticks,1466);
 assert.equal(parallel.cost.scheduler_elapsed_seconds,1779);assert.ok(Math.abs(parallel.cost.allocated_cpu_hours-16*1779/3600)<1e-10);
 assert.equal(parallel.cost.gpu_hours,0);assert.equal(parallel.cp_proof_resumed,false);
 assert.equal(parallel.instance_sha256,'3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e');
 const closeout=n4.cp_runs.find(run=>run.completed_closeout);
 assert.equal(closeout.status,'FEASIBLE');assert.equal(closeout.optimal,false);
 assert.equal(closeout.incumbent_ticks,1541);assert.equal(closeout.cp_lower_bound_ticks,1524);
 assert.equal(closeout.cost.scheduler_elapsed_seconds,7174);assert.equal(closeout.cost.allocated_cpu_hours,16*7174/3600);
 assert.equal(closeout.raw_stock_identity_valid,false);assert.equal(closeout.derived_stock_identity_valid,true);
 assert.equal(closeout.cp_proof_resumed,false);assert.equal(closeout.instance_sha256,parallel.instance_sha256);
 assert.equal(n4.analytic_lower_bound_ticks,1482,'supplemental arithmetic bound remains valid but weaker than final CP bound');
 assert.ok(Math.abs(n4.heuristic_makespan_gap_interval.lower-(2482/1541-1))<1e-12);
 assert.ok(Math.abs(n4.heuristic_makespan_gap_interval.upper-(2482/1524-1))<1e-12);
 const audit=evidence.data.reference_two_hour_audit,seal=evidence.data.reference_two_hour_seal;
 assert.equal(audit.raw_stock_identity_checks.new_cp.valid,false,'literal original rejection must remain visible');
 assert.equal(audit.derived_normalized_witness.stock_identity_check.valid,true);
 assert.equal(audit.derived_normalized_witness.physical_check.valid,true);
 assert.equal(audit.derived_normalized_witness.exact_one_field_change,true);
 assert.equal(audit.derived_normalized_witness.all_physical_legs_operations_and_metrics_unchanged,true);
 assert.equal(seal.raw_stock_identity_rejection_preserved,true);
 assert.equal(seal.identical_optima_between_dispatch_domains_not_claimed,true);
 for(const [key,filename]of [['audit','reference-2h-audit.json'],['derived_witness','reference-2h-normalized-witness.json']]){
  const raw=readFileSync(new URL(`../presentation/stage2/research/${filename}`,import.meta.url));
  assert.equal(createHash('sha256').update(raw).digest('hex'),evidence.data.reference_two_hour_downloads[`${key}_sha256`]);
 }
 assert.equal(evidence.data.closeout_accounting.research_running_job_ids.length,0);
 assert.equal(evidence.data.closeout_accounting.research_finished_allocated_cpu_hours_including_failed,431.99666666666667);
 assert.equal(evidence.data.closeout_accounting.physical_qpu_calls,0);
 assert.equal(createHash('sha256').update(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url))).digest('hex'),'6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60','frozen final outcomes and earlier accounting stay byte-identical');
 assert.equal(n4.analytic_certificate.components.prefix_nonattendance,54);
 assert.equal(n4.supplemental_bound_extension.previous_lower_bound_ticks,1480);
 assert.equal(n4.supplemental_bound_extension.complete_witnesses_checked,26);
 assert.ok(n4.analytic_certificates.some(c=>c.lower_bound_ticks===1480),'the earlier arithmetic certificate remains history');
 assert.equal(n4.supplemental_bound_extension.instance_sha256,parallel.instance_sha256);
 assert.equal(evidence.data.reference_bound_extension.valid,true);
 assert.equal(n4.analytic_certificates[0].lower_bound_ticks,1468,'earlier prefix certificate remains explicit history');
 const n3Auto=rows.find(row=>row.pumps===3&&row.attendance==='automatic');
 assert.equal(n3Auto.optimum_proven,true);assert.equal(n3Auto.best_checked_upper_bound_ticks,1191);assert.equal(n3Auto.best_certified_lower_bound_ticks,1191);
 assert.ok(n4.heuristic_makespan_gap_interval.lower<=n4.heuristic_makespan_gap_interval.upper);
 assert.equal(evidence.data.multi_reference.grid_incomplete,28);
 for(const row of rows)for(const run of row.cp_runs)if(run.status!=='RUNNING'){
  assert.equal(run.valid,true);assert.equal(run.all_orders_fulfilled,true);assert.equal(run.sources_stable,true);
 }
});
test('new factory stress replay is checked and incomplete, never relabeled solved',()=>{
 const url=new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url);
 const bytes=readFileSync(url),raw=JSON.parse(bytes),trace=normalizeTrace(raw);
 const record=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.evidence.json',import.meta.url)));
 assert.equal(createHash('sha256').update(bytes).digest('hex'),record.trace_sha256);
 assert.equal(record.fresh_independent_check.valid,true);assert.equal(record.fresh_independent_check.all_orders_fulfilled,false);
 assert.equal(trace.resources.machines.length,15);assert.equal(trace.operations.length,243);assert.equal(trace.moves.length,312);
 assert.equal(raw.metrics.shipped,13);assert.equal(raw.metrics.orders,14);assert.equal(raw.metrics.all_orders_fulfilled,false);
 assert.equal(snapshot(trace,trace.horizon_ticks).events.filter(event=>event.type==='ship').length,13);
 const deadline=deadlineEvidence(trace);
 assert.equal(deadline.label,'Censored deadline debt');assert.equal(deadline.primaryMinutes,8347);
 assert.equal(deadline.deliveredOnlyMinutes,6907);assert.equal(deadline.cutoffDebtMinutes,8347);
 assert.equal(raw.metrics.total_tardiness_ticks,8347,'raw supplied value is preserved');
 const complete=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/checked-qaoa-8.json',import.meta.url))));
 assert.equal(deadlineEvidence(complete).label,'Total tardiness');assert.equal(deadlineEvidence(complete).primaryMinutes,1884);
});
test('research templates execute against retained evidence without fabricating browser QA',async()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 const originalFetch=globalThis.fetch,originalLocation=globalThis.location,originalHistory=globalThis.history;
 const host={innerHTML:'',querySelectorAll:()=>[],querySelector:selector=>selector==='.research-content'?{addEventListener(){}}:null};
 globalThis.fetch=async()=>({ok:true,json:async()=>evidence});
 globalThis.history={replaceState(){}};
 try{
  for(const [section,expected]of [['frontier','191/210'],['stress','Push the load'],['exact','Unresolved'],['quantum','QAOA'],['sources','tooling_validation'],['overview','208']]){
   globalThis.location={search:`?section=${section}`,href:`https://viewer.invalid/?section=${section}`};await mountResearch(host);
   assert.ok(!host.innerHTML.includes('Research evidence unavailable'),section);
   assert.ok(host.innerHTML.includes(expected),section);
  }
 }finally{globalThis.fetch=originalFetch;if(originalLocation===undefined)delete globalThis.location;else globalThis.location=originalLocation;if(originalHistory===undefined)delete globalThis.history;else globalThis.history=originalHistory;}
});
test('later recovery cohorts retain paired roles, misses and invalid-group suppression',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 const data=evidence.data.later_frontier;
 assert.equal(data.final_evaluation_tapes_used,0);
 assert.equal(data.recovery.completed,768);assert.equal(data.recovery.all_valid,true);
 const train=summarizeRecovery(data.recovery,'TRAIN'),validation=summarizeRecovery(data.recovery,'VALIDATION');
 assert.deepEqual(train.map(row=>row.orders),[10,11,12,13,14,16,24]);assert.ok(train.every(row=>row.valid)&&validation.every(row=>row.valid));
 const t12=train.find(row=>row.orders===12),v12=validation.find(row=>row.orders===12);
 assert.deepEqual([t12.before.complete_runs,t12.after.complete_runs,t12.after.runs],[28,31,32]);
 assert.deepEqual([t12.before.mean_unfulfilled,t12.after.mean_unfulfilled],[1.40625,.0625]);
 assert.deepEqual([v12.before.complete_runs,v12.after.complete_runs,v12.after.runs],[15,15,16]);
 assert.deepEqual([v12.before.max_unfulfilled,v12.after.max_unfulfilled],[11,2]);
 assert.deepEqual([v12.before.mean_unfulfilled,v12.after.mean_unfulfilled],[.6875,.125]);
 assert.deepEqual(v12.after.seeds,Array.from({length:16},(_,i)=>100+i));
 assert.ok(validation.find(row=>row.orders===24).after.mean_unfulfilled>0);
 for(const mutate of [campaign=>{campaign.all_valid=false;},campaign=>{campaign.groups.find(row=>row.policy_id==='VALIDATION/family-guard4-kit/recovery1').valid--;},campaign=>{campaign.groups.find(row=>row.policy_id==='VALIDATION/family-guard4-kit/recovery1').seeds[0]=999;},campaign=>{campaign.groups.push(structuredClone(campaign.groups.find(row=>row.policy_id==='VALIDATION/family-guard4-kit/recovery1'))); }]){
  const bad=structuredClone(data.recovery);mutate(bad);assert.ok(summarizeRecovery(bad).some(row=>!row.valid));
 }
});
test('extended horizon heatmap retains same-TRAIN policy selection and calendar-time scope',()=>{
 const {later_frontier:data}=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url))).data;
 const grid=summarizeHorizons(data.horizon);
 assert.equal(data.horizon.completed,576);assert.equal(grid.valid,true);assert.equal(grid.cells.length,24);
 assert.deepEqual(grid.horizons,[5760,8640,11520,14400]);assert.ok(grid.cells.every(cell=>cell.candidates.length===3));
 for(const [order,horizon,complete]of [[16,8640,8],[20,11520,8],[24,11520,8],[28,11520,8],[32,14400,7]]){
  const cell=grid.cells.find(row=>row.orders===order&&row.horizon===horizon);
  assert.equal(cell.selected.complete_runs,complete);assert.equal(cell.hours,horizon/60);
 }
 assert.equal(data.horizon_scope_audit.numerical_instance_comparisons,144);
 assert.equal(data.horizon_scope_audit.only_changed_instance_field,'horizon_ticks');
 assert.equal(data.horizon_scope_audit.initial_due_dates_unchanged,true);
 assert.equal(data.horizon_scope_audit.physical_resources_unchanged,true);
 const missing=structuredClone(data.horizon);missing.groups.pop();assert.equal(summarizeHorizons(missing).valid,false);
 const unpaired=structuredClone(data.horizon);unpaired.groups[0].seeds[0]=999;assert.equal(summarizeHorizons(unpaired).valid,false);
 const invalid=structuredClone(data.horizon);invalid.groups[0].valid--;assert.equal(summarizeHorizons(invalid).valid,false);
});
test('primary material certificate stays distinct from all-orders completion and secondary optimality',()=>{
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url))).data;
 const proof={cohort:data.primary_quality,certificate:data.primary_quality_seed6,audit:data.primary_quality_audit};
 const summary=summarizePrimary(proof);
 assert.equal(summary.valid,true);assert.equal(summary.complete,7);assert.equal(summary.attained,8);
 assert.deepEqual([summary.orders,summary.stock,summary.needed],[34,34,35]);
 assert.equal(proof.cohort.secondary_optimality_gap,null);
 assert.ok(summary.evidence.first_draw<summary.evidence.first_risk_floor);
 assert.ok(summary.evidence.repair_draw<summary.evidence.repair_risk_floor);
 assert.equal(proof.audit.independent_knapsack_exhaustive_subset_cases,60);
 for(const mutate of [p=>{p.cohort.rows[0].physical_valid=false;},p=>{p.cohort.rows[6].unfulfilled=0;},p=>{p.audit.instance_sha256='wrong';},p=>{p.audit.audited_source_sha256='wrong';},p=>{p.cohort.rows[0].seed=7;}]){
  const corrupt=structuredClone(proof);mutate(corrupt);assert.equal(summarizePrimary(corrupt).valid,false);
 }
});
test('local objective diagnostic preserves actual one-tick forks and selected-cohort limits',()=>{
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url))).data.objective_mechanism;
 assert.equal(summarizeObjective(data).valid,true);assert.match(data.selection_role,/selected TRAIN failure/);
 assert.deepEqual(data.forks.map(row=>[row.seed,row.before_shipped,row.after_shipped,row.orders]),[[0,13,13,14],[1,12,12,12],[2,10,14,14],[4,2,12,12]]);
 const [rotor,batch]=data.example.candidates;
 assert.equal(rotor.operation.machine_id,batch.operation.machine_id);assert.deepEqual(rotor.operation.worker_ids,batch.operation.worker_ids);
 assert.deepEqual(rotor.operation.unit_ids,['P07/rotor/1']);assert.equal(batch.operation.unit_ids.length,2);
 assert.deepEqual([rotor.operation.worker_intervals[0].end-rotor.operation.worker_intervals[0].start,batch.operation.worker_intervals[0].end-batch.operation.worker_intervals[0].start],[5,35]);
 assert.equal(data.targeted_summary.find(row=>row.policy_id==='exact-original').shipped,102);
 assert.equal(data.targeted_summary.find(row=>row.policy_id==='exact-no-batch').shipped,158);
 for(const mutate of [d=>{d.forks[0].prefix_equal=false;},d=>{d.forks[0].fresh_checks[0].valid=false;},d=>{d.ablation[1].capacities.other=1;},d=>{d.targeted_summary[0].invalid=1;}]){
  const corrupt=structuredClone(data);mutate(corrupt);assert.equal(summarizeObjective(corrupt).valid,false);
 }
});
test('optional large replay loads compressed actual activities only on explicit selection',async()=>{
 const raw=readFileSync(new URL('../presentation/stage2/traces/large-train0-32-240h.json.gz',import.meta.url));
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/large-train0-32-240h.evidence.json',import.meta.url)));
 assert.equal(createHash('sha256').update(raw).digest('hex'),evidence.trace_sha256);
 assert.equal(raw.length,194373);assert.equal(evidence.activity_data_changed,false);
 const original=await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
 const requests=[],fetcher=async url=>{requests.push(String(url));return String(url).endsWith('.gz')?new Response(raw):Response.json(evidence);};
 const loaded=await fetchLinkedTrace('./traces/large-train0-32-240h.json.gz','http://viewer.local/stage2/',fetcher);
 assert.equal(requests.length,2);assert.equal(loaded.validation.status,'passed');assert.equal(loaded.validation.valid,true);
 assert.deepEqual(loaded.operations,original.operations);assert.deepEqual(loaded.moves,original.moves);assert.deepEqual(loaded.events,original.events);assert.deepEqual(loaded.metrics,original.metrics);
 const trace=normalizeTrace(loaded),terminal=snapshot(trace,14400);
 assert.equal(trace.horizon_ticks,14400);assert.equal(trace.tick_minutes,1);
 assert.equal(trace.operations.length,617);assert.equal(trace.moves.length,751);assert.equal(terminal.completed.length,617);
 assert.equal(terminal.events.filter(row=>row.type==='ship').length,34);
 assert.equal(trace.metrics.shipped,34);assert.equal(trace.metrics.orders,34);assert.equal(trace.metrics.total_tardiness_ticks,130661);
 assert.ok(trace.operations.some(row=>row.start>5760));assert.ok(trace.moves.some(row=>row.start>5760));
 const parents=unitGenealogy(trace,'P01/pump/1').parents;
 assert.equal(parents.length,3);assert.ok(parents.every(uid=>uid.startsWith('P01/')));
 assert.match(trace.provenance.viewer_replay.label,/TRAIN 0.*240h/);
 assert.equal(trace.provenance.viewer_replay.secondary_optimality_gap,null);
 requests.length=0;
 await fetchLinkedTrace('./traces/default.json','http://viewer.local/stage2/',async url=>{requests.push(String(url));return Response.json(original);});
 assert.equal(requests.length,1,'normal default must not fetch gzip or its optional sidecar');
 await assert.rejects(()=>fetchLinkedTrace('https://other.invalid/run.json.gz','http://viewer.local/stage2/',fetcher),/origin/);
 const wrong=structuredClone(evidence);wrong.trace_sha256='bad';
 await assert.rejects(()=>fetchLinkedTrace('./traces/x.json.gz','http://viewer.local/stage2/',async url=>String(url).endsWith('.gz')?new Response(raw):Response.json(wrong)),/digest/);
 const unchecked=structuredClone(evidence);unchecked.fresh_independent_check.valid=false;
 await assert.rejects(()=>fetchLinkedTrace('./traces/x.json.gz','http://viewer.local/stage2/',async url=>String(url).endsWith('.gz')?new Response(raw):Response.json(unchecked)),/passed physical/);
 await assert.rejects(()=>fetchLinkedTrace('./traces/x.json.gz','http://viewer.local/stage2/',async url=>String(url).endsWith('.gz')?new Response(raw):new Response(null,{status:404})),/sidecar is missing/);
});
test('full TRAIN confirmation aggregates every actor within32 physical tapes and keeps negative loads',()=>{
 const data=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url))).data.reward_confirmation;
 const summary=summarizeConfirmation(data);
 assert.equal(summary.valid,true);assert.equal(data.runs,2240);assert.equal(summary.groups.length,70);assert.equal(data.final_tapes_used,0);
 assert.match(data.seed_role,/not held-out/);assert.deepEqual(summary.loads,[12,13,14,16,24]);
 const get=(orders,policy)=>summary.groups.find(row=>row.orders===orders&&row.policy_id===policy);
 assert.deepEqual([get(12,'exact-original').shipped,get(12,'exact-original').complete],[326,6]);
 assert.deepEqual([get(12,'exact-no-batch').shipped,get(12,'exact-no-batch').complete],[422,31]);
 assert.deepEqual([get(16,'exact-original').shipped,get(16,'exact-no-batch').shipped],[446,440]);
 assert.ok(summary.actors.filter(row=>row.orders===24).every(row=>row.completeFraction===0));
 for(const row of summary.actors){
  const independent=data.actor_aggregates.find(other=>other.orders===row.orders&&other.method===row.method&&other.reward_mode===row.reward_mode);
  assert.deepEqual(row.actors,[7,13,29]);assert.equal(row.environments,32);
  assert.ok(Math.abs(row.meanMissing-independent.mean_missing)<1e-10);
  assert.ok(Math.abs(row.completeFraction-independent.complete_fraction)<1e-10);
  assert.ok(Math.abs(row.meanDebt-independent.mean_cutoff_debt)<1e-8);
 }
 const q=summary.actors.find(row=>row.orders===12&&row.method==='qaoa'&&row.reward_mode==='no-batch');
 assert.ok(Math.abs(q.meanMissing-7/96)<1e-10);assert.ok(Math.abs(q.completeFraction-90/96)<1e-10);
 assert.deepEqual(q.actorTotals.map(row=>[row.actor,row.shipped,row.complete]),[[7,421,30],[13,421,29],[29,423,31]]);
 const equal=summary.actors.filter(row=>row.orders===12&&row.reward_mode==='priority-lex');
 assert.equal(equal.length,3);assert.ok(equal.every(row=>row.meanMissing===.0625&&row.completeFraction===31/32));
 assert.equal(data.n12_priority_lex_actor_metrics_equal_exact,true);
 for(const mutate of [d=>{d.groups.pop();},d=>{d.groups[0].tapes[0].valid=false;},d=>{d.groups[0].tapes[0].seed=10000;},d=>{d.groups.find(row=>row.actor===7).actor=29;},d=>{d.groups[0].tapes[0].decode_mismatches=1;}]){
  const corrupt=structuredClone(data);mutate(corrupt);assert.equal(summarizeConfirmation(corrupt).valid,false);
 }
});
test('recovery examples retain selected-failure bias and actual matched physical moves',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url)));
 const diagnostic=evidence.data.recovery_diagnostic;
 assert.match(diagnostic.selection_role,/deliberately selected failed TRAIN/);
 assert.equal(diagnostic.validation_tapes,0);assert.equal(diagnostic.final_tapes,0);
 assert.deepEqual(diagnostic.pairs.map(row=>[row.seed,row.before.metrics.shipped,row.after.metrics.shipped,row.after.metrics.orders]),[[8,2,12,12],[15,1,12,14],[24,2,14,14],[26,2,12,12]]);
 for(const row of diagnostic.pairs){assert.equal(row.before.fresh_check.valid,true);assert.equal(row.after.fresh_check.valid,true);}
 const sample=diagnostic.pairs[0];
 const after=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/recovery-train8-after.json',import.meta.url)));
 const before=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/recovery-train8-before.json',import.meta.url)));
 assert.deepEqual(after.instance,before.instance);
 assert.equal(after.validation.status,'passed');assert.equal(before.validation.status,'passed');
 for(const replay of sample.viewer_replays){
  const raw=readFileSync(new URL(`../${replay.path}`,import.meta.url));assert.equal(createHash('sha256').update(raw).digest('hex'),replay.sha256);
  assert.equal(replay.validation_annotation_only,true);
 }
 const originalAfter=JSON.parse(readFileSync(new URL(`../${sample.after.trace_path}`,import.meta.url)));
 assert.deepEqual(after.operations,originalAfter.operations);assert.deepEqual(after.moves,originalAfter.moves);assert.deepEqual(after.metrics,originalAfter.metrics);
 const steps=sample.actual_recovery_steps;
 assert.equal(steps.filter(step=>step.kind==='transport').length,4);
 assert.equal(steps.filter(step=>step.kind==='retarget').length,1);
 for(const step of steps.filter(step=>step.kind==='transport')){
  const move=after.moves.find(row=>row.id===step.move_id);
  assert.equal(move.unit_id,step.unit_id);assert.equal(move.from,step.origin);assert.equal(move.to,step.destination);assert.equal(move.drop_tick,step.drop_tick);
 }
 const assembly=steps.find(step=>step.kind==='assembly_start');
 assert.equal(assembly.order_id,'P04');assert.equal(assembly.tick,2340);assert.ok(assembly.end_tick>assembly.tick);
 assert.equal(assembly.parent_unit_ids.length,3);assert.ok(assembly.parent_unit_ids.every(uid=>uid.startsWith('P04/')));
 assert.equal(steps.find(step=>step.kind==='retarget').counts_as_assembled,false);
});
