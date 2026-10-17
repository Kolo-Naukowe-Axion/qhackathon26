import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {activateRun,deliveredMeals,selectedPrograms} from '../presentation/catering/model.js';
import {decodedActions,withAlternative,kitchenVisualState} from '../presentation/catering/kitchen-state.js';
import {decisionComparison,decisionSteps} from '../presentation/catering/decision-story.js';
const {cases}=JSON.parse(await readFile(new URL('../presentation/catering/replay-data.json',import.meta.url)));
test('each selected program translates its own recorded phase times, including multiple batches',()=>{
  const c=activateRun(cases[0]);assert.equal(selectedPrograms(c).length,2);
  for(const p of selectedPrograms(c)){
    const actions=decodedActions(c,c.options.indexOf(p));
    assert.deepEqual(actions.map(a=>a.kind),['prepare','cook','pack','clean']);
    for(const a of actions){const recorded=c.plan.operations.filter(o=>o.batch_id===p.id&&o.kind===a.kind);assert.equal(a.start,recorded[0].start);assert.equal(a.end,Math.max(...recorded.map(o=>o.end)));}
  }
  assert.match(decisionSteps(c)[1].copy,/Main and side/);
});
test('skipping a course changes complete handovers and waste while preserving one-hot choices',()=>{
  const c=activateRun(cases[0]),before=JSON.stringify(c);
  for(const alternative of c.alternatives){
    const view=withAlternative(c,alternative.index);
    assert.equal(view.manual,true);assert.equal(view.bits[alternative.index],0);
    assert.ok(view.metrics.U>c.metrics.U);assert.ok(deliveredMeals(view,Infinity)<deliveredMeals(c,Infinity));
    for(const g of view.onehot_groups)assert.equal(g.indices.reduce((n,i)=>n+view.bits[i],0),1);
  }
  assert.equal(JSON.stringify(c),before);assert.throws(()=>withAlternative(c,10000));
});
test('repair, waiting for clean, cleaning and reuse occupy distinct half-open states',()=>{
  const c=activateRun(cases.find(c=>c.id==='S2'));
  assert.equal(kitchenVisualState(c,59.99).stations.C2.mode,'offline');
  assert.equal(kitchenVisualState(c,60).stations.C2.mode,'awaiting_clean');
  assert.equal(kitchenVisualState(c,70).stations.C2.mode,'clean');
  assert.notEqual(kitchenVisualState(c,80).stations.C2.operation?.recovery,true);
});
test('the tradeoff uses complete-meal handovers and labels the manual intervention',()=>{
  const c=activateRun(cases[0]),comparison=decisionComparison(c,c);
  assert.equal(comparison.current.served,20);assert.ok(comparison.other.served<20);
  assert.match(comparison.copy,/one course alone/);
  const other=withAlternative(c,comparison.other.index),reverse=decisionComparison(other,c);
  assert.equal(reverse.other.served,20);assert.equal(reverse.current.served,comparison.other.served);
});
test('kitchen dispatch animation follows complete meals, not two component allocations',()=>{
  const c=activateRun(cases[0]);
  assert.equal(kitchenVisualState(c,80).departing.length,1);
  assert.equal(kitchenVisualState(c,81).departing.length,0);
  const alternative=withAlternative(c,c.alternatives[0].index);
  const dropped=new Set(c.plan.meal_handovers.filter(h=>!alternative.plan.meal_handovers.some(a=>a.meal_id===h.meal_id)).map(h=>h.time));
  for(const time of dropped)assert.ok(kitchenVisualState(alternative,time).departing.length<kitchenVisualState(c,time).departing.length);
});
