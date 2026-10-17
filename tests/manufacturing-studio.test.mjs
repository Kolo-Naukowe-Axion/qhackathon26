import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {checkedCase,commitments,stateAt,lower} from '../presentation/manufacturing/model.js';
const root=new URL('../',import.meta.url);
const data=JSON.parse(readFileSync(new URL('presentation/manufacturing/data.json',root)));
test('manufacturing display anchors sources and every complete recipe',()=>{
 assert.equal(Object.keys(data.cases).length,9);
 for(const [p,h]of Object.entries(data.source_sha256))assert.equal(createHash('sha256').update(readFileSync(new URL(p,root))).digest('hex'),h,p);
 for(const c of Object.values(data.cases)){
  assert.equal(checkedCase(c),c);
  for(const s of c.plans){
   assert.equal(commitments(c,s).length,c.pumps);
   assert.ok(lower(c)<=s.check.objective);
   for(let i=1;i<=c.pumps;i++){
    const prefix=`P${String(i).padStart(2,'0')}/`;
    const ops=c.problem.operations.filter(o=>o.id.startsWith(prefix));assert.equal(ops.length,16);
    assert.equal(ops.find(o=>o.id===prefix+'pump/step0').predecessors.length,3);
   }
   const r=s.plan[0];assert.ok(stateAt(c,s,r.start).active.includes(r));assert.ok(!stateAt(c,s,r.end).active.includes(r));
  }
 }
 const bad=structuredClone(data.cases['nominal-32']);bad.plans[0].plan.pop();assert.throws(()=>checkedCase(bad),/coverage/);
});
test('original measured pair loses capacity value in its original restricted pool',()=>{
 const a=data.cases['heat-outage-32'],b=data.cases['heat-lease-32'];
 assert.equal(a.reference.optimal,true);assert.equal(b.reference.optimal,true);
 assert.equal(a.reference.objective,65790);assert.equal(b.reference.objective,855);
 assert.equal(a.pool_reference.objective,65790);assert.equal(b.pool_reference.objective,65790);
 assert.equal(b.full_domain.variables,2499);assert.equal(b.full_domain.couplers,381371);
 const plan=b.plans.find(p=>p.id==='raw_reference');assert.equal(commitments(b,plan).reduce((n,o)=>n+o.tardy,0),0);
 const h3=plan.plan.filter(r=>r.machine==='H3');assert.ok(h3.length>0);assert.ok(h3.every(r=>r.start>=360));
});
test('unresolved large complete models and failed controls stay explicit',()=>{
 for(const id of ['nominal-64','nominal-128']){const c=data.cases[id];assert.equal(c.reference.status,'UNKNOWN');assert.equal(c.reference.optimal,false);assert.ok(lower(c)<Math.min(...c.plans.map(s=>s.check.objective)));}
 const rows=data.annealing_pilot.rows;assert.equal(rows.length,60);assert.ok(rows.every(r=>r.retained_policy_objective===r.witness_objective));
 assert.equal(rows.filter(r=>r.penalty==='original_bound').reduce((n,r)=>n+r.feasible_samples,0),21);
 assert.equal(rows.filter(r=>r.penalty==='checked_incumbent_bound').reduce((n,r)=>n+r.feasible_samples,0),1);
 assert.equal(data.veloxq_calls,0);assert.equal(data.packets.veloxq_calls,0);assert.equal(data.packets.rows.length,6);
 assert.ok(data.packets.rows.every(r=>r.files.every(f=>f.audit.coefficient_equality_all_states)));
});
