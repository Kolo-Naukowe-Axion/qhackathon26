import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {activateRun,mealOrders,deliveredMeals,allOperations} from '../presentation/catering/model.js';
import {withAlternative} from '../presentation/catering/kitchen-state.js';
import {productionSequence,componentStatus,playbackEnd,adjacentEvent,eventDescription} from '../presentation/catering/production-sequence.js';
const {cases}=JSON.parse(await readFile(new URL('../presentation/catering/replay-data.json',import.meta.url)));
const cell=activateRun(cases[0]);

test('the cell makes the prep/cook inversion and actual four-step packing queue explicit',()=>{
  const sequence=productionSequence(cell);
  assert.deepEqual(sequence.cooking.map(r=>[r.batch.menu,r.cook.start,r.cook.end,r.cook.resource]),[
    ['A',10,60,'C1'],['C',50,70,'C2'],['B',70,90,'C1']]);
  assert.equal(sequence.inversion.preparedFirst.batch.menu,'B');
  assert.equal(sequence.inversion.cookedFirst.batch.menu,'C');
  assert.deepEqual(sequence.packing.map(r=>[r.label,r.order,r.operation.start,r.operation.end]),[
    ['Main A','Order A',60,70],['Side C','Order A',70,80],['Side C','Order B',80,90],['Main B','Order B',90,100]]);
});
test('course statuses distinguish waiting after prep, packing separate portions and actual service',()=>{
  const [a,b]=mealOrders(cell);
  assert.equal(componentStatus(cell,b,'main',35).status,'Prepared · cook 11:40');
  assert.equal(componentStatus(cell,b,'main',70).status,'Cooking');
  assert.equal(componentStatus(cell,a,'side',75).status,'Packing');
  assert.equal(componentStatus(cell,b,'side',75).status,'Cooked · pack 11:50');
  assert.equal(componentStatus(cell,a,'side',80).status,'Served');
  assert.equal(componentStatus(cell,b,'side',90).status,'Packed · waiting for departure');
  assert.equal(componentStatus(cell,b,'main',100).status,'Served');
});
test('queues are projections of each actual plan and never invent missing courses',()=>{
  for(const c of cases.flatMap(f=>f.runs.map(r=>activateRun(f,r.key)))){
    const before=JSON.stringify(c),sequence=productionSequence(c);
    assert.deepEqual(new Set(sequence.cooking.map(r=>r.cook.id)),new Set(c.plan.operations.filter(o=>o.kind==='cook').map(o=>o.id)));
    assert.deepEqual(new Set(sequence.packing.map(r=>r.operation.id)),new Set(c.plan.operations.filter(o=>o.kind==='pack').map(o=>o.id)));
    assert.ok(sequence.packing.every(r=>r.meal&&r.meal.allocations.some(a=>a?.packing_operation===r.operation.id)));
    assert.ok(allOperations(c).every(o=>o.end<=sequence.end));
    assert.equal(deliveredMeals(c,playbackEnd(c)),deliveredMeals(c,Infinity));
    assert.equal(JSON.stringify(c),before);
  }
  const skipped=withAlternative(cell,cell.alternatives.find(a=>cell.options[a.index].menu==='C').index);
  assert.equal(productionSequence(skipped).cooking.length,2);
  const a=mealOrders(skipped)[0];
  assert.equal(componentStatus(skipped,a,'side',80).status,'Not scheduled');
  assert.equal(componentStatus(skipped,a,'main',80).status,'Discarded · no complete meal');
});
test('event stepping includes attendance-independent operation boundaries, departures and recovery clean',()=>{
  const sequence=productionSequence(cell);
  assert.equal(sequence.end,100);assert.equal(cell.instance.horizon_minutes,160);
  assert.equal(adjacentEvent(sequence,20,1),30);assert.equal(adjacentEvent(sequence,30,1),40);
  assert.equal(adjacentEvent(sequence,40,-1),30);assert.equal(adjacentEvent(sequence,100,1),100);
  assert.match(eventDescription(cell,80),/Order A departs/);
  const disrupted=activateRun(cases.find(c=>c.id==='S2'));
  assert.ok(productionSequence(disrupted).eventTimes.includes(70));
  assert.match(eventDescription(disrupted,70),/Recovery clean/);
});
