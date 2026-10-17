import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateScaling,scalingCell,scalingView,boundInterval} from '../presentation/stage2/planning-scaling.js';
import {gantt,bom,inspector,resourceLanes} from '../presentation/stage2/planning.js';
const data=JSON.parse(readFileSync(new URL('../presentation/stage2/planning-data/scaling.json',import.meta.url)));
const root=new URL('../',import.meta.url);

test('completed scaling sources and all21 checked witness plans remain anchored',()=>{
 assert.equal(validateScaling(data),data);assert.equal(data.contexts.length,4);
 for(const [path,hash]of Object.entries(data.source_sha256))assert.equal(createHash('sha256').update(readFileSync(new URL(path,root))).digest('hex'),hash,path);
 assert.equal(data.contexts.reduce((n,c)=>n+c.plans.length,0),21);
 assert.equal(data.factory_runs,0);assert.equal(data.solver_runs,0);assert.equal(data.quantum_runs,0);
 assert.equal(createHash('sha256').update(readFileSync(new URL('../presentation/stage2/research/final-evidence.json',import.meta.url))).digest('hex'),'6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60');
});
test('latest128-op FEASIBLE interval never becomes exact and v1 history is retained',()=>{
 const c=data.contexts.find(c=>c.operations===128);
 assert.equal(c.raw_reference.status,'FEASIBLE');assert.equal(c.raw_reference.optimal,false);
 assert.equal(c.raw_reference.bound,8071630);assert.equal(c.raw_reference.objective,13941691);
 assert.equal(c.raw_reference.model_variables,46498);assert.equal(c.prior_raw_reference.model_variables,414442);
 assert.equal(c.compact_raw_reference.objective,15951151);assert.equal(c.compact_raw_reference.bound,7626567);
 assert.equal(c.plans[0].check.objective,13941691);assert.equal(c.plans.at(-1).check.objective,15951151);
 assert.equal(c.prior_raw_reference.objective,20812381);assert.equal(c.prior_raw_reference.bound,5033967);
 assert.equal(c.rigid_master.variables,250);assert.equal(c.rigid_master.column_groups,32);assert.equal(c.rigid_master.couplers,4453);
 assert.equal(c.pool_reference.objective,21525346);assert.equal(c.pool_reference.objective,c.best_parent_objective);
 assert.equal(c.operation_pool_reference.objective,19580896);assert.equal(c.operation_master.variables,6046);
 assert.ok(c.operation_pool_excess_interval[0]>0);
 assert.match(boundInterval(c),/objective lies between 8071630 and 13941691/);
 const html=scalingView(data,{context:c.id,plan:0,kind:'machine',order:'P08',operation:'P08/pump/step0',tick:0},{gantt,bom,inspector});
 assert.match(html,/Raw-cell optimum unresolved/);assert.match(html,/40.45% above the latest raw CP incumbent/);
 assert.match(html,/Relative incumbent gap.*42.1%/);assert.match(html,/own prior feasible hint/);
 assert.match(html,/not counts of feasible combined schedules/);assert.match(html,/not QUBO qubits/);
});
test('all recipe/BOM work is shown and parent/worker semantics do not leak between cells',()=>{
 for(const original of data.contexts){const c=scalingCell(original);
  for(const schedule of c.plans){assert.equal(schedule.check.valid,true);assert.equal(schedule.plan.length,c.operations);assert.equal(new Set(schedule.plan.map(r=>r.operation)).size,c.operations);}
  const s=c.plans[0];assert.equal(resourceLanes(c,s,'machine').reduce((n,r)=>n+r.bars.length,0),c.operations);
  assert.equal(resourceLanes(c,s,'worker').reduce((n,r)=>n+r.bars.length,0),c.operations);
  for(let i=1;i<=c.pumps;i++){const order=`P${String(i).padStart(2,'0')}`;const join=c.problem.operations.find(o=>o.id===order+'/pump/step0');assert.equal(join.predecessors.length,3);assert.ok(join.predecessors.every(p=>p.startsWith(order+'/')));assert.equal((bom(c,s,order,order+'/pump/step0').match(/data-operation=/g)||[]).length,16);}
 }
});
test('smaller raw optima and operation-pool loss are scoped to exact numerical cells',()=>{
 const expected=new Map([[32,908670],[48,1297680],[64,1945958]]);
 for(const c of data.contexts.filter(c=>c.operations<128)){assert.equal(c.raw_reference.optimal,true);assert.equal(c.raw_reference.objective,expected.get(c.operations));assert.equal(c.raw_reference.bound,c.raw_reference.objective);}
 const c=data.contexts.find(c=>c.operations===32);assert.equal(c.operation_pool_reference.objective,908670);
 assert.equal(c.operation_master.variables,1489);assert.equal(c.operation_master.couplers,112060);
 assert.equal(c.same_problem_time_indexed_qubo.problem_sha256,c.rigid_master.problem_sha256);
 assert.equal(c.same_problem_time_indexed_qubo.variables,5443);assert.equal(c.same_problem_time_indexed_qubo.couplers,1664149);
 const corrupt=structuredClone(data);corrupt.contexts[0].pool_reference.objective=0;
 assert.throws(()=>validateScaling(corrupt),/reference bounds/);
});
test('completed broader pools and all nine unsuccessful local controls remain explicit',()=>{
 assert.equal(data.negative_pool_probes.length,16);
 assert.equal(data.negative_pool_probes.filter(r=>r.improvement_over_parent>0).length,1);
 const b=data.operation_block_probe;assert.equal(b.runs.length,9);assert.equal(b.master.variables,6046);
 assert.deepEqual([...new Set(b.runs.map(r=>r.seed))],[7,13,29]);
 assert.ok(b.runs.every(r=>r.raw_check&&r.energy===21525346&&r.strict_improvement===0));
 assert.equal(Math.max(...b.runs.map(r=>r.qubits_max)),6);
});
