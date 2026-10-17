import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {normalizeTrace} from '../presentation/stage2/model.js';
import {completionAt,completionRecord,factoryDuration} from '../presentation/stage2/run-completion.js';
import {buildFactoryTour} from '../presentation/stage2/factory-tour.js';

test('final production completes at the last physical shipment, separately from terminal cutoff',()=>{
 for(const [orders,horizon,last]of [[12,5760,4152],[32,14400,11356]]){
  const trace=normalizeTrace(JSON.parse(gunzipSync(readFileSync(new URL(`../presentation/stage2/traces/final-first-leaf0-${orders}-${horizon}.json.gz`,import.meta.url)))));
  assert.equal(completionRecord(trace).completionTick,last);
  assert.equal(completionAt(trace,last-.001).complete,false);
  assert.equal(completionAt(trace,last).complete,true);
  assert.equal(completionAt(trace,last).atCutoff,false);
  assert.equal(completionAt(trace,horizon).completionTick,last);
  const finish=buildFactoryTour(trace).at(-1);assert.equal(finish.id,'completion');assert.equal(finish.end,last);
  assert.equal(finish.selection.id,completionRecord(trace).lastShipment.unit_id);
 }
 assert.equal(factoryDuration(4152),'69h 12m');assert.equal(factoryDuration(11356),'189h 16m');
 assert.equal(factoryDuration(5760),'96h');
});

test('duplicates, unknown shipments and future urgent demand cannot falsely complete a run',()=>{
 const trace={instance:{orders:[{id:'A'},{id:'B'}]},operations:[],metrics:{orders:3},horizon_ticks:10,events:[{tick:1,type:'ship',order_id:'A'},{tick:2,type:'ship',order_id:'A'},{tick:3,type:'ship',order_id:'B'},{tick:4,type:'ship',order_id:'unknown'},{tick:5,type:'urgent_order',order:{id:'C'}},{tick:9,type:'ship',order_id:'C'}]};
 assert.equal(completionAt(trace,4).shipped,2);assert.equal(completionAt(trace,4).complete,false);
 assert.equal(completionAt(trace,9).shipped,3);assert.equal(completionAt(trace,9).complete,true);
 const unfinished={...trace,events:trace.events.filter(event=>event.order_id!=='C')};
 assert.equal(completionAt(unfinished,10).complete,false);
 const tooLate={...trace,events:trace.events.map(event=>event.order_id==='C'?{...event,tick:11}:event)};
 assert.equal(completionAt(tooLate,10).complete,false);
});

test('a checked but incomplete trace reaches its cutoff without an invented finish chapter',()=>{
 const trace=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url))));
 assert.equal(completionAt(trace,trace.horizon_ticks).complete,false);
 assert.equal(completionAt(trace,trace.horizon_ticks).shipped,13);
 assert.equal(buildFactoryTour(trace).some(chapter=>chapter.id==='completion'),false);
});
