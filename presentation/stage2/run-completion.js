const records=new WeakMap();
const orderOf=event=>event.order_id||String(event.unit_id??'').split('/')[0];

// Count physical ship events once per demanded order. The cutoff and the last
// shipment are different boundaries: terminal energy checks use the cutoff.
export function completionRecord(trace){
 if(records.has(trace))return records.get(trace);
 const expected=new Set((trace.instance.orders??[]).map(row=>row.id).filter(Boolean));
 for(const event of trace.events)if(event.type==='urgent_order'&&event.tick<=trace.horizon_ticks&&event.order?.id)expected.add(event.order.id);
 if(!expected.size)for(const op of trace.operations)if(op.order_id)expected.add(op.order_id);
 const total=Math.max(expected.size,Number.isFinite(trace.metrics.orders)?trace.metrics.orders:0);
 const first=new Map();
 for(const event of trace.events){
  const order=orderOf(event);
  if(event.type!=='ship'||!order||!Number.isFinite(event.tick)||event.tick<0||event.tick>trace.horizon_ticks||expected.size&&!expected.has(order))continue;
  if(!first.has(order)||event.tick<first.get(order).tick)first.set(order,event);
 }
 const shipments=[...first.values()].sort((a,b)=>a.tick-b.tick);
 const complete=total>0&&expected.size===total&&[...expected].every(id=>first.has(id));
 const record={total,shipments,completionTick:complete?shipments.at(-1).tick:null,lastShipment:shipments.at(-1)??null};
 records.set(trace,record);return record;
}
export function completionAt(trace,tick){
 const record=completionRecord(trace),shipped=record.shipments.filter(event=>event.tick<=tick).length;
 return {...record,shipped,complete:record.completionTick!==null&&tick>=record.completionTick,atCutoff:tick>=trace.horizon_ticks};
}
export function factoryDuration(ticks,tickMinutes=1){
 const minutes=Math.round(ticks*tickMinutes),hours=Math.floor(minutes/60),rest=minutes%60;
 return hours?rest?`${hours}h ${String(rest).padStart(2,'0')}m`:`${hours}h`:`${rest}m`;
}
