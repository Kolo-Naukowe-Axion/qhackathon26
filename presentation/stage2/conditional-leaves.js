import {escapeHTML as esc} from './model.js';
const methods=[['cem6-2026-16','CEM16 · 96h'],['mpc-2future-16','MPC16 · 96h'],['cem6-2026-24','CEM24 · 96h'],['selected-stretch-32','Stretch32 · 240h']];
const fmt=(v,d=3)=>Number(v).toLocaleString('en',{maximumFractionDigits:d});
export function summarizeConditionalLeaves(data){
 if(!data||data.schema!=='stage2-final-conditional-view.v1'||data.source_files_verified!==true||data.no_new_factory_runs!==true||data.groups?.length!==4)return {valid:false};
 const groups=methods.map(([id])=>data.groups.find(g=>g.method_id===id));if(groups.some(g=>!g))return {valid:false};
 for(const group of groups){
  const n=group.method_id==='selected-stretch-32'?32:group.method_id==='cem6-2026-24'?24:16;
  if(group.config?.orders!==n||group.config.horizon!==(n===32?14400:5760)||group.config.profile!=='full'||!group.true_probability_reweighted_means||group.actor_seeds?.length!==1||group.leaves?.length!==8||group.published_overall_means_recovered!==true)return {valid:false};
  let mass=0,missing=0,success=0;
  for(let i=0;i<8;i++){
   const l=group.leaves[i],n=l.true_probability?.[0],d=l.true_probability?.[1],m=l.conditional_actor_averaged_means;
   if(l.leaf_index!==i||!Number.isInteger(n)||!Number.isInteger(d)||n<=0||d<=0||l.environment_tapes!==32||l.actor_seeds?.length!==1||JSON.stringify(l.actor_seeds)!==JSON.stringify(group.actor_seeds)||l.execution_rows!==32||l.uncertainty_intervals!==null||l.all_fulfilled_by_tape?.length!==32||!Number.isFinite(m?.missing_orders)||m.missing_orders<0||!Number.isFinite(m.all_orders_fulfilled)||m.all_orders_fulfilled<0||m.all_orders_fulfilled>1)return {valid:false};
   if(new Set(l.all_fulfilled_by_tape.map(t=>t.seed)).size!==32||l.all_fulfilled_by_tape.some(t=>!Number.isInteger(t.seed)||t.seed<10000||![0,1].includes(t.actor_mean_all_fulfilled))||Math.abs(l.all_fulfilled_by_tape.reduce((s,t)=>s+t.actor_mean_all_fulfilled,0)/32-m.all_orders_fulfilled)>1e-12)return {valid:false};
   const base=groups[0].leaves[i];if(JSON.stringify(base.outcomes)!==JSON.stringify(l.outcomes)||JSON.stringify(base.true_probability)!==JSON.stringify(l.true_probability)||JSON.stringify(base.all_fulfilled_by_tape.map(t=>t.seed))!==JSON.stringify(l.all_fulfilled_by_tape.map(t=>t.seed)))return {valid:false};
   mass+=n/d;missing+=n/d*m.missing_orders;success+=n/d*m.all_orders_fulfilled;
  }
  if(Math.abs(mass-1)>1e-12||Math.abs(missing-group.true_probability_reweighted_means.missing_orders)>1e-10||Math.abs(success-group.true_probability_reweighted_means.all_orders_fulfilled)>1e-12)return {valid:false};
 }
 return {valid:true,groups};
}
export function conditionalLeaves(data){
 if(!data)return '';const summary=summarizeConditionalLeaves(data);
 if(!summary.valid)return '<p class="research-note">Conditional outcomes suppressed: complete 32-environment cells, matching branches and exact probability recovery are required.</p>';
 const names={mill_ok:'Available',mill_outage:'Outage',supply_ok:'Normal',supply_stress:'Delayed',no_rush:'No',rush:'Yes'};
 return `<details class="reading-details"><summary>Eight observed event branches · 32 environments in every cell</summary><p>Each score is mean missing orders; the smaller line is the observed count shipping every order out of 32. The 32-order stretch gets 240h; the other columns get 96h. Different keyed quality tapes occur in different leaves, so conditional differences are descriptive associations, not causal effects of disruptions.</p><div class="research-table-wrap"><table class="research-table"><caption>Observed conditional final outcomes · true weights recover overall means</caption><thead><tr><th>Mill / supply / rush</th><th>True branch weight</th>${methods.map(([,label])=>`<th>${label}</th>`).join('')}</tr></thead><tbody>${Array.from({length:8},(_,i)=>{const l=summary.groups[0].leaves[i];return `<tr><td>${l.outcomes.map(o=>esc(names[o]??o)).join(' / ')}</td><td>${l.true_probability[0]}/${l.true_probability[1]} (${fmt(100*l.true_probability[0]/l.true_probability[1],1)}%)</td>${summary.groups.map(g=>{const c=g.leaves[i];return `<td>${fmt(c.conditional_actor_averaged_means.missing_orders,5)}<br><small>${c.all_fulfilled_by_tape.reduce((s,t)=>s+t.actor_mean_all_fulfilled,0)}/32 observed all fulfilled</small></td>`;}).join('')}</tr>`;}).join('')}</tbody></table></div><p class="plot-caption">Every cell has 32 environment tapes; actor replicas are nested and do not add environments. Observing 32/32 does not establish true success probability one. No intervals, new primary tests, prior sliders or causal estimates are added. The selected frontier and all final policies remain fixed.</p></details>`;
}
