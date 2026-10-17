import test from 'node:test';
import assert from 'node:assert/strict';
import {productionFrame,inspectionFrame} from '../presentation/stage2/problem-motion.js';

test('illustration waits for every component before creating and shipping the pump',()=>{
 const waiting=productionFrame(6);
 assert.equal(waiting.waiting,true);
 assert.ok(waiting.parts[0].travel>waiting.parts[2].travel);
 assert.equal(waiting.assembled,false);
 assert.equal(waiting.shipped,false);
 const assembled=productionFrame(10);
 assert.ok(assembled.parts.every(part=>part.travel===1&&!part.visible));
 assert.equal(assembled.assembled,true);
 assert.equal(assembled.shipped,false);
 assert.equal(productionFrame(15).shipped,true);
});

test('switching inspection order changes lateness while preserving all durations and finish time',()=>{
 for(const dueFirst of [true,false]){
  const rows=inspectionFrame(dueFirst,50);
  assert.equal(rows.at(-1).end,50);
  assert.equal(rows.find(row=>row.id==='A').end-rows.find(row=>row.id==='A').start,30);
  assert.equal(rows.find(row=>row.id==='B').end-rows.find(row=>row.id==='B').start,20);
  assert.equal(rows.reduce((sum,row)=>sum+row.late,0),dueFirst?0:10);
  assert.ok(rows.every(row=>row.progress===1));
 }
 const midpoint=inspectionFrame(false,40);
 assert.equal(midpoint[0].progress,1);
 assert.equal(midpoint[1].progress,.5);
});
