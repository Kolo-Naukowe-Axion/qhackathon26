import {escapeHTML as esc} from './model.js';
import {confirmationHTML,mountConfirmation} from './objective-confirmation.js';
const number=value=>Number(value).toLocaleString('en',{maximumFractionDigits:2});
let reward='exact-original';
export function summarizeObjective(data){
 const base=data?.ablation?.find(row=>row.policy_id==='exact-original'),changed=data?.ablation?.find(row=>row.policy_id==='exact-no-batch');
 const valid=Boolean(base&&changed&&data.final_tapes_used===0&&data.forks.length===4&&data.all_forced_commit_sets_match&&
  data.forks.every(row=>row.prefix_equal&&row.override_tick===420&&row.overrides===1&&row.fresh_checks.every(check=>check.valid&&check.terminal_requirements_met))&&
  JSON.stringify(base.conflicts)===JSON.stringify(changed.conflicts)&&JSON.stringify(base.capacities)===JSON.stringify(changed.capacities)&&
  Math.abs(base.candidate_rewards.C7-changed.candidate_rewards.C7-100)<1e-8&&
  data.targeted_summary.every(row=>row.invalid===0&&row.runs===12&&JSON.stringify(row.seeds)===JSON.stringify(data.targeted_summary[0].seeds)));
 return {valid,base,changed};
}
function offers(data){
 const variant=data.ablation.find(row=>row.policy_id===reward);
 return `<p class="metric-reading">This control switches between two retained local reward tables. It does not rerun the factory or change the observed fork results below.</p><div class="research-table-wrap"><table class="research-table"><caption>Tick ${data.example.tick} · same H2 furnace and W02 setup worker</caption><thead><tr><th>Actual offered start</th><th>Local reward</th><th>Worker attendance</th><th>Setup / processing</th><th>Chosen in this table?</th></tr></thead><tbody>${data.example.candidates.map(candidate=>{
  const op=candidate.operation,attendance=op.worker_intervals.reduce((sum,row)=>sum+row.end-row.start,0),chosen=variant.selected.includes(candidate.candidate_id);
  return `<tr${chosen?' class="objective-chosen"':''}><td>${esc(op.unit_ids.join(' + '))}</td><td>${number(variant.candidate_rewards[candidate.candidate_id])}</td><td>${attendance} min</td><td>${op.setup_ticks} / ${op.processing_ticks} min</td><td>${chosen?'Selected':'Conflicts with selected start'}</td></tr>`;
 }).join('')}</tbody></table></div><p class="plot-caption">The original +100 reward for an extra batch member makes P05's two-part batch outrank the earlier-priority P07 rotor. Both need the same furnace and worker. The batch adds a 30-minute family setup, holding W02 for 35 rather than 5 minutes. Removing only that batch bonus makes the exact local optimizer choose P07; physical capacities and conflicts at this fork are unchanged.</p>`;
}
export function objectiveMechanism(data,sourceLink,confirmation){
 if(!summarizeObjective(data).valid)return '<p class="research-note">Objective diagnostic suppressed: matched prefix, physical checks and local reward provenance are required.</p>';
 return `<details class="feature-details objective-mechanism"><summary>Why solving the local objective exactly can still lose orders</summary><section class="definition-section"><span class="eyebrow">RETROSPECTIVE TRAIN DIAGNOSTIC / SELECTED FAILURE COHORT</span><h3>A perfect local solve can prefer the wrong start.</h3><p>These four runs share their actual physical history before minute 420. At that boundary, two feasible HEAT starts compete for the same resources. The local objective rewards a batch even when its setup delays a shared worker.</p><label>Local reward table <select id="objective-reward"><option value="exact-original"${reward==='exact-original'?' selected':''}>Original: +100 per extra batch unit</option><option value="exact-no-batch"${reward==='exact-no-batch'?' selected':''}>Remove the extra batch bonus</option></select></label><div id="objective-offers">${offers(data)}</div>
 <h3>Change one decision. Keep exact selection afterward.</h3><p>This is an offline diagnostic: substitute the priority subset only at minute 420, then resume the original exact selector. Future outcomes are inspected afterward to measure consequences; the result is not a future-aware deployed policy.</p><div class="research-table-wrap"><table class="research-table"><caption>Freshly checked, physically identical prefix · four selected TRAIN tapes</caption><thead><tr><th>TRAIN seed</th><th>Original shipped</th><th>One-tick fork shipped</th><th>Realized orders</th><th>Cutoff debt before→after</th></tr></thead><tbody>${data.forks.map(row=>`<tr><td>${row.seed}</td><td>${row.before_shipped}</td><td>${row.after_shipped}</td><td>${row.orders}</td><td>${number(row.before_cutoff_debt)}→${number(row.after_cutoff_debt)} min</td></tr>`).join('')}</tbody></table></div>
 ${confirmation?confirmationHTML(confirmation,sourceLink):''}<details class="feature-details"><summary>Separate 48-run reward ablation on 12 selected TRAIN tapes</summary><p>TRAIN 0–7 plus diagnosed failures 15/23/25/26. This selected sample cannot estimate an unbiased success rate. Each method uses the same physical factory; later state-dependent candidate offers may diverge.</p><div class="research-table-wrap"><table class="research-table"><thead><tr><th>Selector / reward</th><th>Orders shipped</th><th>Complete runs</th><th>Cutoff deadline debt</th></tr></thead><tbody>${data.targeted_summary.map(row=>`<tr><td>${esc(row.policy_id)}</td><td>${row.shipped}/${row.required}</td><td>${row.complete}/${row.runs}</td><td>${number(row.total_tardiness)} min</td></tr>`).join('')}</tbody></table></div></details>
 <div class="research-note">NO UNBIASED RATE / NO FINAL TAPES / NO QUANTUM GAIN · Exactness applies only to the offered local surrogate. ${sourceLink('objective_mechanism')}</div></section></details>`;
}
export function mountObjective(root,data,confirmation){
 root.querySelector('#objective-reward')?.addEventListener('change',event=>{reward=event.target.value;root.querySelector('#objective-offers').innerHTML=offers(data);});
 if(confirmation)mountConfirmation(root,confirmation);
}
