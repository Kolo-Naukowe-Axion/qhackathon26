// Chapters are selected from this trace's actual activities, never a second run.
export function buildFactoryTour(trace){
 const chapters=[],operations=trace.operations.filter(op=>!op.kind||op.kind==='process').sort((a,b)=>a.start-b.start);
 const assembly=operations.find(op=>op.process==='ASSEMBLY'&&op.parent_unit_ids?.length);
 const focusOrder=assembly?.order_id??operations[0]?.order_id;
 const first=operations.find(op=>!focusOrder||op.order_id===focusOrder);
 const focusUnits=new Set(operations.filter(op=>!focusOrder||op.order_id===focusOrder).flatMap(op=>[op.unit_id,...op.parent_unit_ids??[]]));
 const add=(id,title,description,start,end,selection)=>{
  if(!Number.isFinite(start)||!Number.isFinite(end))return;
  const from=Math.max(0,start),to=Math.min(trace.horizon_ticks,end);if(to<=from)return;
  chapters.push({id,title,description,start:from,end:to,selection,orderId:focusOrder});
 };
 const componentNames=new Set(operations.filter(op=>op.order_id===first?.order_id).map(op=>op.unit_id.split('/')[1]));
 if(first)add('parts','Make the parts.',componentNames.has('housing')&&componentNames.has('rotor')&&componentNames.has('flange')?'Housing, rotor and flange follow different recipes.':'Each part needs time on a shared machine.',first.start,Math.min(first.end,first.start+24),{kind:'machine',id:first.machine_id,source:'a'});
 const shared=operations.find(op=>op.start>=Math.min(first?.end??0,(first?.start??0)+24)&&operations.some(before=>before.machine_id===op.machine_id&&before.end<=op.start&&before.order_id===focusOrder&&op.order_id&&before.order_id!==op.order_id));
 if(shared)add('sharing','Share the machines.',`${shared.order_id} takes ${shared.machine_id} after ${focusOrder}.`,shared.start,Math.min(shared.end,shared.start+24),{kind:'machine',id:shared.machine_id,source:'a'});
 const after=shared?Math.min(shared.end,shared.start+24):first?.end??0;
 const bridgeLeg=leg=>leg.start>=after&&(!assembly||leg.end<=assembly.start)&&leg.loaded!==false&&((leg.from==='HUB_A'&&leg.to==='HUB_B')||(leg.from==='HUB_B'&&leg.to==='HUB_A'));
 const hasRobot=move=>trace.resources.agvs.some(robot=>robot.id===move.agv_id);
 const crossing=trace.moves.find(move=>focusUnits.has(move.unit_id)&&hasRobot(move)&&move.legs?.some(bridgeLeg));
 const move=crossing??trace.moves.find(row=>focusUnits.has(row.unit_id)&&hasRobot(row)&&row.pickup_tick>=after&&(!assembly||row.drop_tick<=assembly.start)),leg=crossing?.legs.find(bridgeLeg);
 if(move)add('transport',crossing?'Cross the bridge.':'Move the part.',crossing?'Both halls share one lane. A robot carries the part across.':'A robot takes the part to its next machine.',leg?.start??move.pickup_tick,leg?.end??move.drop_tick,{kind:'agv',id:move.agv_id,source:'a'});
 if(assembly)add('assembly',assembly.parent_unit_ids.length===3?'Assemble the pump.':'Assemble the parts.','The checked components become one pump.',assembly.start,assembly.end,{kind:'machine',id:assembly.machine_id,source:'a'});
 const qa=assembly&&operations.find(op=>op.process==='QA'&&op.unit_id===assembly.unit_id&&op.start>=assembly.end);
 if(qa)add('inspection','Inspect the pump.','The assembled pump needs a final quality check.',qa.start,qa.end,{kind:'machine',id:qa.machine_id,source:'a'});
 const shipment=trace.events.find(event=>event.type==='ship'&&event.unit_id===assembly?.unit_id)??trace.events.find(event=>event.type==='ship'&&focusUnits.has(event.unit_id)&&event.tick>=(qa?.end??assembly?.end??0));
 if(shipment){
  const finalMove=trace.moves.find(row=>row.unit_id===shipment.unit_id&&row.drop_tick===shipment.tick);
  add('shipment','Ship the pump.','The order counts when the pump reaches shipping.',finalMove?Math.max(finalMove.pickup_tick,finalMove.drop_tick-2):Math.max(0,shipment.tick-1),shipment.tick,{kind:'unit',id:shipment.unit_id,source:'a'});
 }
 return chapters;
}

export function tourRate(chapter){return (chapter.end-chapter.start)/8;}
