import {colors,kind,pump,checkedCase,commitments,stateAt,readiness,lower} from './model.js';
import {positions} from '../stage2/factory-layout.js';
import {glyphBody} from '../stage2/factory-parts.js';
import {attachMeritPlans} from './merit-model.js';
import {mountMerit} from './merit.js';
import {storySteps,selectedStory,elapsed} from './story.js';
const $=s=>document.querySelector(s),n=(x,d=0)=>Number(x).toLocaleString('en',{maximumFractionDigits:d});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={'nominal-32':'32 ops · nominal capacity','mill-down-32':'32 ops · milling capacity lost','rush-and-outage-32':'32 ops · expedited order + mill outage','lease-recovery-32':'32 ops · delayed replacement mill','crew-shortage-32':'32 ops · multi-skilled worker absent','heat-outage-32':'32 ops · furnace outage + tight deadlines','heat-lease-32':'32 ops · replacement furnace from 360m','nominal-64':'64 ops · four complete pumps','nominal-128':'128 ops · eight complete pumps'};
const data=await fetch('data.json').then(r=>{if(!r.ok)throw Error('Saved study unavailable');return r.json()});
const merit=await fetch('merit-data.json').then(r=>{if(!r.ok)throw Error('Merit study unavailable');return r.json()});
attachMeritPlans(data.cases,merit);
for(const c of Object.values(data.cases))checkedCase(c);
const state={case:'heat-outage-32',method:'raw_reference',order:'P01',operation:'P01/housing/step0',tick:360,resource:'machine',playing:false,ghost:false};
const point=id=>id==='H3'?[1120,335]:id==='F4'?[1120,165]:positions[id]??[570,250];
const current=()=>data.cases[state.case],plan=()=>current().plans.find(s=>s.id===state.method)??current().plans[0];
function operationName(id){const [,k,step]=id.split('/');return `${k} · ${Number(step.slice(4))+1}`;}
function machineBody(id,active,missing,selected){
 const process=id.replace(/\d/g,''),[x,y]=point(id),h=colors[kind(active?.operation??'P01/pump/x')];
 const equipment=process==='H'?`<rect x="-28" y="-37" width="58" height="48" fill="#778a94"/><rect x="-20" y="-28" width="42" height="28" fill="${active?'#b87a46':'#526976'}"/><path d="M-24 -44H27M-16 -50H18" stroke="#5b7480" stroke-width="5"/>`:process==='T'||process==='F'?`<rect x="-33" y="-22" width="66" height="34" fill="#88a0ae"/><rect x="-26" y="-33" width="27" height="25" fill="#b6c7cf"/><circle class="spindle" cx="14" cy="-20" r="12" fill="#4f7183"/><path d="M14 -31V-9M3 -20H25" stroke="#bfced5" stroke-width="3"/>`:process==='WASH'?`<rect x="-32" y="-31" width="65" height="41" fill="#8da9b8"/><path d="M-24 -15H23M-24 -4H23" stroke="#bed2dc" stroke-width="5"/>`:process==='A'?`<rect x="-35" y="-17" width="70" height="14" fill="#a4bac6"/><path d="M-27 -3V14M27 -3V14" stroke="#668595" stroke-width="6"/>`:`<rect x="-32" y="-22" width="64" height="33" fill="#93aeba"/><path d="M-20 -22V-43H13V-29" stroke="#567888" stroke-width="6"/>`;
 return `<g tabindex="0" role="button" aria-label="Inspect machine ${id}" data-machine="${id}" class="${active?'processing ':''}${missing?'offline':''}" transform="translate(${x} ${y})"><path d="M-55 -13L0 -39L55 -13L0 15Z" fill="#c1d1da" stroke="${selected?'#365d73':'#9eb5c2'}" stroke-width="${selected?3:1}"/><path d="M-55 -13V1L0 29L55 1V-13L0 15Z" fill="#a9bfcc" stroke="#91aab9"/>${equipment}<circle class="status-dot" cx="39" cy="-34" r="4" fill="${missing?'#a16c50':'#a4b7c2'}"/>${active?`<g transform="translate(-11 -27) scale(.6)">${glyphBody(kind(active.operation))}</g><rect x="-42" y="37" width="84" height="16" fill="${h}"/><text x="0" y="48" text-anchor="middle" style="fill:white;font-size:8px">${esc(pump(active.operation))} / ${esc(kind(active.operation))}</text>`:`<text class="machine-caption" x="0" y="48" text-anchor="middle">${missing?'OFFLINE':((id==='H3'||id==='F4')&&state.tick<360?'AVAILABLE FROM 360m':'IDLE AT THIS TIME')}</text>`}<text x="0" y="72" text-anchor="middle" style="font-size:13px;font-weight:600">${id}</text>${missing?'<path d="M-30 -45L35 16M35 -45L-30 16" stroke="#9e6848" stroke-width="4"/>':''}</g>`;
}
function renderFloor(c,s){
 const snap=stateAt(c,s,state.tick),selected=s.plan.find(r=>r.operation===state.operation);
 const ids=[...new Set([...Object.keys(positions).filter(id=>/^(T|F|S|WASH|H|QA|A)\d+$/.test(id)),...Object.keys(c.problem.machines)])];
 let dependencies='';
 if(selected){const o=c.problem.operations.find(o=>o.id===selected.operation);dependencies=o.predecessors.map(id=>{const prior=s.plan.find(r=>r.operation===id),a=point(prior.machine),b=point(selected.machine);return `<path d="M${a[0]} ${a[1]+15}Q${(a[0]+b[0])/2} ${Math.min(a[1],b[1])-100} ${b[0]} ${b[1]-20}" fill="none" stroke="${colors[kind(id)]}" stroke-width="3" stroke-dasharray="7 6" opacity=".8"/>`;}).join('');}
 $('#floor').innerHTML=`<svg viewBox="0 0 1250 585" role="group" aria-label="Two-hall planning schematic at minute ${n(state.tick)}"><defs><pattern id="deck" width="40" height="25" patternUnits="userSpaceOnUse"><path d="M40 0H0V25" fill="none" stroke="#a6bccb" stroke-width=".6"/></pattern></defs><path d="M55 84L370 35L550 135V534L110 550L55 470Z" fill="#c4d4de" stroke="#afc4d1"/><path d="M630 84L1040 35L1210 135V534L680 550L630 470Z" fill="#c4d4de" stroke="#afc4d1"/><rect x="65" y="95" width="480" height="420" fill="url(#deck)"/><rect x="640" y="95" width="565" height="420" fill="url(#deck)"/><path d="M540 260H640" stroke="#a2bac9" stroke-width="32"/><path d="M540 260H640" stroke="#d7e2e8" stroke-width="22"/><text class="hall-title" x="90" y="65">HALL A / MACHINING</text><text class="hall-title" x="660" y="65">HALL B / JOIN & FINISH</text>${dependencies}${ids.map(id=>machineBody(id,snap.active.find(r=>r.machine===id),!c.problem.machines[id],selected?.machine===id)).join('')}</svg>`;
}
function renderCommitments(c,s){
 $('#commitments').innerHTML=commitments(c,s).map(r=>`<button class="commitment" data-order="${r.order}" aria-pressed="${r.order===state.order}"><b>${r.order}</b><span class="${r.tardy?'late':'ontime'}">${r.tardy?n(r.tardy)+'m late':'On time'}</span><small>Due ${n(r.due)}m · final QA ends ${n(r.end)}m<br>${r.end<=state.tick?'Final inspection completed':'Planned completion; not a shipment event'}</small></button>`).join('');
 const r=s.plan.find(r=>r.operation===state.operation),o=c.problem.operations.find(o=>o.id===state.operation);
 $('#inspector').innerHTML=r?`<p class="eyebrow">SELECTED OPERATION</p><h3>${esc(state.operation.replaceAll('/',' / '))}</h3><dl><div><dt>Machine / hall</dt><dd>${r.machine} / ${r.hall}</dd></div><div><dt>Worker</dt><dd>${r.worker}</dd></div><div><dt>Processing</dt><dd>${n(r.start)}–${n(r.end)}m</dd></div><div><dt>Attendance ends</dt><dd>${n(r.attended_end)}m</dd></div><div><dt>Family</dt><dd>${esc(o.family)}</dd></div></dl><p class="reason">${esc(readiness(c,s,state.operation,state.tick))}</p>`:'';
}
function renderBOM(c,s){
 const ops=c.problem.operations.filter(o=>pump(o.id)===state.order),coords=new Map();
 for(const o of ops){const[,k,step]=o.id.split('/');coords.set(o.id,k==='pump'?[650+Number(step.slice(4))*125,100]:[40+Number(step.slice(4))*112,20+['housing','rotor','flange'].indexOf(k)*73]);}
 const completed=stateAt(c,s,state.tick).completed;
 $('#bom').innerHTML=`<svg viewBox="0 0 960 250" role="group" aria-label="All sixteen recipe operations and matching assembly join for ${state.order}">${ops.flatMap(o=>o.predecessors.map(id=>{const [x,y]=coords.get(id),[a,b]=coords.get(o.id);return `<path d="M${x+84} ${y+22}H${a-16}V${b+22}H${a}" fill="none" stroke="${completed.has(id)?'#71947c':'#adbfc7'}" stroke-width="${completed.has(id)?2:1}"/>`;})).join('')}${ops.map(o=>{const[x,y]=coords.get(o.id),r=s.plan.find(r=>r.operation===o.id),active=r.start<=state.tick&&state.tick<r.end;return `<g data-operation="${o.id}" tabindex="0" role="button" aria-label="Inspect ${o.id}" transform="translate(${x} ${y})"><rect width="84" height="45" fill="${active?'#b9cfdc':completed.has(o.id)?'#c7d8ce':'#eff4f5'}" stroke="${state.operation===o.id?'#345d73':'#a8bdc7'}" stroke-width="${state.operation===o.id?3:1}"/><path d="M0 0H84" stroke="${colors[kind(o.id)]}" stroke-width="3"/><text x="7" y="17">${esc(o.id.split('/')[1])} ${Number(o.id.split('step')[1])+1}</text><text x="7" y="33" style="font-family:monospace;font-size:9px">${completed.has(o.id)?'DONE':active?'ACTIVE':n(r.start)+'m'} · ${r.machine}</text></g>`;}).join('')}<text x="650" y="78">MATCHED COMPONENTS → ASSEMBLY → QA</text><text x="650" y="195">Material genealogy is preserved.</text><text x="650" y="213">Processing ≠ physical shipment.</text></svg>`;
}
function renderGantt(c,s){
 const resources=Object.keys(state.resource==='worker'?c.problem.workers:c.problem.machines),left=65,right=1190,width=right-left,step=25,top=30,x=t=>left+width*t/c.problem.horizon;
 const nominal=data.cases['nominal-32'].plans.find(s=>s.id==='raw_reference'),showGhost=state.ghost&&c.operations===32;
 let bars='';
 resources.forEach((id,i)=>{const y=top+i*step;
  bars+=`<text x="0" y="${y+15}">${id}</text><path d="M${left} ${y+23}H${right}" stroke="#c0cfd6"/>`;
  if(showGhost)bars+=nominal.plan.filter(r=>r[state.resource]===id).map(r=>`<rect x="${x(r.start)}" y="${y+1}" width="${Math.max(1,x(r.end)-x(r.start))}" height="20" fill="none" stroke="#ae714d" stroke-dasharray="3 3"/>`).join('');
  bars+=s.plan.filter(r=>r[state.resource]===id).map(r=>{const end=state.resource==='worker'?r.attended_end:r.end;return `<rect data-operation="${r.operation}" tabindex="0" role="button" aria-label="Inspect ${r.operation} on ${id}" x="${x(r.start)}" y="${y+4}" width="${Math.max(2,x(end)-x(r.start))}" height="16" fill="${colors[kind(r.operation)]}" opacity="${pump(r.operation)===state.order?1:.24}" stroke="${r.operation===state.operation?'#213c4b':'none'}" stroke-width="2"><title>${r.operation} · ${r.start}–${end}m · ${r.worker}</title></rect>`;}).join('');
 });
 $('#gantt').innerHTML=`<svg viewBox="0 0 1210 ${top+resources.length*step+5}" aria-label="Every saved operation on ${state.resource} lanes">${Array.from({length:9},(_,i)=>{const t=i*c.problem.horizon/8;return `<path d="M${x(t)} 22V${top+resources.length*step}" stroke="#c5d2d8"/><text x="${x(t)}" y="12" text-anchor="middle">${n(t/60,1)}h</text>`;}).join('')}${bars}<path d="M${x(state.tick)} 20V${top+resources.length*step}" stroke="#345b70" stroke-width="1.5"/></svg>`;
 $('#ghost-note').textContent=showGhost?`Dashed: unchanged nominal plan. Under this scenario it is ${c.unchanged_nominal_plan_check.valid?'still feasible':'INVALID'}; it is a comparator, not a recovered schedule.`:'';
}
function renderEncoding(c){
 const a=data.cases['heat-outage-32'],b=data.cases['heat-lease-32'];
 const values=[['Outage · complete-model optimum',a.plans.find(s=>s.id==='raw_reference').check],['Replacement · original restricted pool',b.pool_reference.check??b.plans.find(s=>s.id==='pool_reference').check],['Replacement · enriched pool',b.plans.find(s=>s.id==='enriched_reference').check]];
 $('#recovery-comparison').innerHTML=values.map(([label,v])=>`<div class="comparison-row"><b>${label}</b><div class="track"><i class="${v.weighted_terminal_tardiness?'':'zero'}" style="width:${100*v.weighted_terminal_tardiness/45}%"></i></div><span><strong>${n(v.weighted_terminal_tardiness)}m</strong>weighted terminal tardiness</span></div>`).join('');
 const full=c.full_domain,pool=c.pool,cert=(full??pool)?.penalty_certificate;
 $('#encoding-detail').innerHTML=`<div class="encoding-note"><p><b>${esc(labels[c.id])}.</b> ${full?`The complete domain has ${n(full.variables)} bits and ${n(full.couplers)} couplers after exact support pruning.`:'A complete time-indexed QUBO was not materialized for this case.'} The candidate pool has ${n(pool?.variables)} bits / ${n(pool?.couplers)} couplers. It retains every operation, but restricts choices.</p><p>${cert?`<b>Checked-incumbent penalty:</b> ${n(cert.original_penalty)} → ${n(cert.penalty)} (${n(cert.ratio,1)}× smaller). This preserves feasible ground states using a checked heuristic witness, not the CP optimum.`:''} Native references are independent of the compiler. No VeloxQ output is shown.</p></div>`;
}
function updateClock(){const c=current(),s=plan();const choice=s.plan.find(r=>r.operation===state.operation);$('#math-choice').textContent=choice?`Selected schedule example: ${choice.operation} · ${choice.machine} · ${choice.worker} · start ${choice.start} min, finish ${choice.end} min.`:'';$('#time').value=state.tick;$('#clock').value=`${n(state.tick/60,1)} h`;$('#clock-label').textContent=`${n(state.tick)} / ${n(c.problem.horizon)} MIN`;renderFloor(c,s);renderCommitments(c,s);renderBOM(c,s);renderGantt(c,s);}
function renderCase(){
 const c=current();if(!c.plans.some(s=>s.id===state.method))state.method=c.plans.some(s=>s.id==='pool_reference')?'pool_reference':'list';
 $('#method').innerHTML=c.plans.map(s=>`<option value="${s.id}">${esc(s.name)}${s.optimal?(s.id==='raw_reference'?' · COMPLETE OPTIMUM':' · POOL OPTIMUM'):''}</option>`).join('');$('#method').value=state.method;
 const orders=[...new Set(c.problem.operations.map(o=>pump(o.id)))];if(!orders.includes(state.order))state.order=orders[0];
 $('#order').innerHTML=orders.map(o=>`<option>${o}</option>`).join('');$('#order').value=state.order;$('#scenario').value=c.id;
 state.operation=c.problem.operations.some(o=>o.id===state.operation)?state.operation:state.order+'/housing/step0';state.tick=Math.min(state.tick,c.problem.horizon);$('#time').max=c.problem.horizon;
 const s=plan(),exact=s.id==='raw_reference'&&s.optimal;
 const step=selectedStory(state.case,state.method);
 $('#story-tag').textContent=step?.tag??'EXPLORE THE SAVED STUDY';
 $('#story-title').textContent=step?.title??'Inspect the production plan.';
 $('#story-copy').textContent=step?.copy??labels[c.id]+'. Each view uses the selected checked schedule.';
 document.querySelectorAll('[data-story-step]').forEach(b=>{if(b.dataset.storyStep===step?.id)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
 $('#case-summary').innerHTML=`<strong class="result-number ${s.check.weighted_terminal_tardiness?'late':'ontime'}">${s.check.weighted_terminal_tardiness?n(s.check.weighted_terminal_tardiness):'On time'}${s.check.weighted_terminal_tardiness?'<small>min late</small>':''}</strong><span class="result-label">${s.check.weighted_terminal_tardiness?'Weighted terminal tardiness':'All modeled due dates met'}</span><p>Completion ${elapsed(s.check.makespan)}<br>${c.operations} mandatory operations</p>`;
 $('#schedule-scope').textContent=`${s.quality_label??(exact?'Complete-model optimum certified.':s.id==='pool_reference'?'Restricted-pool optimum; complete-model quality may differ.':'Checked saved schedule; no complete-model optimality claim.')} Whole-model objective interval: [${n(lower(c))}, ${n(Math.min(...c.plans.map(s=>s.check.objective)))}]. ${Object.keys(c.problem.workers).length} workers; ${Object.keys(c.problem.machines).length} available machines. Final inspection is not shipment.`;

 $('#compare-capacity').textContent=state.case==='heat-lease-32'?'Remove replacement capacity ↗':'Test replacement capacity ↗';renderEncoding(c);updateClock();
}
function showView(view){
 for(const b of document.querySelectorAll('[data-workspace-view]')){const on=b.dataset.workspaceView===view;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;}
 for(const p of document.querySelectorAll('.workspace-panel'))p.hidden=p.id!=='view-'+view;
}
const tabs=[...document.querySelectorAll('[data-workspace-view]')];
for(const b of tabs){b.addEventListener('click',()=>showView(b.dataset.workspaceView));b.addEventListener('keydown',e=>{
 const i=tabs.indexOf(b),j=e.key==='ArrowRight'?(i+1)%tabs.length:e.key==='ArrowLeft'?(i+tabs.length-1)%tabs.length:e.key==='Home'?0:e.key==='End'?tabs.length-1:null;
 if(j!==null){e.preventDefault();showView(tabs[j].dataset.workspaceView);tabs[j].focus();}
});}
$('#story-steps').innerHTML=storySteps.map((s,i)=>`<button class="story-step" data-story-step="${s.id}"><span>0${i+1}</span><span>${s.label}</span></button>`).join('');
for(const b of document.querySelectorAll('[data-story-step]'))b.addEventListener('click',()=>{
 const step=storySteps.find(s=>s.id===b.dataset.storyStep);state.case=step.case;state.method=step.method;state.tick=360;state.playing=false;$('#play').textContent='▶';$('#play').setAttribute('aria-label','Play saved schedule');showView('floor');renderCase();$('.workspace').scrollTop=0;
});
showView(location.hash==='#merit'?'analysis':'floor');
$('#scenario').innerHTML=Object.keys(data.cases).map(id=>`<option value="${id}">${labels[id]}</option>`).join('');
$('#scenario').addEventListener('change',e=>{state.case=e.target.value;state.method='raw_reference';renderCase();});
$('#method').addEventListener('change',e=>{state.method=e.target.value;renderCase();});
$('#order').addEventListener('change',e=>{state.order=e.target.value;state.operation=state.order+'/housing/step0';updateClock();});
$('#compare-capacity').addEventListener('click',()=>{state.case=state.case==='heat-lease-32'?'heat-outage-32':'heat-lease-32';state.method='raw_reference';renderCase();});
$('#time').addEventListener('input',e=>{state.tick=Number(e.target.value);updateClock();});
$('#ghost').addEventListener('change',e=>{state.ghost=e.target.checked;renderGantt(current(),plan());});
document.querySelectorAll('[data-resource]').forEach(b=>b.addEventListener('click',()=>{state.resource=b.dataset.resource;document.querySelectorAll('[data-resource]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));renderGantt(current(),plan());}));
document.addEventListener('click',e=>{
 const el=e.target.closest('[data-operation],[data-order],[data-machine],[data-case]');if(!el)return;
 if(el.dataset.case){state.case=el.dataset.case;state.method='raw_reference';return renderCase();}
 if(el.dataset.order){state.order=el.dataset.order;state.operation=state.order+'/housing/step0';}
 if(el.dataset.operation){state.operation=el.dataset.operation;state.order=pump(state.operation);}
 if(el.dataset.machine){const rows=plan().plan.filter(r=>r.machine===el.dataset.machine);const r=rows.find(r=>r.start<=state.tick&&state.tick<r.end)??rows.filter(r=>r.start>=state.tick).sort((a,b)=>a.start-b.start)[0]??rows[0];if(r){state.operation=r.operation;state.order=pump(r.operation);}}
 $('#order').value=state.order;updateClock();
});
document.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.closest('[data-operation],[data-machine]')){e.preventDefault();e.target.click();}});
let last=0;$('#play').addEventListener('click',()=>{state.playing=!state.playing;$('#play').textContent=state.playing?'Ⅱ':'▶';$('#play').setAttribute('aria-label',state.playing?'Pause saved schedule':'Play saved schedule');last=0;});
function animate(t){if(state.playing&&t-last>100){state.tick+=Math.max(3,current().problem.horizon/180);if(state.tick>current().problem.horizon)state.tick=0;updateClock();last=t;}requestAnimationFrame(animate);}requestAnimationFrame(animate);
$('#scaling').innerHTML=['nominal-32','nominal-64','nominal-128'].map(id=>{const c=data.cases[id];return `<tr><td><button data-case="${id}">${c.pumps} complete pumps ↗</button></td><td>${c.operations}</td><td>${n(c.initializer_cost.raw_assignment_candidates)}</td><td>${n(c.pool.variables)} / ${n(c.pool.couplers)}</td><td>${c.reference.status}${c.reference.optimal?' · certified':''}</td><td>${n(Math.min(...c.plans.map(s=>s.check.objective)))} / ${n(lower(c))}</td></tr>`;}).join('');
$('#provenance').textContent=Object.entries(data.source_sha256).map(([p,h])=>`${p}\nSHA-256 ${h}`).join('\n\n');
$('#packet-status').textContent='Four current cold SDK files: 818-bit deadline, 2,078-bit enriched (two penalty settings), and 2,499-bit complete optimization. Every literal coefficient and offset was audited. Earlier six-model cold/witness packets are retained separately. Service calls: 0.';
renderCase();
mountMerit(merit,(id,fresh)=>{
 state.case='heat-lease-32';
 if(fresh){const c=data.cases[state.case];c.plans=c.plans.filter(p=>p.id!==fresh.id);c.plans.push(fresh);checkedCase(c);}
 state.method=id;showView('floor');renderCase();$('.workspace').scrollTop=0;
});

if(data.annealing_pilot){
 const rows=data.annealing_pilot.rows;
 const groups=['original_bound','checked_incumbent_bound'].map(p=>{const runs=rows.filter(r=>r.penalty===p);return{label:p==='original_bound'?'Original safe bound':'Checked-incumbent safe bound',valid:runs.reduce((n,r)=>n+r.feasible_samples,0),samples:runs.reduce((n,r)=>n+r.returned_samples,0),improved:runs.filter(r=>r.retained_policy_objective<r.witness_objective).length};});
 $('#annealing-results').innerHTML=`<div class="table-wrap"><table><thead><tr><th>Penalty</th><th>Feasible returned samples</th><th>Runs improving the heuristic</th></tr></thead><tbody>${groups.map(g=>`<tr><td>${g.label}</td><td>${g.valid} / ${g.samples}</td><td>${g.improved} / ${rows.length/2}</td></tr>`).join('')}</tbody></table></div>`;
}
