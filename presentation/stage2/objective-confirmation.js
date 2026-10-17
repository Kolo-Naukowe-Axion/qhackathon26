import {escapeHTML as esc} from './model.js';
const mean=values=>values.reduce((sum,value)=>sum+value,0)/values.length;
const fmt=(value,digits=3)=>Number(value).toLocaleString('en',{maximumFractionDigits:digits});
let selectedLoad=12,selectedReward='priority-lex';
export function summarizeConfirmation(data){
 const groups=data?.groups??[],seeds=JSON.stringify(Array.from({length:32},(_,i)=>i));
 let valid=Boolean(data?.source_files_verified&&data.final_tapes_used===0&&data.runs===2240&&data.valid===2240&&data.decode_mismatches===0&&
  groups.reduce((sum,group)=>sum+group.tapes.length,0)===data.runs&&new Set(groups.map(group=>`${group.orders}:${group.policy_id}`)).size===groups.length&&
  groups.every(group=>JSON.stringify(group.tapes.map(row=>row.seed).sort((a,b)=>a-b))===seeds&&group.tapes.every(row=>row.valid&&row.decode_mismatches===0&&
   Number.isInteger(row.orders)&&Number.isInteger(row.shipped)&&row.shipped>=0&&row.shipped<=row.orders&&row.complete===(row.shipped===row.orders)&&Number.isFinite(row.cutoff_debt)&&
   data.physical_instance_hashes[`${group.orders}:${row.seed}`])));
 const summaries=groups.map(group=>({...group,shipped:group.tapes.reduce((sum,row)=>sum+row.shipped,0),required:group.tapes.reduce((sum,row)=>sum+row.orders,0),
  complete:group.tapes.filter(row=>row.complete).length,meanMissing:mean(group.tapes.map(row=>row.orders-row.shipped)),meanDebt:mean(group.tapes.map(row=>row.cutoff_debt))}));
 const sampled=new Map();
 for(const group of groups.filter(row=>row.actor!==null)){
  const key=`${group.orders}:${group.method}:${group.reward_mode}`;
  if(!sampled.has(key))sampled.set(key,[]);sampled.get(key).push(group);
 }
 const actors=[...sampled.values()].map(members=>{
  const first=members[0],actorIds=members.map(row=>row.actor).sort((a,b)=>a-b);
  if(JSON.stringify(actorIds)!=='[7,13,29]')valid=false;
  const clustered=Array.from({length:32},(_,seed)=>{
   const factory=members.map(group=>group.tapes.find(row=>row.seed===seed));
   if(factory.some(row=>!row)||new Set(factory.map(row=>row?.orders)).size!==1){valid=false;return {missing:NaN,complete:NaN,debt:NaN};}
   return {missing:mean(factory.map(row=>row.orders-row.shipped)),complete:mean(factory.map(row=>Number(row.complete))),debt:mean(factory.map(row=>row.cutoff_debt))};
  });
  return {orders:first.orders,method:first.method,reward_mode:first.reward_mode,actors:actorIds,environments:32,
   meanMissing:mean(clustered.map(row=>row.missing)),completeFraction:mean(clustered.map(row=>row.complete)),meanDebt:mean(clustered.map(row=>row.debt)),
   actorTotals:members.map(group=>({actor:group.actor,shipped:group.tapes.reduce((sum,row)=>sum+row.shipped,0),complete:group.tapes.filter(row=>row.complete).length})).sort((a,b)=>a.actor-b.actor)};
 });
 return {valid,groups:summaries,actors,loads:[...new Set(groups.map(row=>row.orders))].sort((a,b)=>a-b)};
}
function body(data){
 const summary=summarizeConfirmation(data);
 if(!summary.valid)return '<p class="research-note">Confirmation suppressed: every predeclared group, paired tape and all three actors must remain valid and present.</p>';
 const deterministic=summary.groups.filter(row=>row.orders===selectedLoad&&row.actor===null),actors=summary.actors.filter(row=>row.orders===selectedLoad&&row.reward_mode===selectedReward);
 return `<div class="research-table-wrap">${deterministic.length?`<table class="research-table"><caption>Static selectors · ${selectedLoad} initial orders · 32 paired physical tapes</caption><thead><tr><th>Selector / local objective</th><th>Shipped / required</th><th>Complete runs</th><th>Mean missing</th><th>Mean cutoff debt</th></tr></thead><tbody>${deterministic.map(row=>`<tr><td>${esc(row.policy_id)}</td><td>${row.shipped}/${row.required}</td><td>${row.complete}/32</td><td>${fmt(row.meanMissing)}</td><td>${fmt(row.meanDebt,1)} min</td></tr>`).join('')}</tbody></table>`:'<p>Static selectors were not measured at this load in this confirmation campaign; their absence is retained.</p>'}</div>
 <h3>All declared actors, averaged within each factory first.</h3><p>Actor seeds 7/13/29 are repeated solver randomness on the same 32 environments. They are not 96 independent factory scenarios. Each mean below first averages the three actors within each physical tape, then averages the 32 tapes. No actor is selected for its outcome.</p>
 ${actors.length?`<div class="research-table-wrap"><table class="research-table"><caption>${selectedReward} reward · ${selectedLoad} initial orders · 32 environments ×3 actors each</caption><thead><tr><th>Configured sampler</th><th>Mean missing</th><th>Mean complete fraction</th><th>Mean cutoff debt</th><th>Actor totals shipped / complete runs</th></tr></thead><tbody>${actors.map(row=>`<tr><td>${esc(row.method.toUpperCase())}</td><td>${fmt(row.meanMissing,4)}</td><td>${fmt(row.completeFraction*100,2)}%</td><td>${fmt(row.meanDebt,1)} min</td><td>${row.actorTotals.map(actor=>`${actor.actor}: ${actor.shipped} / ${actor.complete}`).join(' · ')}</td></tr>`).join('')}</tbody></table></div>`:'<p>Randomized actor runs were not measured at this load; only the static comparisons above are available.</p>'}
 <p class="plot-caption">“Complete fraction” averages actor outcomes; it is not an integer count of 32 distinct successes. The last column retains every actor’s total shipped and complete-run count across 32 tapes. QAOA denotes a CPU-simulated configuration with declared classical fallbacks, not physical QPU execution.</p>`;
}
export function confirmationHTML(data,sourceLink){
 const summary=summarizeConfirmation(data);
 if(!summary.valid)return '<p class="research-note">Full TRAIN confirmation unavailable or invalid; original retained diagnostic remains separate.</p>';
 const n12=summary.groups.filter(row=>row.orders===12),original=n12.find(row=>row.policy_id==='exact-original'),corrected=n12.find(row=>row.policy_id==='exact-no-batch'),priority=n12.find(row=>row.policy_id==='priority-original'),lex=n12.find(row=>row.policy_id==='exact-priority-lex');
 const n16=summary.groups.filter(row=>row.orders===16),original16=n16.find(row=>row.policy_id==='exact-original'),corrected16=n16.find(row=>row.policy_id==='exact-no-batch');
 return `<section class="definition-section reward-confirmation"><span class="eyebrow">LATER CONFIRMATION / FULL CONTIGUOUS TRAIN0–31 / STILL DEVELOPMENT DATA</span><h3>Correcting the objective survives the full training cohort.</h3><p>${data.runs.toLocaleString('en')} valid runs with zero recorded decode mismatches. At 12 initial orders, exact-original ships ${original.shipped}/${original.required} with ${original.complete}/32 complete runs; exact-no-batch ships ${corrected.shipped}/${corrected.required} with ${corrected.complete}/32 complete. Priority reaches ${priority.shipped}/${priority.required}; exact priority-lex reaches ${lex.shipped}/${lex.required}. This tests the objective correction, not a quantum advantage.</p>
 <p class="plot-caption">This is broader than the earlier 12-tape selected-failure diagnostic, but remains reused development TRAIN data, not an unbiased unseen-data estimate or final evaluation. At 16 orders the original exact objective ships ${original16.shipped}/${original16.required}, while no-batch ships ${corrected16.shipped}/${corrected16.required}: the correction is not uniformly better. Higher-load failures remain selectable.</p>
 <div class="plot-toolbar"><label>Initial orders <select id="confirmation-load">${summary.loads.map(load=>`<option${load===selectedLoad?' selected':''}>${load}</option>`).join('')}</select></label><label>Sampled reward <select id="confirmation-reward"><option value="priority-lex"${selectedReward==='priority-lex'?' selected':''}>Priority-lex</option><option value="no-batch"${selectedReward==='no-batch'?' selected':''}>No extra batch bonus</option></select></label></div><div id="confirmation-body">${body(data)}</div>
 <p class="research-note">At 12 orders, all three actors of QAOA, SA and uniform under priority-lex match exact’s physical metrics on every tape. No quantum gain is observed in that comparison. No-batch actors vary; every declared actor remains included. Cutoff debt includes unshipped orders only through 96h, leaving their eventual lateness unknown.</p>
 <p class="plot-caption">Encoding scope: these are corrected rich-factory local start-selection controllers. The three-bit baseline certificate concerns a different scheduling instance; earlier 23-bit scaling fixtures use older reward semantics and are not substituted here. Original report, protocol, all ${data.runs} rows, full frozen source files and independent aggregation digests remain retained. ${sourceLink('reward_confirmation')}</p></section>`;
}
export function mountConfirmation(root,data){
 const refresh=()=>{root.querySelector('#confirmation-body').innerHTML=body(data);};
 root.querySelector('#confirmation-load')?.addEventListener('change',event=>{selectedLoad=Number(event.target.value);refresh();});
 root.querySelector('#confirmation-reward')?.addEventListener('change',event=>{selectedReward=event.target.value;refresh();});
}
