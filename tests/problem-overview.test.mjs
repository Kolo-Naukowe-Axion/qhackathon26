import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {INSTANCES,permutations,earliestSchedule} from '../presentation/problems/schedule-model.js';

test('teaching schedule uses the official instances and respects both job and machine precedence',()=>{
 for(const [key,size,optimum]of [['A','2x2',4],['B','3x3',8]]){
  const official=JSON.parse(readFileSync(new URL(`../instances/instance_${size}.json`,import.meta.url)));
  const instance=INSTANCES[key];assert.deepEqual(instance.jobs.map(job=>job.durations),official.jobs.map(job=>job.operations.map(op=>op.duration)));
  const schedules=permutations(instance.jobs.map(job=>job.id)).map(order=>earliestSchedule(instance,order));
  assert.equal(Math.min(...schedules.map(row=>row.makespan)),optimum);
  for(const schedule of schedules){
   assert.equal(schedule.operations.length,instance.jobs.length*instance.machines.length);
   for(const op of schedule.operations){
    assert.ok(op.start>=0&&op.end-op.start===op.duration);
    const previous=schedule.operations.find(row=>row.job===op.job&&row.machine===op.machine-1);
    if(previous)assert.ok(op.start>=previous.end);
    for(const other of schedule.operations.filter(row=>row!==op&&row.machine===op.machine))assert.ok(op.end<=other.start||other.end<=op.start);
   }
  }
 }
});
