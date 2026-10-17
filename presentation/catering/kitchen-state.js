import {offline,mealOrders,allOperations} from './model.js';
export function stationState(c,resource,time){
  const operation=allOperations(c).find(o=>o.resource===resource&&o.start<=time&&time<o.end);
  const batch=operation&&c.plan.batches.find(b=>b.id===operation.batch_id);
  return {resource,operation,batch,mode:offline(c,resource,time)?'offline':operation?.kind??((c.plan.recovery_operations??[]).some(o=>o.resource===resource&&time>=o.repair_end&&time<o.start)?'awaiting_clean':'idle'),
    progress:operation?(time-operation.start)/(operation.end-operation.start):0,
    remaining:operation?Math.ceil(operation.end-time):0,
    next:allOperations(c).filter(o=>o.resource===resource&&o.start>time).sort((a,b)=>a.start-b.start)[0]};
}
export function kitchenVisualState(c,time){
  const orders=mealOrders(c);
  return {stations:Object.fromEntries(['P1','C1','C2','K1'].map(id=>[id,stationState(c,id,time)])),
    ready:orders.filter(m=>m.ready_at!==null&&time>=m.ready_at&&time<m.departure),
    departing:orders.filter(m=>m.handed&&time>=m.departure&&time<m.departure+1).map(m=>({...m,progress:time-m.departure})),
    waitingPrep:c.plan.batches.filter(b=>{const op=c.plan.operations.find(o=>o.batch_id===b.id&&o.kind==='prepare');return op&&time>=op.end&&time<b.cook_start;})};
}
export function decodedActions(c,index){
  const program=index===-1?c.snapshot.fixed_batches[0]:c.options[index];
  if(!program)return [];
  const ops=index===-1?c.plan.operations.filter(o=>o.batch_id===program.id):program.operations;
  return ['prepare','cook','pack','clean'].flatMap(kind=>{
    const group=ops.filter(o=>o.kind===kind),first=group[0];
    return first?[{kind,start:first.start,end:Math.max(...group.map(o=>o.end)),resource:first.resource,worker:first.worker,attended_end:first.attended_end,program}]:[];
  });
}
export function withAlternative(reference,index){
  const alternative=reference.alternatives.find(a=>a.index===index&&a.valid);
  if(!alternative)throw new Error('No checked intervention for this program');
  return {...reference,...alternative,manual:true};
}
