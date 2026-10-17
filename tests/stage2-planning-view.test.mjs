import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validatePlanning,representation,resourceLanes,gantt,bom,inspector} from '../presentation/stage2/planning.js';
import {summarizeMixer,mixerView} from '../presentation/stage2/planning-mixer.js';
const base=new URL('../',import.meta.url);
const raw=readFileSync(new URL('../presentation/stage2/planning-data/evidence.json',import.meta.url));
const data=JSON.parse(raw);

test('planning export pins retained development sources and never changes frozen final metrics',()=>{
 assert.equal(validatePlanning(data),data);
 for(const [path,hash]of Object.entries(data.source_sha256))assert.equal(createHash('sha256').update(readFileSync(new URL(path,base))).digest('hex'),hash,path);
 assert.equal(data.factory_runs,0);assert.equal(data.solver_runs,0);assert.equal(data.physical_qpu_calls,0);
 assert.equal(createHash('sha256').update(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url))).digest('hex'),'6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60');
});
test('raw, support-pruned, conditional and restricted counts remain different scopes',()=>{
 const c=data.cases[0];assert.ok(c.raw.total_bits>c.support_pruned.total_bits);
 assert.equal(c.support_pruned.total_bits,1189);assert.equal(c.trajectory.variables,5);
 assert.equal(representation(c,'pruned').loss,0);
 assert.equal(representation(c,'trajectory').loss,173040);
 assert.equal(c.native_cp.optimal,true);assert.equal(c.trajectory.restricted_exact_objective,2119575);
 const corrupt=structuredClone(data);corrupt.cases[0].trajectory.gap_to_cp_incumbent=0;
 assert.throws(()=>validatePlanning(corrupt),/Restriction gap/);
 const wrong=structuredClone(data);wrong.cases[0].support_pruned.objective_used=true;
 assert.throws(()=>validatePlanning(wrong),/pruning scope/);
 const four=data.cases[3];assert.equal(four.problem.operations.length,64);
 assert.equal(four.initializer_valid,false);assert.equal(four.trajectory,null);
 assert.match(four.trajectory_error,/No two distinct/);assert.equal(representation(four,'trajectory'),null);
});
test('every saved schedule contains full matched recipes and assembly joins',()=>{
 assert.equal(data.cases.reduce((s,c)=>s+c.plans.length,0),97);
 for(const c of data.cases){
  for(const s of c.plans){assert.equal(s.check.valid,true);assert.equal(s.plan.length,c.pumps*16);}
  for(let i=1;i<=c.pumps;i++){
   const id=`P${String(i).padStart(2,'0')}`;
   const join=c.problem.operations.find(o=>o.id===`${id}/pump/step0`);
   assert.equal(join.predecessors.length,3);assert.ok(join.predecessors.every(p=>p.startsWith(id+'/')));
  }
 }
});
test('worker Gantt uses attendance instead of falsely reserving automatic processing',()=>{
 const c=data.cases[0],s=c.plans[0];
 const automatic=s.plan.find(r=>r.attended_end<r.end);assert.ok(automatic);
 const workers=resourceLanes(c,s,'worker');const bar=workers.flatMap(r=>r.bars).find(r=>r.operation===automatic.operation);
 assert.equal(bar.display_end,automatic.attended_end);assert.notEqual(bar.display_end,automatic.end);
 const machine=resourceLanes(c,s,'machine').flatMap(r=>r.bars).find(r=>r.operation===automatic.operation);
 assert.equal(machine.display_end,automatic.end);
 assert.match(gantt(c,s,'worker',automatic.operation,'P01',0),/Saved worker schedule, 32 operations/);
 assert.equal((bom(c,s,'P01','P01/pump/step0').match(/data-operation=/g)||[]).length,16);
 assert.match(inspector(c,s,automatic.operation),/Worker attends/);
});
test('independent local QASM evidence and adverse factory integration stay retained',()=>{
 assert.equal(data.circuit_audit.circuits,48);assert.ok(data.circuit_audit.max_probability_error<1e-15);
 for(const row of data.circuit_audit.rows){assert.equal(row.valid,true);assert.equal(createHash('sha256').update(readFileSync(new URL(`../presentation/stage2/planning-data/${row.qasm_file}`,import.meta.url))).digest('hex'),row.qasm_sha256);}
 for(const seed of [0,1]){
  const baseline=data.integration.rows.find(r=>r.seed===seed&&r.method==='baseline');
  const qaoa=data.integration.rows.find(r=>r.seed===seed&&r.method==='compressed_qaoa');
  assert.ok(qaoa.shipped<baseline.shipped);assert.equal(qaoa.valid,true);
 }
 const setup=data.setup_costs.rows;assert.equal(setup.length,6);
 for(const grid of [60,30,15]){const pair=setup.filter(r=>r.case.grid===grid);assert.equal(pair[0].variables,pair[1].variables);assert.ok(pair[1].couplers>pair[0].couplers);}
 assert.ok(setup.every(r=>r.cp_status==='OPTIMAL'));
});
test('finer grid rows remain native CP references without invented large QUBOs',()=>{
 const rows=data.fine_grid.rows;assert.equal(rows.length,2);
 const minute=rows.find(r=>r.case.grid===1),five=rows.find(r=>r.case.grid===5);
 assert.equal(minute.cp.objective,787555);assert.equal(five.cp.objective,793320);
 assert.equal(minute.unary_assignment_bits_before_support,115878);
 assert.equal(five.unary_assignment_bits_before_support,23878);
 assert.ok(rows.every(r=>!r.qubo_built&&r.cp.optimal&&r.case.metric_setups));
 assert.ok(data.setup_costs.rows.find(r=>r.case.grid===15&&r.case.metric_setups).cp_objective/minute.cp.objective-1>.15);
});
test('fresh validation retains all16 paired seeds and rejects unsupported promotion',()=>{
 const v=data.soft_validation;assert.equal(v.rows.length,48);
 assert.deepEqual(v.protocol.seeds,Array.from({length:16},(_,i)=>50000000+i));
 const baseline=v.groups.find(g=>g.method==='baseline'),q=v.groups.find(g=>g.method==='compressed_qaoa');
 assert.equal(baseline.mean_missing,1.4375);assert.equal(q.mean_missing,2.125);
 assert.equal(baseline.mean_cutoff_debt,7576.9375);assert.equal(q.mean_cutoff_debt,8650.9375);
 for(const seed of v.protocol.seeds){const rows=v.rows.filter(r=>r.seed===seed);assert.equal(new Set(rows.map(r=>r.instance_sha256)).size,1);
  const a=rows.find(r=>r.method==='constructive'),b=rows.find(r=>r.method==='compressed_qaoa');
  for(const key of ['orders','shipped','cutoff_deadline_debt'])assert.equal(a[key],b[key]);
 }
});
test('mixer comparison keeps strong onehot control, all actors and adverse resource tradeoffs',()=>{
 const s=summarizeMixer(data,'case2',2);assert.equal(s.rows.length,12);
 const xy=s.rows.filter(r=>r.label==='qaoa_xy'),x=s.rows.filter(r=>r.label==='qaoa_x'),control=s.rows.filter(r=>r.label==='uniform_onehot');
 assert.equal(xy.filter(r=>r.pool_optimum_sampled).length,3);assert.equal(x.filter(r=>r.pool_optimum_sampled).length,1);
 assert.ok(control.every(r=>r.exact_hit_probability===.025));
 assert.ok(xy.every(r=>r.circuit.compiled_gates.cx===48));assert.ok(x.every(r=>r.circuit.compiled_gates.cx===64));
 assert.ok(xy.every(r=>r.circuit.compiled_depth>x[0].circuit.compiled_depth));
 assert.ok(xy.every(r=>r.makespan_invariant_leakage<1e-14));
 assert.match(mixerView(data,'case2',2),/resource-conflict penalties/);assert.match(mixerView(data,'case2',2),/not 64 physical shots/);
 assert.equal(summarizeMixer(data,'case3'),null);
 const wrong=structuredClone(data);wrong.mixer.cases[2].results=wrong.mixer.cases[2].results.filter(r=>r.seed!==29);
 assert.throws(()=>summarizeMixer(wrong,'case2',2),/Missing mixer actor/);
 const mismatch=structuredClone(data);mismatch.mixer.cases[2].master.pool_sha256='wrong';
 assert.throws(()=>summarizeMixer(mismatch,'case2',2),/pool mismatch/);
});
test('all36 mixer circuits pin actual QASM and independent logical transpilation checks',()=>{
 const audit=data.mixer.audit;assert.equal(audit.circuits,36);assert.equal(audit.valid,true);
 assert.ok(audit.max_probability_error<2.84e-15);assert.ok(audit.max_transpilation_error<2.84e-15);
 for(const row of audit.rows){assert.equal(row.valid,true);assert.equal(createHash('sha256').update(readFileSync(new URL(`../presentation/stage2/planning-data/${row.qasm_file}`,import.meta.url))).digest('hex'),row.qasm_sha256);}
 assert.match(audit.connectivity,/logical all-to-all/);assert.equal(data.mixer.protocol.shots,32);
});
