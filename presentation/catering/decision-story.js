import {clock,selectedPrograms,requestedMeals,deliveredMeals} from './model.js';
import {decodedActions} from './kitchen-state.js';
export function decisionSteps(c){
  const programs=selectedPrograms(c),p=programs[0];
  if(!p)return [{title:'A checked continuation',copy:'The current view executes its saved operations, including committed work and any recovery clean.',duration:3}];
  const index=c.options.indexOf(p),actions=decodedActions(c,index);
  return [
    {title:`${programs.length} batch choices become a plan`,copy:'Each selected program sets quantity, equipment, crew and times. Idle bits leave their anchor unused.',duration:2.5},
    {title:'Two courses make one meal',copy:'Main and side must both be packed for the same departure. An unpaired component is waste, even when it was cooked on time.',duration:3},
    {title:`Follow x${index+1}: Menu ${p.menu}`,copy:`${p.yield_lots*c.instance.lot_size} component portions. Prep starts ${clock(actions[0].start)} on ${actions[0].resource}, with ${actions[0].worker}.`,duration:2.8},
    {title:'Now run the saved schedule',copy:'The kitchen follows the checked operations. The clock animates a retained result; no optimizer runs during playback.',duration:2.5},
  ];
}
function outcome(c,index,plan,metrics){
  const view={...c,plan};
  return {index,program:c.options[index],plan,metrics,served:deliveredMeals(view,Infinity),
    waste:metrics.W*c.instance.lot_size,missed:requestedMeals(c)-deliveredMeals(view,Infinity)};
}
export function decisionComparison(c,reference){
  const candidate=c.manual?{index:c.index,plan:reference.plan,metrics:reference.metrics}:reference.alternatives.find(a=>a.valid&&a.metrics.U>c.metrics.U)??reference.alternatives[0];
  if(!candidate)return null;
  const index=c.manual?c.index:candidate.index;
  const current=outcome(c,index,c.plan,c.metrics),other=outcome(c,candidate.index,candidate.plan,candidate.metrics);
  const total=requestedMeals(c),difference=Math.abs(current.served-other.served);
  return {current,other,total,winner:difference?'served':'tie',
    title:difference?`${difference} meals depend on this batch.`:'A checked change to the plan.',
    copy:`${c.manual?'This intervention skips':'Skip'} x${index+1}: cooking one course alone cannot serve a complete meal. Compare actual handovers and discarded component portions.`,
    constraint:c.snapshot.outages.length?'C2 is repaired at 11:30, then cleaned 11:40–11:50. Cooking resumes only after that clean.':'The committed Menu A batch stays in both plans. This is a checked drop-to-idle intervention, not another solver run.'};
}
