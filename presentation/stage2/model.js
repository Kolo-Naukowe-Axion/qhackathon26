/** Versioned display adapter. Display validation is not a physical feasibility proof. */
export const SCHEMA = 'metaltech-stage2-trace.v1';
export const BLUEPRINT_MACHINES = [
  ['T1','A','T'],['T2','A','T'],['F1','A','F'],['F2','A','F'],['WASH1','A','WASH'],['H1','A','HEAT'],['QA1','A','QA'],
  ['F3','B','F'],['S1','B','S'],['S2','B','S'],['WASH2','B','WASH'],['H2','B','HEAT'],['QA2','B','QA'],['A1','B','ASSEMBLY'],['A2','B','ASSEMBLY'],
].map(([id,hall,process])=>({id,hall,process,input_capacity:process==='ASSEMBLY'?6:process==='HEAT'||process==='QA'?4:2}));
const number = (value,fallback=0) => Number.isFinite(Number(value))?Number(value):fallback;
const array = value => Array.isArray(value)?value:[];
const id = value => String(value ?? '');
const interval = (row,index,kind) => ({...row,id:id(row.id||`${kind}-${index}`),start:number(row.start??row.start_tick),end:number(row.end??row.end_tick),unit_id:id(row.unit_id??row.part_id??row.unit??row.job_id),unit_ids:array(row.unit_ids).length?row.unit_ids.map(id):[id(row.unit_id??row.part_id??row.unit??row.job_id)].filter(Boolean),order_id:id(row.order_id??row.order),machine_id:id(row.machine_id??row.machine??row.resource_id),worker_ids:array(row.worker_ids??row.workers),tool_ids:array(row.tool_ids??row.tools)});
export function normalizeTrace(input){
  if(!input||typeof input!=='object'||Array.isArray(input)) throw new Error('A trace must be a JSON object.');
  if(input.schema!==SCHEMA) throw new Error(`Unsupported trace schema: ${input.schema??'missing'}. Expected ${SCHEMA}.`);
  const resources=input.resources??{};
  const operations=array(input.operations??input.schedule??input.activities).map((row,index)=>interval(row,index,'operation'));
  const moves=array(input.moves??input.transport).map((row,index)=>({...interval(row,index,'move'),agv_id:id(row.agv_id??row.agv),from:id(row.from??row.origin),to:id(row.to??row.destination),pickup_tick:number(row.pickup_tick,row.start),drop_tick:number(row.drop_tick,row.end),legs:array(row.legs)}));
  for(const row of [...operations,...moves]) if(row.start<0||row.end<=row.start) throw new Error(`Invalid half-open interval for ${row.id}.`);
  const machines=array(resources.machines??input.machines);
  const machineIds=new Set(machines.map(row=>id(row.id)));
  for(const row of operations) if(row.machine_id&&!machineIds.has(row.machine_id)) throw new Error(`Unknown machine ${row.machine_id} in ${row.id}.`);
  const horizon=number(input.horizon_ticks,Math.max(1,...operations.map(row=>row.end),...moves.map(row=>row.end)));
  if(horizon<=0) throw new Error('The trace horizon must be positive.');
  if([...operations,...moves].some(row=>row.end>horizon)) throw new Error('An activity ends beyond the trace horizon.');
  return {schema:SCHEMA,run_id:id(input.run_id??input.name??'Imported run'),tick_minutes:number(input.tick_minutes,15),horizon_ticks:horizon,
    provenance:{...input.provenance,kind:input.provenance?.kind??'unverified'},resources:{...resources,machines,agvs:array(resources.agvs),workers:array(resources.workers),tools:array(resources.tools)},operations,moves,
    events:array(input.events).map(row=>({...row,tick:number(row.tick??row.time),resource_id:id(row.resource_id??row.machine_id)})).sort((a,b)=>a.tick-b.tick),
    energy:array(input.energy).sort((a,b)=>a.tick-b.tick),validation:input.validation??{status:'unverified'},metrics:input.metrics??{},instance:input.instance??{},raw:input};
}
export function blueprint(){return normalizeTrace({schema:SCHEMA,run_id:'MetalTech · design blueprint',tick_minutes:15,horizon_ticks:384,provenance:{kind:'blueprint',instance:'metaltech_pressure.json',description:'Proposed layout. No solver run loaded. Resource positions are a visual schematic.'},resources:{machines:BLUEPRINT_MACHINES,agvs:[1,2,3,4].map(n=>({id:`AGV${n}`})),workers:Array.from({length:10},(_,i)=>({id:`W${String(i+1).padStart(2,'0')}`})),tools:[{id:'MILL-KIT-1'},{id:'MILL-KIT-2'},{id:'WELD-1'},{id:'WELD-2'},{id:'CALIBRATION'}]},operations:[],moves:[],events:[]});}
export function fixture(){
  const base=blueprint().raw;
  const operations=[
    ['H-T','housing','T','T1',1,5],['R-T','rotor','T','T2',1,5],['F-F','flange','F','F1',1,5],
    ['H-F','housing','F','F2',9,15],['R-H','rotor','HEAT','H1',9,17],['F-S','flange','S','S1',10,14],
    ['H-W','housing','WASH','WASH1',20,22],['R-F','rotor','F','F3',23,28],['F-W','flange','WASH','WASH2',19,21],
    ['H-H','housing','HEAT','H1',26,34],['R-W','rotor','WASH','WASH2',33,35],['F-Q','flange','QA','QA2',26,29],
    ['H-Q','housing','QA','QA1',38,41],['R-Q','rotor','QA','QA2',39,42],
    ['ASSEMBLY','pump','ASSEMBLY','A1',48,52],['P-Q','pump','QA','QA2',56,59],
  ].map(([id,unit_id,process,machine_id,start,end],i)=>({id,unit_id:`P01-${unit_id}`,order_id:'P01',process,machine_id,start,end,mode:'standard',worker_ids:[`W${String(i%10+1).padStart(2,'0')}`],tool_ids:process==='F'?['MILL-KIT-1']:[],...(process==='ASSEMBLY'?{parent_unit_ids:['P01-housing','P01-rotor','P01-flange']}:{})}));
  const routes={housing:['STOCK','T1','F2','WASH1','H1','QA1','A1'],rotor:['STOCK','T2','H1','F3','WASH2','QA2','A1'],flange:['STOCK','F1','S1','WASH2','QA2','A1'],pump:['A1','QA2','SHIPPING']};
  const moves=[];
  for(const [unit,route] of Object.entries(routes))for(let i=0;i<route.length-1;i++){
    const preceding=operations.find(op=>op.unit_id===`P01-${unit}`&&op.machine_id===route[i]);
    const next=operations.find(op=>op.unit_id===`P01-${unit}`&&op.machine_id===route[i+1]);
    const end=next?.start??(preceding?.end??60)+4;
    const start=preceding?.end??Math.max(0,end-1);
    if(end>start)moves.push({id:`MOVE-${unit}-${i}`,unit_id:`P01-${unit}`,agv_id:`AGV${moves.length%4+1}`,from:route[i],to:route[i+1],start,end});
  }
  return normalizeTrace({...base,run_id:'Synthetic display fixture',horizon_ticks:64,provenance:{kind:'synthetic',solver:'None · handcrafted animation',description:'UI fixture only. Not a solver result, not physically validated. Resources may conflict.'},operations,moves,
    events:[{tick:16,type:'machine_outage',resource_id:'F2',description:'Illustrative outage · fixture only',end:24}],
    energy:Array.from({length:65},(_,tick)=>({tick,grid_kw:12+operations.filter(op=>op.start<=tick&&tick<op.end).length*9,cap_kw:90,solar_kw:Math.max(0,Math.round(18*Math.sin(tick/64*Math.PI))),soc:40})),validation:{status:'not_validated',description:'Display fixture; no physical feasibility claim.'}});
}
export function snapshot(trace,tick){
  const active=trace.operations.filter(row=>row.start<=tick&&tick<row.end);
  const completed=trace.operations.filter(row=>row.end<=tick);
  const moves=trace.moves.filter(row=>row.start<=tick&&tick<row.end);
  const units=new Set([...array(trace.instance.units).map(row=>id(row.id)),...trace.operations.flatMap(row=>row.unit_ids),...trace.operations.map(row=>row.unit_id)].filter(Boolean));
  const location=new Map();
  for(const unit of units){
    const latest=[...completed.filter(row=>row.unit_ids.includes(unit)||row.unit_id===unit).map(row=>({time:row.end,at:row.machine_id})),...trace.moves.filter(row=>row.unit_id===unit&&row.drop_tick<=tick).map(row=>({time:row.drop_tick,at:row.to}))].sort((a,b)=>b.time-a.time)[0];
    const created=trace.operations.find(row=>row.process==='ASSEMBLY'&&row.unit_id===unit);
    if(created&&tick<created.end)continue;
    const initial=array(trace.instance.units).find(row=>id(row.id)===unit)?.initial_location??'STOCK';
    location.set(unit,latest?.at??initial);
  }
  for(const row of active)if(row.process!=='ASSEMBLY')for(const unit of row.unit_ids)location.set(unit,row.machine_id);
  for(const row of moves)if(row.unit_id&&row.entity_type!=='tool'&&row.pickup_tick<=tick&&tick<row.drop_tick)location.set(row.unit_id,row.agv_id);
  for(const row of trace.operations)if(row.start<=tick)for(const unit of array(row.parent_unit_ids))location.delete(unit);
  return {tick,active,completed,moves,units,location,events:trace.events.filter(row=>row.tick<=tick),energy:trace.energy.filter(row=>row.tick<=tick).at(-1)??null};
}
export function machineStatus(trace,machine,tick){
  const op=trace.operations.find(row=>row.machine_id===machine&&row.start<=tick&&tick<row.end);
  const outage=trace.events.find(row=>row.resource_id===machine&&row.type.includes('outage')&&row.tick<=tick&&tick<(row.end??trace.horizon_ticks));
  const held=trace.operations.filter(row=>row.machine_id===machine&&row.end<=tick&&row.kind!=='maintenance'&&row.kind!=='tool_service').sort((a,b)=>b.end-a.end)[0];
  const blocked=held?.unit_ids.some(unit=>!trace.moves.some(move=>move.unit_id===unit&&move.from===machine&&move.pickup_tick>=held.end&&move.pickup_tick<=tick)&&!trace.operations.some(row=>row.start<=tick&&array(row.parent_unit_ids).includes(unit)));
  return outage?{state:'outage',event:outage}:op?{state:op.kind==='maintenance'?'maintenance':'working',operation:op}:blocked?{state:'output held',operation:null}:{state:trace.provenance.kind==='blueprint'?'proposed':'idle'};
}
export function metricsAt(trace,tick){
  const state=snapshot(trace,tick);
  return {active:state.active.length,completed:state.completed.length,operations:trace.operations.length,moving:state.moves.length,orders:new Set(trace.operations.map(row=>row.order_id).filter(Boolean)).size};
}
export function deadlineEvidence(trace){
 const metrics=trace.metrics??{},checked=trace.validation?.metrics??{},scale=Number(trace.tick_minutes??1);
 const incomplete=metrics.all_orders_fulfilled===false||trace.validation?.all_orders_fulfilled===false;
 const supplied=Number.isFinite(metrics.total_tardiness_ticks)?metrics.total_tardiness_ticks*scale:null;
 const debt=Number.isFinite(checked.terminal_deadline_debt_ticks)?checked.terminal_deadline_debt_ticks*scale:supplied;
 const delivered=Number.isFinite(checked.tardiness_ticks)?checked.tardiness_ticks*scale:incomplete?null:supplied;
 return {incomplete,label:incomplete?'Censored deadline debt':'Total tardiness',
  primaryMinutes:supplied??debt,deliveredOnlyMinutes:delivered,cutoffDebtMinutes:debt,
  explanation:incomplete?'Includes unshipped orders only through the cutoff; their eventual lateness is unknown.':'All realized orders shipped; no unfinished-order censoring remains.'};
}
export function resourceOccupancy(trace,tick){
 const state=snapshot(trace,tick),workingUnits=new Set(state.active.flatMap(row=>row.unit_ids));
 const buffers=trace.resources.machines.map(machine=>{
   const here=[...state.location].filter(([,at])=>at===machine.id).map(([unit])=>unit);
   const output=here.filter(unit=>!workingUnits.has(unit)&&trace.operations.some(op=>op.machine_id===machine.id&&op.end<=tick&&op.unit_ids.includes(unit)&&!trace.moves.some(move=>move.unit_id===unit&&move.from===machine.id&&move.pickup_tick>=op.end&&move.pickup_tick<=tick)));
   const input=here.filter(unit=>!workingUnits.has(unit)&&!output.includes(unit));
   const reserved=trace.moves.filter(move=>move.to===machine.id&&move.start<=tick&&tick<move.drop_tick&&move.entity_type!=='tool'&&move.unit_id).map(move=>move.unit_id);
   return {machine_id:machine.id,input,output,reserved,capacity:machine.input_capacity??null};
 });
 return {buffers,workers:state.active.flatMap(op=>(Array.isArray(op.worker_intervals)?op.worker_intervals.filter(row=>row.start<=tick&&tick<row.end).map(row=>row.worker_id):op.worker_ids).map(worker=>({id:worker,operation_id:op.id,machine_id:op.machine_id}))),tools:state.active.flatMap(op=>op.tool_ids.map(tool=>({id:tool,operation_id:op.id,machine_id:op.machine_id})))};
}
export function unitGenealogy(trace,unit){
  const own=trace.operations.filter(row=>row.unit_ids.includes(unit)||row.unit_id===unit).sort((a,b)=>a.start-b.start);
  const parents=[...new Set(own.flatMap(row=>array(row.parent_unit_ids)))];
  const children=[...new Set(trace.operations.filter(row=>array(row.parent_unit_ids).includes(unit)).map(row=>row.unit_id))];
  return {unit,operations:own,parents,children};
}
export const escapeHTML = value => String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
