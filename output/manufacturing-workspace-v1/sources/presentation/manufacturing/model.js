export const colors={housing:'#60899d',rotor:'#b9814d',flange:'#7b9b83',pump:'#335365'};
export const kind=id=>id.split('/')[1];
export const pump=id=>id.split('/')[0];
export function checkedCase(c){
 if(c.operations!==16*c.pumps||c.problem.operations.length!==c.operations)throw Error('Incomplete pump recipes');
 for(const s of c.plans){
  if(!s.check.valid||s.plan.length!==c.operations||new Set(s.plan.map(r=>r.operation)).size!==c.operations)throw Error('Invalid saved coverage');
  if(s.check.objective!==(c.problem.horizon+1)*s.check.weighted_terminal_tardiness+s.check.makespan)throw Error('Objective mismatch');
  for(const r of s.plan){const o=c.problem.operations.find(o=>o.id===r.operation);if(!o||!c.problem.machines[r.machine]||!c.problem.workers[r.worker]||r.end-r.start!==o.durations[r.machine])throw Error('Bad saved assignment');}
 }
 return c;
}
export function commitments(c,s){
 const nonterminal=new Set(c.problem.operations.flatMap(o=>o.predecessors));
 return c.problem.operations.filter(o=>!nonterminal.has(o.id)).map(o=>{const row=s.plan.find(r=>r.operation===o.id);return{order:pump(o.id),due:o.due,end:row.end,tardy:Math.max(0,row.end-o.due),operation:o.id};});
}
export function stateAt(c,s,tick){
 return {active:s.plan.filter(r=>r.start<=tick&&tick<r.end),attending:s.plan.filter(r=>r.start<=tick&&tick<r.attended_end),completed:new Set(s.plan.filter(r=>r.end<=tick).map(r=>r.operation))};
}
export function readiness(c,s,id,tick){
 const o=c.problem.operations.find(o=>o.id===id),r=s.plan.find(r=>r.operation===id);if(!r)return 'Select a saved operation.';
 if(r.end<=tick)return `Completed at ${r.end} min. This is process completion, not physical shipment.`;
 if(r.start<=tick)return `Processing on ${r.machine}. ${r.worker} attends through minute ${r.attended_end}.`;
 const pending=o.predecessors.filter(id=>s.plan.find(r=>r.operation===id).end>tick);
 if(pending.length)return `Waiting for ${pending.length} predecessor${pending.length===1?'':'s'}: ${pending.map(x=>x.split('/').slice(1).join('/')).join(', ')}.`;
 const release=Math.max(o.release,o.machine_release?.[r.machine]??0);
 if(tick<release)return `Release constraint: this assignment cannot start before minute ${release}.`;
 const busy=s.plan.find(x=>x.operation!==id&&x.worker===r.worker&&x.start<=tick&&tick<x.attended_end);
 if(busy)return `${r.worker} is currently attending ${busy.operation}. Planned start is minute ${r.start}.`;
 return `Predecessors have completed. Planned start: minute ${r.start}; transfer lags, calendars and other future assignments still apply.`;
}
export function lower(c){return Math.max(c.lower_bound.objective,c.reference.bound??0);}
