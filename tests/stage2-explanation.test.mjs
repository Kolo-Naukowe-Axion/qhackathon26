import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {normalizeTrace,snapshot,machineStatus,blueprint} from '../presentation/stage2/model.js';
import {buildFactoryTour,tourRate} from '../presentation/stage2/factory-tour.js';
import {semanticChoice} from '../presentation/stage2/research-explain.js';
const run=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/checked-qaoa-8.json',import.meta.url))));

test('guided chapters point to real activities, shared resources, bridge travel and shipment',()=>{
 const chapters=buildFactoryTour(run);
 assert.deepEqual(chapters.map(row=>row.id),['parts','sharing','transport','assembly','inspection','shipment']);
 for(let i=1;i<chapters.length;i++)assert.ok(chapters[i].start>=chapters[i-1].end,'the walkthrough must not jump backwards in time');
 for(const chapter of chapters){assert.ok(chapter.start>=0&&chapter.end<=run.horizon_ticks&&chapter.end>chapter.start);assert.ok(Math.abs((chapter.end-chapter.start)/tourRate(chapter)-8)<1e-8);}
 for(const chapter of chapters.filter(row=>row.selection.kind==='machine'))assert.equal(machineStatus(run,chapter.selection.id,chapter.start).state,'working');
 const travel=chapters.find(row=>row.id==='transport');
 assert.ok(snapshot(run,(travel.start+travel.end)/2).moves.some(move=>move.agv_id===travel.selection.id&&move.legs.some(leg=>leg.from==='HUB_A'&&leg.to==='HUB_B'||leg.from==='HUB_B'&&leg.to==='HUB_A')));
 const sharing=chapters.find(row=>row.id==='sharing'),ops=run.operations.filter(row=>row.machine_id===sharing.selection.id&&row.start<=sharing.start);
 assert.ok(new Set(ops.map(row=>row.order_id)).size>1);
 const delivery=chapters.at(-1);
 assert.equal(snapshot(run,delivery.start).events.some(event=>event.type==='ship'&&event.unit_id===delivery.selection.id),false);
 assert.ok(snapshot(run,delivery.end).events.some(event=>event.type==='ship'&&event.unit_id===delivery.selection.id));
});

test('empty blueprint has no fabricated guided activities',()=>assert.deepEqual(buildFactoryTour(blueprint()),[]));

test('eight-code teaching lab agrees with independently retained feasible full orders',()=>{
 const bundle=JSON.parse(readFileSync(new URL('../presentation/stage2/research/evidence.json',import.meta.url))),valid=[];
 for(let n=0;n<8;n++){
  const bits=[n>>2&1,n>>1&1,n&1],choice=semanticChoice(bundle.data.rank_three_model,bits);
  assert.ok(choice.full.every(bit=>bit===0||bit===1));assert.ok(choice.energy>=0);
  const expanded=choice.full.reduce((sum,bit,i)=>sum+bit*2**i,0);
  assert.equal(choice.valid,bundle.data.rank_three_verification.retained_good_original_states.includes(expanded));
  if(choice.valid)valid.push(expanded);
 }
 assert.equal(valid.length,5);
 assert.deepEqual(valid.sort((a,b)=>a-b),bundle.data.rank_three_verification.retained_good_original_states);
});

test('larger stress trace has a chronological six-moment walkthrough too',()=>{
 const trace=normalizeTrace(JSON.parse(readFileSync(new URL('../presentation/stage2/traces/tool-homes-train0-12.json',import.meta.url))));
 const chapters=buildFactoryTour(trace);assert.equal(chapters.length,6);
 for(let i=1;i<chapters.length;i++)assert.ok(chapters[i].start>=chapters[i-1].end);
 assert.equal(chapters.at(-1).selection.id,'P01/pump/1');
 assert.ok(chapters.every(chapter=>chapter.orderId==='P01'));
 const travel=chapters.find(chapter=>chapter.id==='transport');
 const move=trace.moves.find(move=>move.agv_id===travel.selection.id&&move.start<=travel.start&&travel.start<move.end);
 assert.ok(move.unit_id.startsWith(travel.orderId+'/'),'bridge cargo must belong to the order shown in the sidebar');
});

test('malformed imported graph legs cannot create a backwards or out-of-range tour clip',()=>{
 const base=blueprint().raw;
 const trace=normalizeTrace({...base,horizon_ticks:10,operations:[{id:'op',unit_id:'part',machine_id:'T1',start:0,end:2}],moves:[{id:'move',unit_id:'part',agv_id:'AGV1',from:'HUB_A',to:'HUB_B',start:4,end:8,pickup_tick:4,drop_tick:8,legs:[{from:'HUB_A',to:'HUB_B',start:100,end:101,loaded:true}]}]});
 for(const chapter of buildFactoryTour(trace))assert.ok(chapter.start>=0&&chapter.end>chapter.start&&chapter.end<=10);
});
