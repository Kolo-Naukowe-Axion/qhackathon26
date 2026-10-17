import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {storySteps,selectedStory,elapsed} from '../presentation/manufacturing/story.js';
import {attachMeritPlans} from '../presentation/manufacturing/merit-model.js';
import {checkedCase,commitments} from '../presentation/manufacturing/model.js';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(readFileSync(new URL(p,root)));
const data=read('presentation/manufacturing/data.json');
attachMeritPlans(data.cases,read('presentation/manufacturing/merit-data.json'));
test('recovery story selects the measured complete and restricted schedules without altering their facts',()=>{
 const outcomes=storySteps.map(step=>{
  const c=data.cases[step.case];checkedCase(c);
  const plan=c.plans.find(p=>p.id===step.method);assert.ok(plan,step.id);
  assert.equal(c.operations,32);assert.equal(plan.plan.length,32);
  assert.ok(commitments(c,plan).every(r=>r.due===900));
  return [plan.check.weighted_terminal_tardiness,plan.check.makespan];
 });
 assert.deepEqual(outcomes,[[45,945],[0,855],[45,945],[0,855]]);
 assert.equal(selectedStory('heat-lease-32','recipe_qaoa'),null);
 assert.equal(elapsed(855),'14h 15m');
 assert.equal(elapsed(945),'15h 45m');
});
