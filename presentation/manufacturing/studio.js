import {colors,kind,pump,checkedCase,commitments,stateAt,readiness,lower,pumpJourney,nextPlanEvent} from './model.js';
import {renderFactoryScene,machineAvailability} from './factory-scene.js';
import {glyphBody} from '../stage2/factory-parts.js';
import {attachMeritPlans} from './merit-model.js';
import {mountMerit} from './merit.js';
import {storySteps,selectedStory,elapsed,observations} from './story.js';
const $=s=>document.querySelector(s),n=(x,d=0)=>Number(x).toLocaleString('en',{maximumFractionDigits:d});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={'nominal-32':'32 ops · nominal capacity','mill-down-32':'32 ops · milling capacity lost','rush-and-outage-32':'32 ops · expedited order + mill outage','lease-recovery-32':'32 ops · delayed replacement mill','crew-shortage-32':'32 ops · multi-skilled worker absent','heat-outage-32':'32 ops · furnace outage + tight deadlines','heat-lease-32':'32 ops · replacement furnace from 360m','nominal-64':'64 ops · four complete pumps','nominal-128':'128 ops · eight complete pumps'};
const data=await fetch('data.json').then(r=>{if(!r.ok)throw Error('Saved study unavailable');return r.json()});
const merit=await fetch('merit-data.json').then(r=>{if(!r.ok)throw Error('Merit study unavailable');return r.json()});
attachMeritPlans(data.cases,merit);
for(const c of Object.values(data.cases))checkedCase(c);
const state={case:'heat-outage-32',method:'raw_reference',order:'P02',operation:'P02/housing/step3',tick:360,machine:null,resource:'machine',playing:false,ghost:false};
const current=()=>data.cases[state.case],plan=()=>current().plans.find(s=>s.id===state.method)??current().plans[0];
function renderFloor(c,s){
 $('#floor').innerHTML=renderFactoryScene({c,s,tick:state.tick,selectedOperation:state.operation,selectedOrder:state.order,selectedMachine:state.machine,playing:state.playing});
 const snap=stateAt(c,s,state.tick),done=commitments(c,s).filter(r=>r.end<=state.tick).length;
 $('#world-status').innerHTML=`<span><strong>${snap.completed.size} / ${c.operations}</strong> operations finished</span><span><strong>${snap.active.length}</strong> processing</span><span><strong>${snap.attending.length}</strong> workers attending</span><span><strong>${done} / ${c.pumps}</strong> pumps inspected</span>`;
}
function renderJourney(c,s){
 const j=pumpJourney(c,s,state.order,state.tick);
 $('#pump-journey').innerHTML=`<div class="journey-heading"><div><p class="eyebrow">FOLLOW THE PUMP</p><h3>${j.order} <span>${j.completed} / ${j.total} steps</span></h3></div><svg class="pump-glyph" viewBox="0 0 36 36" aria-hidden="true">${glyphBody('pump')}</svg></div><p class="journey-phase">${j.phase}</p><div class="journey-progress" role="progressbar" aria-label="${j.order} completed operations" aria-valuemin="0" aria-valuemax="${j.total}" aria-valuenow="${j.completed}"><i style="width:${100*j.completed/j.total}%"></i></div>${j.components.map(part=>`<div class="component-row ${part.complete?'component-complete':''}"><svg viewBox="0 0 36 36" aria-hidden="true">${glyphBody(part.name)}</svg><div><div class="component-label"><strong>${part.name[0].toUpperCase()+part.name.slice(1)}</strong><span>${part.completed}/${part.steps.length}</span></div><p>${part.complete?'Component ready':part.active?`Processing on ${part.active.machine}`:`Next: ${part.next.machine} at ${elapsed(part.next.start)}`}</p><div class="recipe-dots">${part.steps.map((r,i)=>`<button class="recipe-step ${r.status}" data-operation="${r.operation}" aria-label="Inspect ${r.operation}: ${r.status}" aria-pressed="${r.operation===state.operation}" title="${part.name} step ${i+1} · ${r.machine} · ${r.status}">${r.status==='complete'?'✓':i+1}</button>`).join('')}</div></div></div>`).join('')}<div class="join-route">${[j.assembly,j.inspection].map((r,i)=>`<button data-operation="${r.operation}" class="join-step ${r.status}" aria-pressed="${r.operation===state.operation}"><span>${r.status==='complete'?'✓':i+4}</span>${i?'Final inspection':'Assemble pump'}<small>${r.status==='complete'?'Complete':r.status==='active'?'Processing':elapsed(r.start)}</small></button>`).join('')}</div><p class="journey-note">Progress follows the saved schedule. Inspection completion is not shipment.</p>`;
}
function renderCommitments(c,s){
 $('#commitments').innerHTML=commitments(c,s).map(r=>`<button class="commitment" data-order="${r.order}" aria-pressed="${r.order===state.order}"><b>${r.order}</b><span class="${r.tardy?'late':'ontime'}">${r.tardy?n(r.tardy)+'m late':'On-time plan'}</span><small>Due ${elapsed(r.due)} · inspection ${elapsed(r.end)}<br>${r.end<=state.tick?'✓ Final inspection complete':'○ Inspection not yet complete'}</small></button>`).join('');
 const r=s.plan.find(r=>r.operation===state.operation),o=c.problem.operations.find(o=>o.id===state.operation);
 $('#inspector').innerHTML=r?`<p class="eyebrow">SELECTED OPERATION</p><h3>${esc(state.operation.replaceAll('/',' / '))}</h3><dl><div><dt>Machine / hall</dt><dd>${r.machine} / ${r.hall}</dd></div><div><dt>Worker</dt><dd>${r.worker}</dd></div><div><dt>Processing</dt><dd>${n(r.start)}–${n(r.end)}m</dd></div><div><dt>Attendance ends</dt><dd>${n(r.attended_end)}m</dd></div><div><dt>Family</dt><dd>${esc(o.family)}</dd></div></dl><p class="reason">${esc(readiness(c,s,state.operation,state.tick))}</p><button class="seek-operation" data-seek="${r.start}">See this step at ${elapsed(r.start)} →</button>`:'';
}
function renderMachineInspector(c,s){
 const id=state.machine,av=machineAvailability(c.problem,id,state.tick),machine=c.problem.machines[id];
 const rows=s.plan.filter(r=>r.machine===id).sort((a,b)=>a.start-b.start),active=rows.find(r=>r.start<=state.tick&&state.tick<r.end),next=rows.find(r=>r.start>state.tick);
 $('#inspector').innerHTML=`<p class="eyebrow">SELECTED MACHINE</p><h3>${esc(id)}${machine?' / Hall '+esc(machine.hall):''}</h3><dl><div><dt>Current state</dt><dd>${active?'Processing':esc(av.label)}</dd></div><div><dt>Completed steps</dt><dd>${rows.filter(r=>r.end<=state.tick).length} / ${rows.length}</dd></div>${active?`<div><dt>Operation</dt><dd>${esc(active.operation)}</dd></div><div><dt>Attending now</dt><dd>${state.tick<active.attended_end?esc(active.worker):'No worker required'}</dd></div>`:''}</dl><p class="reason">${active?`Processing until minute ${active.end}. Attendance ends at ${active.attended_end}.`:!machine?'Unavailable for this complete planning window. No assignment can use this machine.':esc(av.detail)}${next?` Next saved assignment: ${esc(next.operation)} at ${elapsed(next.start)}.`:''}</p>${next?`<button class="seek-operation" data-seek="${next.start}">See the next assignment →</button>`:''}`;
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
  if(showGhost)bars+=nominal.plan.filter(r=>r[state.resource]===id).map(r=>{const end=state.resource==='worker'?r.attended_end:r.end;return `<rect x="${x(r.start)}" y="${y+1}" width="${Math.max(1,x(end)-x(r.start))}" height="20" fill="none" stroke="#ae714d" stroke-dasharray="3 3"/>`;}).join('');
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
function updateClock(){
 const active=document.activeElement,group=active?.closest?.('#floor,#commitments,#bom,#gantt,#pump-journey,#inspector')?.id;
 const key=group?['operation','order','machine','seek'].find(k=>active.dataset[k]):null,value=key?active.dataset[key]:null;
 const c=current(),s=plan(),choice=s.plan.find(r=>r.operation===state.operation);
 $('#math-choice').textContent=choice?`Selected schedule example: ${choice.operation} · ${choice.machine} · ${choice.worker} · start ${choice.start} min, finish ${choice.end} min.`:'';
 $('#time').value=state.tick;$('#clock').value=elapsed(state.tick);$('#clock-label').textContent=`SAVED PLAN · ${state.playing?'PLAYING':'PAUSED'}`;$('#next-event').disabled=nextPlanEvent(c,s,state.tick)===null;
 renderFloor(c,s);renderCommitments(c,s);if(state.machine)renderMachineInspector(c,s);renderJourney(c,s);renderBOM(c,s);renderGantt(c,s);
 if(group&&key){
  const next=[...document.getElementById(group).querySelectorAll(`[data-${key}]`)].find(el=>el.dataset[key]===value);
  const fallback=state.machine?[...$('#floor').querySelectorAll('[data-machine]')].find(el=>el.dataset.machine===state.machine):[...$('#pump-journey').querySelectorAll('[data-operation]')].find(el=>el.dataset.operation===state.operation);
  (next??fallback)?.focus({preventScroll:true});
 }
}
function renderCase(){
 setPlaying(false);state.machine=null;
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
 $('#world-state').textContent=step?['The furnace outage','Bring in spare capacity','The missing choices','The recovered deadline'][storySteps.indexOf(step)]:'Explore the selected plan';
 $('#story-observation').textContent=observations[step?.id]??'Select a machine or a recipe step to inspect its actual planned assignment. Playback changes the view, not the schedule.';
 $('#next-story').textContent=step&&storySteps.indexOf(step)<3?'Next decision →':'See the model & results →';
 document.querySelectorAll('[data-story-step]').forEach(b=>{if(b.dataset.storyStep===step?.id)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
 $('#case-summary').innerHTML=`<strong class="result-number ${s.check.weighted_terminal_tardiness?'late':'ontime'}">${s.check.weighted_terminal_tardiness?n(s.check.weighted_terminal_tardiness):'On-time plan'}${s.check.weighted_terminal_tardiness?'<small>min late</small>':''}</strong><span class="result-label">${s.check.weighted_terminal_tardiness?'Weighted terminal tardiness':'Predicted from this saved schedule'}</span><p>Completion ${elapsed(s.check.makespan)}<br>${c.operations} mandatory operations</p>`;
 $('#run-notice').textContent=s.run_notice??'';$('#run-notice').hidden=!s.run_notice;
 $('.story-facts').hidden=!['heat-outage-32','heat-lease-32'].includes(state.case);
 $('#schedule-scope').textContent=`${s.quality_label??(exact?'Complete-model optimum certified.':s.id==='pool_reference'?'Restricted-pool optimum; complete-model quality may differ.':'Checked saved schedule; no complete-model optimality claim.')} Whole-model objective interval: [${n(lower(c))}, ${n(Math.min(...c.plans.map(s=>s.check.objective)))}]. ${Object.keys(c.problem.workers).length} workers; ${Object.keys(c.problem.machines).length} modeled machines. Final inspection is not shipment.`;

 $('#compare-capacity').textContent=state.case==='heat-lease-32'?'Remove replacement capacity ↗':'Test replacement capacity ↗';renderEncoding(c);updateClock();
}
function showView(view,focus=false){
 for(const b of document.querySelectorAll('[data-workspace-view]')){const on=b.dataset.workspaceView===view;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;}
 for(const p of document.querySelectorAll('.workspace-panel'))p.hidden=p.id!=='view-'+view;
 if(focus)document.querySelector('#tab-'+view).focus({preventScroll:true});
}
function focusWorld(focused){document.body.classList.toggle('factory-focused',focused);$('#focus-world').setAttribute('aria-pressed',String(focused));$('#focus-world').textContent=focused?'Exit focus ⤡':'Focus factory ⤢';}
$('#focus-world').addEventListener('click',()=>focusWorld(!document.body.classList.contains('factory-focused')));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('factory-focused')){focusWorld(false);$('#focus-world').focus();}});
const tabs=[...document.querySelectorAll('[data-workspace-view]')];
for(const b of tabs){b.addEventListener('click',()=>showView(b.dataset.workspaceView));b.addEventListener('keydown',e=>{
 const i=tabs.indexOf(b),j=e.key==='ArrowRight'?(i+1)%tabs.length:e.key==='ArrowLeft'?(i+tabs.length-1)%tabs.length:e.key==='Home'?0:e.key==='End'?tabs.length-1:null;
 if(j!==null){e.preventDefault();showView(tabs[j].dataset.workspaceView);tabs[j].focus();}
});}
$('#story-steps').innerHTML=storySteps.map((s,i)=>`<button class="story-step" data-story-step="${s.id}"><span>0${i+1}</span><span>${s.label}</span></button>`).join('');
function selectStory(step){
 state.case=step.case;state.method=step.method;state.tick=360;state.operation=state.order+'/housing/step3';setPlaying(false);showView('floor');renderCase();$('.workspace').scrollTop=0;
}
for(const b of document.querySelectorAll('[data-story-step]'))b.addEventListener('click',()=>selectStory(storySteps.find(s=>s.id===b.dataset.storyStep)));
$('#next-story').addEventListener('click',()=>{const i=storySteps.indexOf(selectedStory(state.case,state.method));if(i>=0&&i<3){selectStory(storySteps[i+1]);document.querySelector(`[data-story-step="${storySteps[i+1].id}"]`).focus({preventScroll:true});}else{showView('analysis',true);$('.workspace').scrollTop=0;}});
showView(location.hash==='#merit'?'analysis':'floor');
$('#scenario').innerHTML=Object.keys(data.cases).map(id=>`<option value="${id}">${labels[id]}</option>`).join('');
$('#scenario').addEventListener('change',e=>{state.case=e.target.value;state.method='raw_reference';setPlaying(false);renderCase();});
$('#method').addEventListener('change',e=>{state.method=e.target.value;setPlaying(false);renderCase();});
$('#order').addEventListener('change',e=>{state.machine=null;state.order=e.target.value;state.operation=state.order+'/housing/step0';updateClock();});
$('#compare-capacity').addEventListener('click',()=>{state.case=state.case==='heat-lease-32'?'heat-outage-32':'heat-lease-32';state.method='raw_reference';renderCase();});
$('#time').addEventListener('input',e=>{state.tick=Number(e.target.value);setPlaying(false);updateClock();});
$('#ghost').addEventListener('change',e=>{state.ghost=e.target.checked;renderGantt(current(),plan());});
document.querySelectorAll('[data-resource]').forEach(b=>b.addEventListener('click',()=>{state.resource=b.dataset.resource;document.querySelectorAll('[data-resource]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));renderGantt(current(),plan());}));
document.addEventListener('click',e=>{
 const el=e.target.closest('[data-operation],[data-order],[data-machine],[data-case],[data-seek]');if(!el)return;
 if(el.dataset.seek!==undefined){state.tick=Number(el.dataset.seek);setPlaying(false);updateClock();return;}
 if(el.dataset.case){state.case=el.dataset.case;state.method='raw_reference';return renderCase();}
 if(el.dataset.order){state.machine=null;state.order=el.dataset.order;state.operation=state.order+'/housing/step0';}
 if(el.dataset.operation){state.machine=null;state.operation=el.dataset.operation;state.order=pump(state.operation);}
 if(el.dataset.machine){state.machine=el.dataset.machine;const rows=plan().plan.filter(r=>r.machine===el.dataset.machine);const r=rows.find(r=>r.start<=state.tick&&state.tick<r.end)??rows.filter(r=>r.start>=state.tick).sort((a,b)=>a.start-b.start)[0]??rows[0];if(r){state.operation=r.operation;state.order=pump(r.operation);}}
 $('#order').value=state.order;updateClock();
});
document.addEventListener('keydown',e=>{const control=e.target.closest?.('[data-operation],[data-machine]');if((e.key==='Enter'||e.key===' ')&&control instanceof SVGElement){e.preventDefault();control.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
let last=0;
function setPlaying(playing){state.playing=playing;$('#play').textContent=playing?'Ⅱ':'▶';$('#play').setAttribute('aria-label',playing?'Pause saved schedule':'Play saved schedule');last=0;}
$('#play').addEventListener('click',()=>{if(!state.playing&&state.tick>=plan().check.makespan)state.tick=0;setPlaying(!state.playing);updateClock();});
$('#restart').addEventListener('click',()=>{state.tick=0;setPlaying(false);updateClock();});
$('#next-event').addEventListener('click',()=>{const next=nextPlanEvent(current(),plan(),state.tick);if(next!==null)state.tick=next;setPlaying(false);updateClock();});
function animate(t){
 if(state.playing){if(!last)last=t;const delta=t-last;if(delta>=100){state.tick=Math.min(plan().check.makespan,state.tick+Math.min(delta,300)*Number($('#speed').value)/1000);last=t;if(state.tick>=plan().check.makespan)setPlaying(false);updateClock();}}
 requestAnimationFrame(animate);
}requestAnimationFrame(animate);
$('#scaling').innerHTML=['nominal-32','nominal-64','nominal-128'].map(id=>{const c=data.cases[id];return `<tr><td><button data-case="${id}">${c.pumps} complete pumps ↗</button></td><td>${c.operations}</td><td>${n(c.initializer_cost.raw_assignment_candidates)}</td><td>${n(c.pool.variables)} / ${n(c.pool.couplers)}</td><td>${c.reference.status}${c.reference.optimal?' · certified':''}</td><td>${n(Math.min(...c.plans.map(s=>s.check.objective)))} / ${n(lower(c))}</td></tr>`;}).join('');
$('#provenance').textContent=Object.entries(data.source_sha256).map(([p,h])=>`${p}\nSHA-256 ${h}`).join('\n\n');
$('#packet-status').textContent='Four current cold SDK files: 818-bit deadline, 2,078-bit enriched (two penalty settings), and 2,499-bit complete optimization. Every literal coefficient and offset was audited. Earlier six-model cold/witness packets are retained separately. Service calls: 0.';
renderCase();
mountMerit(merit,(id,fresh)=>{
 state.case='heat-lease-32';
 if(fresh){const c=data.cases[state.case];c.plans=c.plans.filter(p=>p.id!==fresh.id);c.plans.push(fresh);checkedCase(c);}
 state.method=id;showView('floor',true);renderCase();$('.workspace').scrollTop=0;
});

if(data.annealing_pilot){
 const rows=data.annealing_pilot.rows;
 const groups=['original_bound','checked_incumbent_bound'].map(p=>{const runs=rows.filter(r=>r.penalty===p);return{label:p==='original_bound'?'Original safe bound':'Checked-incumbent safe bound',valid:runs.reduce((n,r)=>n+r.feasible_samples,0),samples:runs.reduce((n,r)=>n+r.returned_samples,0),improved:runs.filter(r=>r.retained_policy_objective<r.witness_objective).length};});
 $('#annealing-results').innerHTML=`<div class="table-wrap"><table><thead><tr><th>Penalty</th><th>Feasible returned samples</th><th>Runs improving the heuristic</th></tr></thead><tbody>${groups.map(g=>`<tr><td>${g.label}</td><td>${g.valid} / ${g.samples}</td><td>${g.improved} / ${rows.length/2}</td></tr>`).join('')}</tbody></table></div>`;
}
