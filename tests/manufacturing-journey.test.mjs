import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pumpJourney,nextPlanEvent,stateAt} from '../presentation/manufacturing/model.js';
import {elapsed} from '../presentation/manufacturing/story.js';
const data=JSON.parse(readFileSync(new URL('../presentation/manufacturing/data.json',import.meta.url)));
const c=data.cases['heat-lease-32'],s=c.plans.find(p=>p.id==='raw_reference');

test('an on-time plan does not imply a finished pump during replay',()=>{
 assert.equal(s.check.weighted_terminal_tardiness,0);
 for(const order of ['P01','P02']){
  const start=pumpJourney(c,s,order,0),end=pumpJourney(c,s,order,s.check.makespan);
  assert.equal(start.completed,0);assert.equal(start.total,16);
  assert.notEqual(start.phase,'Inspection complete');
  assert.equal(end.completed,16);assert.equal(end.phase,'Inspection complete');
  assert.ok(end.components.every(p=>p.complete));
  const inspection=s.plan.find(r=>r.operation===order+'/pump/step1');
  assert.equal(pumpJourney(c,s,order,inspection.end-0.1).inspection.status,'active');
  assert.equal(pumpJourney(c,s,order,inspection.end).inspection.status,'complete');
 }
});

test('journey steps use processing boundaries while workers use attendance boundaries',()=>{
 const row=s.plan.find(r=>r.machine==='H3');
 const before=pumpJourney(c,s,row.operation.split('/')[0],row.start-0.1);
 const after=pumpJourney(c,s,row.operation.split('/')[0],row.attended_end);
 assert.equal(before.components.find(p=>p.name==='housing').next.operation,row.operation);
 assert.equal(before.components.find(p=>p.name==='housing').next.status,'planned');
 assert.equal(after.components.find(p=>p.name==='housing').active.operation,row.operation);
 assert.ok(stateAt(c,s,row.attended_end).active.includes(row));
 assert.ok(!stateAt(c,s,row.attended_end).attending.includes(row));
 assert.equal(nextPlanEvent(c,s,row.start),row.attended_end);
 assert.equal(nextPlanEvent(c,s,c.problem.horizon),null);
 assert.equal(elapsed(59.99),'0h 59m');
 assert.equal(elapsed(60),'1h 00m');
});
