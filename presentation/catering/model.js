export const CASES = {
  CELL: {title:'Two courses. One meal.', short:'Complete small cell', event:'Main + side must reach the same departure'},
  S0: {title:'Lunch service', short:'Larger · normal service', event:'Six customers + the committed meal'},
  S1: {title:'One more order.', short:'Larger · urgent order', event:'+10 complete meals revealed at 10:50'},
  S2: {title:'A cooker goes offline.', short:'Larger · cooker outage', event:'C2 repair + mandatory post-repair clean'},
  S3: {title:'A little kitchen chaos.', short:'Larger · both events', event:'Urgent order + cooker outage + recovery clean'},
};
export const PHASES = {prepare:'Prep',cook:'Cook',pack:'Pack',clean:'Clean'};
export const RESOURCES = ['P1','C1','C2','K1'];
export function clock(minute, origin='10:30') {
  const [h,m]=origin.split(':').map(Number), total=h*60+m+Math.floor(minute);
  return `${String(Math.floor(total/60)).padStart(2,'0')}:${String(total%60).padStart(2,'0')}`;
}
export const allOperations=c=>[...c.plan.operations,...(c.plan.recovery_operations??[]).map(o=>({...o,kind:'clean',recovery:true,attended_end:o.end}))];
export const activeOperations=(c,t)=>allOperations(c).filter(o=>o.start<=t&&t<o.end);
export const workerOperation=(c,w,t)=>allOperations(c).find(o=>o.worker===w&&o.start<=t&&t<o.attended_end);
export const offline=(c,r,t)=>c.snapshot.outages.some(o=>o.resource===r&&o.start<=t&&t<o.end);
export function mealOrders(c) {
  const groups=new Map(c.snapshot.demand_groups.map(d=>[d.id,d]));
  return c.instance.service_model.meals.filter(m=>groups.has(m.main)&&groups.has(m.side)).map(m=>{
    const demand=groups.get(m.main), handover=c.plan.meal_handovers.find(h=>h.meal_id===m.id);
    const allocations=[m.main,m.side].map(id=>c.plan.allocations.find(a=>a.demand_group===id));
    const operations=allocations.map(a=>a&&c.plan.operations.find(o=>o.id===a.packing_operation));
    return {...m,departure:demand.departure,revealed:demand.revealed,handed:!!handover,
      allocations,ready_at:operations.every(Boolean)?Math.max(...operations.map(o=>o.end)):null};
  });
}
export const requestedMeals=c=>mealOrders(c).length*c.instance.lot_size;
export const deliveredMeals=(c,t)=>c.plan.meal_handovers.reduce((n,h)=>n+(t>=h.time?h.lots*c.instance.lot_size:0),0);
export const packedMeals=(c,t)=>mealOrders(c).reduce((n,m)=>n+(m.ready_at!==null&&t>=m.ready_at?c.instance.lot_size:0),0);
export const discardedComponents=(c,t)=>[...c.plan.disposals,...c.plan.unpaired_disposals].reduce((n,d)=>n+(t>=d.time?d.lots*c.instance.lot_size:0),0);
export const selectedPrograms=c=>c.options.filter((_,i)=>c.bits[i]===1);
export const selectedProgram=c=>selectedPrograms(c)[0];
export const bitDescription=(c,i)=>c.options[i]?`Menu ${c.options[i].menu} · ${c.options[i].yield_lots*c.instance.lot_size} component portions · ${c.options[i].cooker}`:`Idle · ${c.onehot_groups.find(g=>g.idle_index===i)?.anchor??'anchor'}`;
export const activateRun=(fixture,key='qaoa')=>({...fixture,...fixture.runs.find(r=>r.key===key)});
