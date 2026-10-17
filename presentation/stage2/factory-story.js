// Presentation summaries derive only from the currently loaded trace.
export const productionOperations=trace=>trace.operations.filter(op=>!op.kind||op.kind==='process');
export function orderIds(trace){return [...new Set(productionOperations(trace).map(op=>op.order_id).filter(Boolean))];}
export function orderJourney(trace,orderId,tick,location=new Map()){
 const operations=productionOperations(trace).filter(op=>op.order_id===orderId);
 const assembly=operations.find(op=>op.process==='ASSEMBLY'&&op.parent_unit_ids?.length);
 const pump=assembly?.unit_id,parents=assembly?.parent_unit_ids??[...new Set(operations.filter(op=>op.process!=='ASSEMBLY'&&op.unit_id!==pump).map(op=>op.unit_id))];
 const shipped=pump?trace.events.find(event=>event.type==='ship'&&event.unit_id===pump&&event.tick<=tick)??null:null;
 const afterAssembly=assembly?operations.filter(op=>op.unit_id===pump&&op.start>=assembly.end).sort((a,b)=>a.start-b.start):[];
 const inspection=afterAssembly.filter(op=>op.process==='QA').at(-1),pumpCurrent=afterAssembly.find(op=>op.start<=tick&&tick<op.end);
 const scrap=trace.events.find(event=>event.type==='scrap'&&event.unit_id===pump&&event.tick<=tick)??null;
 const lastQuality=trace.events.filter(event=>event.type==='qa_result'&&event.unit_id===pump&&event.tick<=tick).at(-1);
 const components=parents.map(id=>{
  const steps=operations.filter(op=>op.unit_id===id).sort((a,b)=>a.start-b.start);
  const current=steps.find(op=>op.start<=tick&&tick<op.end),finished=steps.filter(op=>op.end<=tick).length;
  return {id,kind:id.split('/')[1]??id.split('-').at(-1),steps,current,finished,location:location.get(id),consumed:Boolean(assembly&&assembly.start<=tick)};
 });
 const arrival=trace.events.find(event=>event.type==='urgent_order'&&event.order?.id===orderId),order=trace.instance.orders?.find(row=>row.id===orderId)??(arrival&&arrival.tick<=tick?arrival.order:null),release=order?.release_tick??arrival?.tick??null;
 const released=release===null||tick>=release;
 const phase=!released?'unreleased':shipped?'shipped':scrap?'scrapped':pumpCurrent?.process==='QA'?'inspection':pumpCurrent?'rework':lastQuality?.passed===false?'awaiting-rework':inspection&&tick>=inspection.end?'delivery':assembly&&tick>=assembly.end?'awaiting-inspection':assembly&&tick>=assembly.start?'assembly':'components';
 const relatedMachines=new Set(components.filter(row=>!row.consumed).map(row=>row.current?.machine_id??row.location).filter(Boolean));
 const relatedRobots=new Set(components.filter(row=>!row.consumed).map(row=>row.location).filter(Boolean));
 if(assembly&&tick>=assembly.start){const current=operations.find(op=>op.unit_id===pump&&op.start<=tick&&tick<op.end);if(current)relatedMachines.add(current.machine_id);const at=location.get(pump);if(at){relatedMachines.add(at);relatedRobots.add(at);}}
 const due=Number.isFinite(order?.due_tick)?order.due_tick:null;
 const deadline=due===null?null:{due,difference:due-(shipped?.tick??tick),shipped:Boolean(shipped)};
 return {orderId,assembly,inspection,pump,components,phase,shipped,scrap,relatedMachines,relatedRobots,deadline};
}
export function nextActivityTick(trace,tick){
 return [...productionOperations(trace).map(op=>op.start),...trace.moves.map(move=>move.start),...trace.events.filter(event=>event.type==='ship'||event.type.includes('outage')||event.type==='urgent_order'||event.type==='release').map(event=>event.tick)].filter(time=>time>tick+.05&&time<=trace.horizon_ticks).sort((a,b)=>a-b)[0]??trace.horizon_ticks;
}
export function partGlyph(kind){
 const body=kind==='housing'?'<path d="M9 10h18v18H9zM5 15h4m18 0h4M5 24h4m18 0h4"/><circle cx="18" cy="19" r="5"/>':kind==='rotor'?'<path d="M3 18h30M8 13v10m20-10v10"/><circle cx="18" cy="18" r="9"/><path d="m14 12 8 12m-10-6h12m-10 6 8-12"/>':kind==='flange'?'<circle cx="18" cy="18" r="12"/><circle cx="18" cy="18" r="5"/><path d="M18 8v2m0 16v2M8 18h2m16 0h2"/>':'<path d="M10 10h17v17H10zM27 14h6v9h-6M10 16H4v7h6M13 27v4m11-4v4"/><circle cx="18.5" cy="18.5" r="5"/><path d="M18.5 13.5v10m-5-5h10"/>';
 return `<svg viewBox="0 0 36 36" aria-hidden="true">${body}</svg>`;
}
