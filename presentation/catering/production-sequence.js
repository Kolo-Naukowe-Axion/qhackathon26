// Read-only projections of the retained schedule. No new scheduling decisions.
import {allOperations,mealOrders,clock} from './model.js';

export function orderName(meal){
  if(meal.id==='committed')return 'Order A';
  if(meal.id==='urgent')return 'Urgent order';
  const n=Number(/^customer-(\d+)$/.exec(meal.id)?.[1]);
  return Number.isInteger(n)?`Order ${n<25?String.fromCharCode(66+n):n+2}`:meal.id;
}
export function batchName(c,batch){
  const roles=new Set();
  for(const m of mealOrders(c))for(const [i,role] of [[0,'Main'],[1,'Side']])if(m.allocations[i]?.batch_id===batch.id)roles.add(role);
  return `${roles.size===1?[...roles][0]:'Menu'} ${batch.menu}`;
}
export function playbackEnd(c){
  return Math.max(c.snapshot.current_time,...allOperations(c).map(o=>o.end),...mealOrders(c).map(m=>m.departure));
}
export function componentStatus(c,meal,course,time){
  const index=course==='main'?0:1,allocation=meal.allocations[index];
  if(!allocation)return {label:course==='main'?'Main':'Side',status:'Not scheduled',state:'missing',ready_at:null};
  const batch=c.plan.batches.find(b=>b.id===allocation.batch_id),ops=c.plan.operations.filter(o=>o.batch_id===batch.id);
  const prepare=ops.find(o=>o.kind==='prepare'),cook=ops.find(o=>o.kind==='cook'),pack=ops.find(o=>o.id===allocation.packing_operation);
  let status,state='waiting';
  if(time>=meal.departure){status=meal.handed?'Served':'Discarded · no complete meal';state=meal.handed?'served':'missing';}
  else if(time>=pack.end){status='Packed · waiting for departure';state='ready';}
  else if(time>=pack.start){status='Packing';state='active';}
  else if(time>=cook.end)status=`Cooked · pack ${clock(pack.start)}`;
  else if(time>=cook.start){status='Cooking';state='active';}
  else if(time>=prepare.end)status=`Prepared · cook ${clock(cook.start)}`;
  else if(time>=prepare.start){status='Preparing';state='active';}
  else status=`Prep ${clock(prepare.start)}`;
  return {label:batchName(c,batch),status,state,ready_at:pack.end,batch_id:batch.id};
}
export function productionSequence(c){
  const meals=mealOrders(c),fixed=new Set(c.snapshot.fixed_batches.map(b=>b.id));
  const batches=c.plan.batches.map(batch=>{
    const operations=c.plan.operations.filter(o=>o.batch_id===batch.id);
    return {batch,operations,label:batchName(c,batch),committed:fixed.has(batch.id),cook:operations.find(o=>o.kind==='cook'),prepare:operations.find(o=>o.kind==='prepare')};
  });
  const cooking=[...batches].sort((a,b)=>a.cook.start-b.cook.start||a.cook.resource.localeCompare(b.cook.resource)||a.batch.id.localeCompare(b.batch.id));
  const packing=c.plan.operations.filter(o=>o.kind==='pack').sort((a,b)=>a.start-b.start||a.id.localeCompare(b.id)).map(operation=>{
    const allocation=c.plan.allocations.find(a=>a.packing_operation===operation.id);
    const meal=meals.find(m=>m.main===allocation?.demand_group||m.side===allocation?.demand_group);
    const batch=c.plan.batches.find(b=>b.id===operation.batch_id);
    return {operation,label:batchName(c,batch),meal,order:meal?orderName(meal):'Unallocated food'};
  });
  const inversion=batches.flatMap(a=>batches.filter(b=>a.prepare.start<b.prepare.start&&a.cook.start>b.cook.start).map(b=>({preparedFirst:a,cookedFirst:b})))[0];
  const eventTimes=[...new Set([0,c.snapshot.current_time,playbackEnd(c),...allOperations(c).flatMap(o=>[o.start,o.end]),...meals.map(m=>m.departure)])].sort((a,b)=>a-b);
  return {batches,cooking,packing,inversion,eventTimes,end:playbackEnd(c)};
}
export function adjacentEvent(sequence,time,direction){
  return direction>0?sequence.eventTimes.find(t=>t>time+1e-6)??sequence.end:[...sequence.eventTimes].reverse().find(t=>t<time-1e-6)??0;
}
export function eventDescription(c,time){
  const starts=allOperations(c).filter(o=>o.start===time).map(o=>o.recovery?'Recovery clean':`${{prepare:'Prep',cook:'Cook',pack:'Pack',clean:'Clean'}[o.kind]} ${c.plan.batches.find(b=>b.id===o.batch_id)?.menu??''}`);
  const departures=mealOrders(c).filter(m=>m.departure===time).map(m=>`${orderName(m)} ${m.handed?'departs':'missed'}`);
  const ends=allOperations(c).filter(o=>o.end===time).map(o=>`${o.recovery?'Recovery clean':`${{prepare:'Prep',cook:'Cook',pack:'Pack',clean:'Clean'}[o.kind]} ${c.plan.batches.find(b=>b.id===o.batch_id)?.menu??''}`} finishes`);
  return [...starts,...departures].join(' + ')||ends.join(' + ')||'Start of replay';
}
