import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalizeTrace,snapshot,blueprint,fixture} from '../presentation/stage2/model.js';
import {orderIds,orderJourney,nextActivityTick} from '../presentation/stage2/factory-story.js';
const run=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url))));

test('one-pump tracker follows actual parent components and their recipe intervals',()=>{
 const order=orderIds(run)[0],start=orderJourney(run,order,0,snapshot(run,0).location);
 assert.equal(start.components.length,3);assert.deepEqual(start.components.map(row=>row.id),start.assembly.parent_unit_ids);
 assert.ok(start.components.every(row=>row.finished===0&&!row.consumed));
 const tick=start.assembly.start,building=orderJourney(run,order,tick,snapshot(run,tick).location);
 assert.equal(building.phase,'assembly');
 assert.ok(building.components.every(row=>row.consumed&&row.finished===row.steps.length));
 assert.deepEqual([...building.relatedMachines],[building.assembly.machine_id]);
});

test('one-pump shipment is not inferred from assembly or final inspection',()=>{
 const order=orderIds(run)[0],base=orderJourney(run,order,0),shipment=run.events.find(event=>event.type==='ship'&&event.unit_id===base.pump);
 for(const time of [base.assembly.end,base.inspection.end,shipment.tick-.01])assert.equal(orderJourney(run,order,time).shipped,null);
 assert.equal(orderJourney(run,order,base.assembly.end).phase,'awaiting-inspection');
 assert.equal(orderJourney(run,order,base.inspection.start).phase,'inspection');
 assert.equal(orderJourney(run,order,base.inspection.end).phase,'delivery');
 assert.equal(orderJourney(run,order,shipment.tick).phase,'shipped');
});

test('incomplete order never acquires a shipment in the presentation tracker',()=>{
 const unfinished=orderIds(run).find(order=>!orderJourney(run,order,run.horizon_ticks).shipped);
 assert.ok(unfinished);assert.notEqual(orderJourney(run,unfinished,run.horizon_ticks).phase,'shipped');
 assert.equal(run.events.filter(event=>event.type==='ship').length,13);
});

test('activity jump uses a future recorded boundary, with a bounded terminal fallback',()=>{
 assert.equal(nextActivityTick(run,0),Math.min(...[...run.operations.map(row=>row.start),...run.moves.map(row=>row.start)].filter(time=>time>.05)));
 const nearEnd=Math.max(...run.operations.map(row=>row.end),...run.moves.map(row=>row.end));
 assert.ok(nextActivityTick(run,nearEnd)<=run.horizon_ticks);
 assert.equal(nextActivityTick(run,run.horizon_ticks),run.horizon_ticks);
});

test('blueprint does not invent orders or assembly progress',()=>{
 const trace=blueprint();assert.deepEqual(orderIds(trace),[]);const journey=orderJourney(trace,'unknown',0);
 assert.deepEqual(journey.components,[]);assert.equal(journey.assembly,undefined);assert.equal(journey.shipped,null);
});

test('deadline reading uses supplied due time and freezes at shipment instead of growing after delivery',()=>{
 const first=orderIds(run)[0],early=orderJourney(run,first,0);
 assert.equal(early.deadline.due,run.instance.orders.find(row=>row.id===first).due_tick);
 assert.equal(early.deadline.difference,early.deadline.due);
 const shipped=orderJourney(run,first,run.horizon_ticks),atShip=orderJourney(run,first,shipped.shipped.tick);
 assert.ok(shipped.deadline.shipped);assert.equal(shipped.deadline.difference,atShip.deadline.difference);
 assert.equal(shipped.deadline.difference,shipped.deadline.due-shipped.shipped.tick);
 const unfinished=orderIds(run).map(order=>orderJourney(run,order,run.horizon_ticks)).find(row=>!row.shipped);
 assert.equal(unfinished.deadline.shipped,false);assert.equal(unfinished.deadline.difference,unfinished.deadline.due-run.horizon_ticks);
 assert.equal(orderJourney(blueprint(),'unknown',0).deadline,null);
});

test('urgent due dates appear only when their recorded order is revealed',()=>{
 const urgent=run.events.find(event=>event.type==='urgent_order');
 assert.ok(urgent);const before=orderJourney(run,urgent.order.id,urgent.tick-.01),revealed=orderJourney(run,urgent.order.id,urgent.tick);
 assert.equal(before.deadline,null);assert.equal(before.phase,'unreleased');
 assert.equal(revealed.deadline.due,urgent.order.due_tick);assert.equal(revealed.deadline.difference,urgent.order.due_tick-urgent.tick);
});

test('failed final inspection and rework do not become ready-to-ship states',()=>{
 const base=fixture().raw,pump='P01-pump';
 const trace=normalizeTrace({...base,operations:[...base.operations,{id:'repair-pump',order_id:'P01',unit_id:pump,machine_id:'S1',process:'S',start:60,end:61},{id:'reinspect-pump',order_id:'P01',unit_id:pump,machine_id:'QA2',process:'QA',start:61,end:63}],events:[...base.events,{tick:59,type:'qa_result',unit_id:pump,passed:false},{tick:63,type:'qa_result',unit_id:pump,passed:true}]});
 assert.equal(orderJourney(trace,'P01',56).phase,'inspection');
 assert.equal(orderJourney(trace,'P01',59).phase,'awaiting-rework');
 assert.equal(orderJourney(trace,'P01',60).phase,'rework');
 assert.equal(orderJourney(trace,'P01',61).phase,'inspection');
 assert.equal(orderJourney(trace,'P01',63).phase,'delivery');
 assert.equal(orderJourney(trace,'P01',63).shipped,null);
});
test('recorded final-pump scrap stays scrapped and cannot appear awaiting repair or shipment',()=>{
 const raw=JSON.parse(readFileSync(new URL('../output/stage2-search/final-independent-audit/nontrivial-proof-seed10020/audit-only-witness.json',import.meta.url)));
 const scrap=raw.events.find(e=>e.type==='scrap'&&e.unit_id==='P32/pump/1');assert.equal(scrap.tick,6790);
 assert.notEqual(orderJourney(raw,'P32',scrap.tick-1).phase,'scrapped');
 for(const tick of [scrap.tick,scrap.tick+1,raw.horizon_ticks]){
  const story=orderJourney(raw,'P32',tick);assert.equal(story.phase,'scrapped');assert.equal(story.scrap.tick,scrap.tick);assert.equal(story.shipped,null);assert.ok(story.components.every(c=>c.consumed));
 }
});
