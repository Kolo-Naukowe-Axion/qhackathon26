import {escapeHTML as esc} from './model.js';

const fmt=(value,digits=3)=>Number(value).toLocaleString('en',{maximumFractionDigits:digits});
let cohort='VALIDATION',metric='missing';
const stable=value=>JSON.stringify(value,Object.keys(value??{}).sort());
export function summarizeRecovery(campaign,role='VALIDATION'){
 const groups=campaign.groups.filter(row=>row.seed_role===role&&row.policy_id.includes('/family-guard4-kit/'));
 const orders=[...new Set(groups.map(row=>row.orders))].sort((a,b)=>a-b);
 return orders.map(order=>{
  const beforeRows=groups.filter(row=>row.orders===order&&row.policy_id.endsWith('/recovery0'));
  const afterRows=groups.filter(row=>row.orders===order&&row.policy_id.endsWith('/recovery1'));
  const before=beforeRows[0],after=afterRows[0];
  const options=row=>{if(!row)return null;const copy=structuredClone(row.solver_options);delete copy.recovery_policy.enabled;return JSON.stringify(copy);};
  const valid=Boolean(campaign.all_valid&&beforeRows.length===1&&afterRows.length===1&&before&&after&&before.runs>0&&after.runs>0&&before.valid===before.runs&&after.valid===after.runs&&
   stable(before.weights)===stable(after.weights)&&options(before)===options(after)&&before.horizon_ticks===after.horizon_ticks&&JSON.stringify(before.seeds)===JSON.stringify(after.seeds));
  return {orders:order,before,after,valid};
 });
}
export function summarizeHorizons(campaign){
 const groups=campaign.groups,orders=[...new Set(groups.map(row=>row.orders))].sort((a,b)=>a-b),horizons=[...new Set(groups.map(row=>row.horizon_ticks))].sort((a,b)=>a-b);
 const baseValid=Boolean(campaign.all_valid&&groups.length&&groups.every(row=>row.runs>0&&row.valid===row.runs&&row.seed_role==='TRAIN'));
 const cells=orders.flatMap(order=>horizons.map(horizon=>{
  const candidates=groups.filter(row=>row.orders===order&&row.horizon_ticks===horizon);
  const selected=[...candidates].sort((a,b)=>a.mean_unfulfilled-b.mean_unfulfilled||a.mean_tardiness_minutes-b.mean_tardiness_minutes||a.mean_total_cost-b.mean_total_cost)[0];
  return {orders:order,horizon,hours:horizon*campaign.tick_minutes/60,candidates,selected};
 }));
 const valid=baseValid&&Number.isFinite(campaign.tick_minutes)&&campaign.tick_minutes>0&&cells.every(cell=>cell.selected&&cell.candidates.length===3&&new Set(cell.candidates.map(row=>row.policy_id)).size===3&&cell.candidates.every(row=>JSON.stringify(row.seeds)===JSON.stringify(groups[0].seeds)));
 return {valid,orders,horizons,cells};
}
function recoveryPlot(rows){
 const w=1000,h=290,left=58,right=24,top=23,bottom=47,max=metric==='completion'?1:Math.max(...rows.flatMap(row=>[row.before.mean_unfulfilled,row.after.mean_unfulfilled]),1)*1.08;
 const x=order=>left+(order-rows[0].orders)/(rows.at(-1).orders-rows[0].orders)*(w-left-right);
 const value=row=>metric==='completion'?row.complete_runs/row.runs:row.mean_unfulfilled,y=v=>h-bottom-v/max*(h-top-bottom);
 return `<svg class="frontier-plot" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(cohort)} matched recovery policy outcomes by initial order load">
 ${[0,.25,.5,.75,1].map(t=>`<path class="plot-grid" d="M${left} ${y(max*t)}H${w-right}"/><text x="${left-10}" y="${y(max*t)+3}" text-anchor="end">${metric==='completion'?`${fmt(max*t*100,0)}%`:fmt(max*t,1)}</text>`).join('')}
 ${rows.map(row=>`<text x="${x(row.orders)}" y="${h-bottom+22}" text-anchor="middle">${row.orders}</text>`).join('')}
 ${['before','after'].map((key,index)=>`<polyline fill="none" stroke="${index?'#355e7c':'#a78c6a'}" stroke-width="2" ${index?'':'stroke-dasharray="5 4"'} points="${rows.map(row=>`${x(row.orders)},${y(value(row[key]))}`).join(' ')}"/>${rows.map(row=>`<circle cx="${x(row.orders)}" cy="${y(value(row[key]))}" r="4" fill="${index?'#355e7c':'#a78c6a'}"><title>${row.orders} initial orders; recovery ${index?'ON':'OFF'}: ${fmt(value(row[key]))}</title></circle>`).join('')}`).join('')}
 <text x="${w-right}" y="${h-3}" text-anchor="end">INITIAL ORDERS · URGENT ARRIVALS ALSO COUNT</text></svg>`;
}
function recoveryBody(data){
 const rows=summarizeRecovery(data.recovery,cohort);
 if(!rows.length||rows.some(row=>!row.valid))return '<p class="research-note">Performance plot suppressed: invalid or unmatched cohort groups are retained in the source.</p>';
 const sample=rows.find(row=>row.orders===12);
 return `<p class="metric-reading">${cohort}: seeds ${sample.after.seeds[0]}–${sample.after.seeds.at(-1)}, ${sample.after.runs} paired scenarios per load. ${metric==='completion'?'Fraction shipping every realized order by 96 hours; late shipments count. Higher is better.':'Mean orders still unshipped at96h. Lower is better.'}</p>${recoveryPlot(rows)}
 <p class="plot-caption"><span class="recovery-before">Dashed amber: recovery OFF.</span> Solid blue: recovery ON. At load 12, complete runs are ${sample.before.complete_runs}→${sample.after.complete_runs}/${sample.after.runs}, while mean missing falls ${fmt(sample.before.mean_unfulfilled)}→${fmt(sample.after.mean_unfulfilled)}. The worst observed missing count falls ${sample.before.max_unfulfilled}→${sample.after.max_unfulfilled}; these remain development observations.</p>
 <div class="research-table-wrap"><table class="research-table"><caption>Same family admission, QA guard 4 and kit policy; only recovery toggled · ${cohort}</caption><thead><tr><th>Initial orders</th><th>Complete OFF→ON</th><th>Mean missing OFF→ON</th><th>Worst missing OFF→ON</th><th>Mean cutoff debt OFF→ON</th></tr></thead><tbody>${rows.map(row=>`<tr><td>${row.orders}</td><td>${row.before.complete_runs}→${row.after.complete_runs}/${row.after.runs}</td><td>${fmt(row.before.mean_unfulfilled)}→${fmt(row.after.mean_unfulfilled)}</td><td>${row.before.max_unfulfilled}→${row.after.max_unfulfilled}</td><td>${fmt(row.before.mean_tardiness_minutes,1)}→${fmt(row.after.mean_tardiness_minutes,1)} min</td></tr>`).join('')}</tbody></table></div>
 <p class="plot-caption">Cutoff debt adds actual delivered lateness and unfinished-order debt only through the horizon. Eventual lateness of unshipped orders remains unknown. All tested loads, including unresolved 16 and 24, remain visible. The source also retains the separate no-guard baseline variant.</p>`;
}
function horizonDetail(cell){
 const row=cell.selected;
 return `<div class="policy-detail"><div><span class="eyebrow">SELECTED WITHIN THIS TRAIN SWEEP</span><h3>${cell.orders} initial orders · ${fmt(cell.hours,0)} hours</h3><p class="policy-id">${esc(row.policy_id)}</p><p>${cell.candidates.length} tested prior rules · seeds ${row.seeds[0]}–${row.seeds.at(-1)}. This is selection on the displayed training data.</p></div><dl><div><dt>Runs shipping all</dt><dd>${row.complete_runs}/${row.runs}</dd></div><div><dt>Mean missing at cutoff</dt><dd>${fmt(row.mean_unfulfilled)}</dd></div><div><dt>Mean cutoff-censored debt</dt><dd>${fmt(row.mean_tardiness_minutes,1)} min</dd></div></dl></div>`;
}
function horizonBody(data){
 const grid=summarizeHorizons(data.horizon);
 if(!grid.valid||grid.cells.some(cell=>!cell.selected))return '<p class="research-note">Horizon plot suppressed: invalid or missing policy groups are retained in the source.</p>';
 const initial=grid.cells.find(cell=>cell.orders===24&&cell.horizon===11520)??grid.cells[0];
 return `<div class="research-table-wrap"><table class="research-table horizon-matrix"><caption>Best tested rule in each cell · complete runs/${initial.selected.runs} · TRAIN seeds ${initial.selected.seeds[0]}–${initial.selected.seeds.at(-1)}</caption><thead><tr><th>Initial orders</th>${grid.horizons.map(h=>`<th>${fmt(h*data.horizon.tick_minutes/60,0)} hours</th>`).join('')}</tr></thead><tbody>${grid.orders.map(order=>`<tr><th>${order}</th>${grid.horizons.map(h=>{const cell=grid.cells.find(c=>c.orders===order&&c.horizon===h),row=cell.selected;return `<td><button class="horizon-cell ${row.complete_runs===row.runs?'all-complete':'part-complete'}" data-horizon-order="${order}" data-horizon-tick="${h}" aria-label="${order} initial orders, ${cell.hours} hours: ${row.complete_runs}/${row.runs} complete; inspect selected policy"><strong>${row.complete_runs}/${row.runs}</strong><small>Missing avg ${fmt(row.mean_unfulfilled)}</small></button></td>`;}).join('')}</tr>`).join('')}</tbody></table></div><p class="plot-caption">Click a cell to inspect its actual selected rule. Each cell chooses among three prior rules by mean missing, then cutoff debt, then cost, using these same TRAIN seeds. It does not establish an optimum or held-out performance.</p><div id="horizon-detail">${horizonDetail(initial)}</div>`;
}
export function summarizePrimary(proof){
 const {cohort,certificate,audit}=proof??{};
 const valid=Boolean(cohort&&certificate&&audit&&cohort.all_primary_bounds_attained&&cohort.orders===32&&cohort.horizon_ticks===14400&&
  cohort.rows.length===8&&JSON.stringify(cohort.rows.map(row=>row.seed).sort((a,b)=>a-b))==='[0,1,2,3,4,5,6,7]'&&
  cohort.rows.every(row=>row.physical_valid&&row.terminal_requirements_met&&row.primary_optimum_attained&&row.unfulfilled===row.unfulfilled_lower_bound)&&
  cohort.secondary_optimality_gap===null&&audit.all_adversarial_assumption_changes_rejected&&
  cohort.source_hashes['stage2/quality_material_bound.py']===audit.audited_source_sha256&&certificate.instance_sha256===audit.instance_sha256&&
  certificate.seed===6&&certificate.horizon_ticks===cohort.horizon_ticks);
 return {valid,complete:cohort?.rows.filter(row=>row.unfulfilled===0).length,attained:cohort?.rows.filter(row=>row.primary_optimum_attained).length,
  orders:certificate?.observed_realized_orders,stock:certificate?.available_raw_blanks.housing,
  needed:certificate?Object.values(certificate.necessary_blank_demands).reduce((sum,need)=>sum+(need?.[0]??0),0):null,
  evidence:certificate?.unavoidable_quality_evidence.find(row=>row.unit_id==='P05/housing/1')};
}
function primaryBody(proof,sourceLink){
 const result=summarizePrimary(proof);
 if(!result.valid||!result.evidence)return '<p class="research-note">Primary certificate suppressed: matching source-bound proof and physically checked witnesses are required.</p>';
 const evidence=result.evidence;
 return `<section class="definition-section"><span class="eyebrow">03 / FIXED REALIZED TRAIN TAPES · PRIMARY OBJECTIVE ONLY</span><h3>The last missing order can be unavoidable.</h3><p>At 32 initial orders and 240h, ${result.complete}/8 scenarios ship every realized order. All ${result.attained}/8 physically checked witnesses attain a proved minimum unfulfilled count for their own fixed tape. This is a per-instance primary certificate, not a new all-orders-complete result.</p>
 <div class="policy-detail"><div><span class="eyebrow">WHY SEED 6 CANNOT SHIP ALL ORDERS</span><h3>${result.orders} realized orders need at least ${result.needed} housing blanks.</h3><p>Only ${result.stock} blanks exist. The original P05 housing must fail its first inspection and its single repair inspection under every legal manufacturing mode, consuming one extra blank if P05 is fulfilled. Shipping ${result.orders-1} orders attains the resulting one-missing-order bound.</p></div><dl><div><dt>First keyed draw / required risk floor</dt><dd>${fmt(evidence.first_draw*100,3)}% &lt; ${fmt(evidence.first_risk_floor*100,3)}%</dd></div><div><dt>Repair draw / fixed risk floor</dt><dd>${fmt(evidence.repair_draw*100,3)}% &lt; ${fmt(evidence.repair_risk_floor*100,3)}%</dd></div><div><dt>Blank conservation</dt><dd>${result.needed} needed &gt; ${result.stock} available</dd></div></dl></div>
 <p class="plot-caption">The ${result.complete} complete cases attain the elementary lower bound of zero missing; seed 6 needs the nontrivial quality/material argument. That bound uses an offline analysis of immutable future draws and finite stock; those draws are not controller inputs. It assumes the audited engine's original RAW lineages, matched BOM, legal modes, one repair/replacement, declared supply and bounded quality model. All eight certificate instance hashes match retained checked full-physics witnesses. The independent audit separately reconstructs seed 6's hash draws and checks the material relaxation against 60 exhaustive small cases. Deadline debt and cost may still improve; no secondary optimum, final-tape, universal-policy or quantum advantage claim follows.</p>
 ${proof.replay?`<div class="research-note"><a href="?trace=./traces/large-train0-32-240h.json.gz&amp;view=factory">Load the actual large factory replay ↗</a><p>${esc(proof.replay.label)} · ${proof.replay.operations} recorded operations · ${proof.replay.moves} robot moves · ${proof.replay.metrics.shipped}/${proof.replay.metrics.orders} shipped. Total tardiness ${fmt(proof.replay.metrics.total_tardiness_ticks,0)} min; model cost ${fmt(proof.replay.metrics.total_cost,2)}. This optional ${fmt(proof.replay.compressed_bytes/1000,0)}KB compressed trace loads only when selected. Ten days is extra calendar time, not 96-hour success. ${sourceLink('large_replay')}</p></div>`:''}
 <div class="research-note">FROZEN SOURCE / MATCHED CERTIFICATES AND WITNESSES · ${sourceLink('primary_quality')} · seed6 ${sourceLink('primary_quality_seed6')} · independent audit ${sourceLink('primary_quality_audit')}</div></section>`;
}
export function laterFrontier(data,sourceLink,proof){
 return `<div class="research-heading"><div><span class="eyebrow">LATER DEVELOPMENT / FIXED FACTORY / EXPLICIT LIMITS</span><h2>Push the load. Then measure what changes.</h2><p>Two separate experiments: improve a controller within 96 hours, or give the same physical factory more calendar time. Neither is a final held-out result.</p></div></div>
 <section class="definition-section"><span class="eyebrow">01 / SAME 96-HOUR HORIZON · RECOVERY OFF VERSUS ON</span><h3>Recover a blocked kit without adding capacity.</h3><p>${data.recovery.completed} reported checker-valid runs. The selected controller uses hard tool homes, family admission, QA guard 4 and kit reservation. The paired toggle adds only bounded physical buffer recovery. TRAIN and VALIDATION remain distinct; validation is still development selection.</p><div class="plot-toolbar"><label>Cohort <select id="recovery-cohort"><option${cohort==='VALIDATION'?' selected':''}>VALIDATION</option><option${cohort==='TRAIN'?' selected':''}>TRAIN</option></select></label><label>Vertical axis <select id="recovery-metric"><option value="missing"${metric==='missing'?' selected':''}>Mean unshipped ↓</option><option value="completion"${metric==='completion'?' selected':''}>Complete-run fraction ↑</option></select></label></div><div id="recovery-cohort-body">${recoveryBody(data)}</div></section>
 <section class="definition-section"><span class="eyebrow">02 / EXTRA CALENDAR TIME · SAME RESOURCES AND ORIGINAL DUE DATES</span><h3>A longer horizon changes the capacity question.</h3><p>${data.horizon.completed} reported checker-valid TRAIN runs across four cutoffs. More calendar time supplies more worker, machine and transport hours. This is not faster computation, a 96-hour solution, or an on-time-delivery guarantee.</p>${horizonBody(data)}<p class="plot-caption">An independent rebuild checked ${data.horizon_scope_audit.numerical_instance_comparisons} same-order/seed instance comparisons: only <code>horizon_ticks</code> changed. Initial due dates, physical resources and event definitions remained fixed. Cost includes the longer operating window. A complete run may still contain late shipments.</p></section>
 ${primaryBody(proof,sourceLink)}<div class="research-note">NO FINAL TAPES · Original reports, protocol hashes, all policy groups and aggregation checks are retained. ${sourceLink('later_frontier')}</div>`;
}
export function mountLaterFrontier(root,data){
 const refresh=()=>{root.querySelector('#recovery-cohort-body').innerHTML=recoveryBody(data);};
 root.querySelector('#recovery-cohort')?.addEventListener('change',event=>{cohort=event.target.value;refresh();});
 root.querySelector('#recovery-metric')?.addEventListener('change',event=>{metric=event.target.value;refresh();});
 root.querySelector('.horizon-matrix')?.addEventListener('click',event=>{
  const button=event.target.closest('[data-horizon-order]');if(!button)return;
  const grid=summarizeHorizons(data.horizon),cell=grid.cells.find(row=>row.orders===Number(button.dataset.horizonOrder)&&row.horizon===Number(button.dataset.horizonTick));
  root.querySelector('#horizon-detail').innerHTML=horizonDetail(cell);
 });
}
