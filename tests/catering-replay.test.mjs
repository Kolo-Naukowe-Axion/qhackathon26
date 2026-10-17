import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {activateRun,deliveredMeals,packedMeals,mealOrders,requestedMeals,activeOperations,workerOperation} from '../presentation/catering/model.js';
const data=JSON.parse(await readFile(new URL('../presentation/catering/replay-data.json',import.meta.url)));
const root=new URL('../',import.meta.url);
test('all V3 replay methods retain checked plans with traceable frozen sources',async()=>{
  assert.equal(data.schema,'catering-kitchen-replay.v3');
  assert.deepEqual(data.cases.map(c=>c.id),['CELL','S0','S1','S2','S3']);
  for(const fixture of data.cases)for(const run of fixture.runs){
    assert.equal(fixture.instance.profile_id,'paired-course-contiguous.v3');
    const bytes=await readFile(new URL(run.source.path,root));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),run.source.sha256);
    assert.equal(run.valid,true);
    if(run.key==='qaoa'){
      const payload=JSON.parse(bytes);
      assert.equal(payload.execution_kind,'quantum_simulator');
      assert.equal(payload.bundle_sha256,run.bundle_sha256);
      assert.ok(payload.samples.some(s=>JSON.stringify(s.bits)===JSON.stringify(run.bits)&&s.count===run.count&&s.reported_energy===run.energy));
    }
    if(run.key==='raw')assert.deepEqual(JSON.parse(bytes).plan,run.plan);
    for(const g of run.onehot_groups)assert.equal(g.indices.reduce((n,i)=>n+run.bits[i],0),1);
    const fixed=new Set(fixture.snapshot.fixed_batches.map(p=>p.id));
    if(run.bits.length)assert.deepEqual(new Set(run.plan.batches.filter(p=>!fixed.has(p.id)).map(p=>p.id)),new Set(run.options.filter((_,i)=>run.bits[i]).map(p=>p.id)));
  }
});
test('the complete-cell quantum replay is an actual optimum sample, not a reference substitution',()=>{
  const c=activateRun(data.cases[0]);assert.equal(c.bits.length,35);assert.equal(c.options.length,32);assert.equal(c.count,13);
  assert.deepEqual(c.metrics,{U:0,W:0,B:2,R:2});assert.equal(c.plan.meal_handovers.length,2);
  assert.equal(requestedMeals(c),20);assert.equal(deliveredMeals(c,79),0);assert.equal(deliveredMeals(c,80),10);assert.equal(deliveredMeals(c,100),20);
});
test('components cannot double-count complete meals; packing and departures remain distinct',()=>{
  for(const fixture of data.cases)for(const run of fixture.runs){
    const c=activateRun(fixture,run.key);
    assert.equal(deliveredMeals(c,Infinity),run.plan.meal_handovers.reduce((n,h)=>n+h.lots*c.instance.lot_size,0));
    assert.equal(requestedMeals(c)-deliveredMeals(c,Infinity),run.metrics.U*c.instance.lot_size);
    assert.equal(packedMeals(c,Infinity),deliveredMeals(c,Infinity));
    for(const m of mealOrders(c))if(m.handed)assert.ok(m.ready_at<=m.departure);
  }
});
test('mandatory recovery clean is visible as resource occupation and W2 attendance',()=>{
  for(const fixture of data.cases.filter(c=>['S2','S3'].includes(c.id)))for(const run of fixture.runs){
    const c=activateRun(fixture,run.key);
    assert.ok(activeOperations(c,70).some(o=>o.recovery&&o.resource==='C2'&&o.kind==='clean'));
    assert.equal(workerOperation(c,'W2',75).recovery,true);
    assert.ok(!activeOperations(c,80).some(o=>o.recovery));
    assert.ok(!c.plan.operations.some(o=>o.resource==='C2'&&o.kind==='cook'&&o.start<80));
  }
});
