import {CASES,PHASES,RESOURCES,clock,activeOperations,allOperations,workerOperation,offline,deliveredMeals,packedMeals,requestedMeals,mealOrders,selectedPrograms,bitDescription,activateRun,discardedComponents} from './model.js';
import {kitchenSVG,prepareScene,renderWorker,renderKitchen} from './scene.js';
import {buildWorkerTrack,workerPoseAt} from './worker-motion.js';
import {decodedActions,stationState,withAlternative} from './kitchen-state.js';
import {decisionSteps,decisionComparison} from './decision-story.js';
import {productionSequence,playbackEnd,componentStatus,orderName,adjacentEvent,eventDescription} from './production-sequence.js';

const $=s=>document.querySelector(s),reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let data,current,referenceCase,fixture,inspected=-1,time=20,playing=false,looping=true,speed=1,lastFrame=0,lastDraw=0,workerTracks=new Map();
let sequence,timelineView='batch',endHold=0;
let decodeTour=null,decodeStage=0,decodeElapsed=0,decodeAuto=!reduced,vectorBeforeTour=false;
$('#kitchen').innerHTML=kitchenSVG();
const artReady=prepareScene($('#kitchen'));
const firstChoice=()=>current.options.findIndex((_,i)=>current.bits[i]===1);
const program=()=>inspected===-1?current.snapshot.fixed_batches[0]:current.options[inspected];
const label=o=>o.recovery?'Recovery clean':`${PHASES[o.kind]} ${current.plan.batches.find(b=>b.id===o.batch_id)?.menu??''}`;
const tuple=m=>['U','W','B','R'].map(k=>m[k]).join(', ');
const repo=path=>`https://github.com/Kolo-Naukowe-Axion/qhackathon26/blob/main/${path}`;

function drawBits(){
  $('#bits').style.setProperty('--n',current.bits.length);
  $('#bits').innerHTML=current.bits.map((x,i)=>`<button class="bit ${x?'is-selected':''} ${i===inspected?'is-inspected':''} ${i>=current.options.length?'register':''}" data-bit="${i}" aria-label="Inspect x${i+1}, value ${x}. ${bitDescription(current,i)}"><b>${x}</b><small>x${i+1}</small></button>`).join('');
  $('#vector-status').textContent=current.bits.length?`${selectedPrograms(current).length} ${selectedPrograms(current).length===1?'batch':'batches'} · ${current.bits.length} bits incl. idle`:'Raw scheduling reference · no QUBO bitstring';
  $('#vector-toggle').disabled=!current.bits.length;
}
function drawTranslation(){
  const chosen=selectedPrograms(current);
  $('#decoded-strip').innerHTML=chosen.length?chosen.map(p=>{
    const i=current.options.indexOf(p);
    return `<button class="solution-token" data-program="${i}">x${i+1}=1 <small>${p.menu} · ${p.yield_lots*current.instance.lot_size} portions</small></button>`;
  }).join('<span class="decode-arrow">+</span>'):'<strong>Checked schedule → prep → cook → pack → handover</strong>';
  const i=inspected>=0&&current.options[inspected]?inspected:firstChoice(),actions=decodedActions(current,i),p=current.options[i];
  $('#trace-content').innerHTML=`<h2>Programs become timed instructions.</h2><p class="trace-bridge">${chosen.length} new batch programs are selected together. Each sets <strong>when, where, who and how many</strong>. Menu A is already committed.</p><div class="recipe-rule"><span>MAIN + SIDE = COMPLETE MEAL</span><p>Both courses must be packed before the same departure. Unpaired components are discarded.</p></div>${p?`<div class="decode-equation"><b>x${i+1}=1</b><span>→</span><strong>Menu ${p.menu} · ${p.yield_lots*current.instance.lot_size} component portions</strong></div><div class="decoded-actions">${actions.map(a=>`<button class="decoded-action" data-seek="${a.start}" data-resource="${a.resource}"><span>↗</span><div><b>${clock(a.start)} · ${PHASES[a.kind]}</b><small>${a.resource} · ${a.worker} · ${a.end-a.start}m</small></div></button>`).join('')}</div>`:'<p class="trace-bridge">Inspect a batch or an operation on the timeline for its recorded instructions.</p>'}<p class="trace-parallel">Packing and cleaning can overlap when they use different workers and equipment. Playback follows a retained plan.</p>`;
  const comp=decisionComparison(current,referenceCase);
  $('#tradeoff-tab').disabled=!comp;
  $('#tradeoff-content').innerHTML=comp?`<h2>${comp.title}</h2><p class="comparison-copy">${comp.copy}</p><table class="comparison-table"><thead><tr><th>Final outcome</th><th>This plan</th><th>${current.manual?'Saved plan':'Skip batch'}</th></tr></thead><tbody>${[['Complete meals',comp.current.served,comp.other.served],['Unserved meals',comp.current.missed,comp.other.missed],['Discarded component portions',comp.current.waste,comp.other.waste],['New batches',comp.current.metrics.B,comp.other.metrics.B]].map(row=>`<tr><th>${row[0]}</th><td>${row[1]}</td><td>${row[2]}</td></tr>`).join('')}</tbody></table><p class="comparison-constraint">${comp.constraint}</p><button class="pixel-button" data-alternative="${comp.other.index}">${current.manual?'Restore saved plan':'Replay with this batch skipped'} ↗</button><p class="comparison-source">This intervention was decoded and independently checked during export. It is not another solver run.</p>`:'<p>No checked intervention is available for this view.</p>';
}
function drawInspector(){
  if(inspected===-2){
    const recovery=current.plan.recovery_operations[0];
    $('#bit-tag').textContent='MANDATORY RECOVERY';$('#program-title').textContent=`${recovery.resource} post-repair clean`;
    $('#program-copy').textContent='The cooker stays unavailable for new cooking until this required clean finishes, even when it was idle during the outage.';
    $('#program-phases').innerHTML=`<button class="phase" data-program-seek="${recovery.start}"><time>${clock(recovery.start)}</time><div><b>Recovery clean</b><small>${recovery.resource} · ${recovery.worker} · ${recovery.end-recovery.start}m</small></div></button>`;
    $('#program-note').textContent=`Repair ends ${clock(recovery.repair_end)}. W2 first finishes the committed batch clean, then cleans C2. Earliest C2 cooking: ${clock(recovery.end)}.`;
    $('#try-program').hidden=true;$('#restore-plan').hidden=!current.manual;$('#alternative-result').textContent='';drawTimeline();return;
  }
  const p=program(),chosen=inspected===-1||current.bits[inspected]===1;
  $('#bit-tag').textContent=inspected===-1?'COMMITTED':`x${inspected+1} = ${current.bits[inspected]}`;
  $('#program-title').textContent=p?`Menu ${p.menu} · ${p.yield_lots*current.instance.lot_size} portions`:'Leave this anchor idle';
  $('#program-copy').textContent=p?(inspected===-1?'Already started. Its remaining operations stay in every continuation.':chosen?'Selected batch program: quantity, equipment, crew and times.':'An offered alternative. The notebook previews it; the saved schedule still runs.'):'An idle data bit selects no new program in its one-hot group. It does not represent missed demand directly.';
  const actions=decodedActions(current,inspected);
  $('#program-phases').innerHTML=actions.map(a=>`<button class="phase" data-program-seek="${a.start}" data-resource="${a.resource}"><time>${clock(a.start)}</time><div><b>${PHASES[a.kind]}</b><small>${a.resource} · ${a.worker} · ${a.end-a.start}m</small></div></button>`).join('');
  $('#program-note').textContent=p?`Reserves: ${p.allocation_order.join(', ')}. Component reservations become meals only when the matching course is also delivered.`:bitDescription(current,inspected);
  $('#try-program').hidden=!referenceCase.alternatives.some(a=>a.index===inspected)||current.manual;
  $('#try-program').textContent=`Skip x${inspected+1} and replay`;
  $('#restore-plan').hidden=!current.manual;
  $('#alternative-result').textContent=current.manual?'Checked manual intervention · no optimizer was called.':'';
  drawTimeline();
}
function drawTimeline(){
  const H=playbackEnd(current),ops=allOperations(current);
  const bar=o=>`<button class="op ${o.recovery?'recovery':o.kind} ${current.snapshot.fixed_batches.some(b=>b.id===o.batch_id)?'committed':''}" data-operation="${o.id}" title="${clock(o.start)}–${clock(o.end)} · ${label(o)} · ${o.resource} · ${o.worker}${o.attended_end<o.end?` attended until ${clock(o.attended_end)}`:''}" aria-label="Follow ${label(o)}, ${clock(o.start)} to ${clock(o.end)}, ${o.resource}, ${o.worker}" style="left:${o.start/H*100}%;width:${(o.end-o.start)/H*100}%">${o.recovery?'Recovery clean':o.kind==='cook'?`Cook ${o.resource}`:PHASES[o.kind]}</button>`;
  const unavailable=id=>current.snapshot.outages.filter(o=>o.resource===id).map(o=>`<span class="outage" title="${id} under repair ${clock(o.start)}–${clock(o.end)}" style="left:${o.start/H*100}%;width:${(o.end-o.start)/H*100}%">REPAIR</span>`).join('')+(current.plan.recovery_operations??[]).filter(o=>o.resource===id&&o.start>o.repair_end).map(o=>`<span class="outage awaiting-clean" title="${id} waiting for mandatory clean ${clock(o.repair_end)}–${clock(o.start)}" style="left:${o.repair_end/H*100}%;width:${(o.start-o.repair_end)/H*100}%">WAIT</span>`).join('');
  const rows=timelineView==='batch'?sequence.cooking.map(row=>`<div class="resource-row batch-row"><span class="resource-label">${row.label}<small>${row.batch.yield_lots*current.instance.lot_size} portions${row.committed?' · started':''}</small></span>${row.operations.map(bar).join('')}</div>`).join('')+(current.plan.recovery_operations?.length?`<div class="resource-row batch-row"><span class="resource-label">Recovery<small>required clean</small></span>${[...new Set(current.plan.recovery_operations.map(o=>o.resource))].map(unavailable).join('')}${ops.filter(o=>o.recovery).map(bar).join('')}</div>`:''):RESOURCES.map(id=>`<div class="resource-row equipment-row"><span class="resource-label">${id}</span>${unavailable(id)}${ops.filter(o=>o.resource===id).map(bar).join('')}</div>`).join('');
  const departures=mealOrders(current).map(m=>`<button class="handover-marker ${m.handed?'':'unfilled'}" data-departure="${m.departure}" title="${orderName(m)} · ${clock(m.departure)} · ${m.handed?'complete meals depart':'incomplete order'}" aria-label="Follow ${orderName(m)} departure at ${clock(m.departure)}" style="left:${m.departure/H*100}%">${orderName(m).replace('Order ','').replace('Urgent order','!')}</button>`).join('');
  $('#timeline').innerHTML=`<div class="timeline-grid"><div class="ruler">${Array.from({length:Math.floor(H/20)+1},(_,i)=>`<span style="left:${i*20/H*100}%">${clock(i*20)}</span>`).join('')}</div>${rows}<div class="departure-row"><span class="resource-label">Departures</span>${departures}</div><div id="cursor" class="cursor"></div></div>`;
  $('#schedule-heading').textContent=timelineView==='batch'?'SCHEDULE BY BATCH':'SCHEDULE BY EQUIPMENT';
  $('#batch-view').setAttribute('aria-pressed',String(timelineView==='batch'));$('#equipment-view').setAttribute('aria-pressed',String(timelineView==='equipment'));
}
function drawSequence(){
  $('#production-sequence').scrollTop=0;
  const meals=mealOrders(current),count=meals.length;
  $('#sequence-intro').textContent=`${count*current.instance.lot_size} meals · ${count} orders · main + side`;
  $('#cooking-order').innerHTML=sequence.cooking.map((r,i)=>`<li><button data-sequence-operation="${r.cook.id}" data-start="${r.cook.start}" data-end="${r.cook.end}"><span class="queue-number">${i+1}</span><span><b>${r.label}${r.committed?' · already started':''}</b><small>${clock(r.cook.start)}–${clock(r.cook.end)} · ${r.cook.resource} · ${r.batch.yield_lots*current.instance.lot_size} portions</small></span><i>↗</i></button></li>`).join('');
  $('#packing-order').innerHTML=sequence.packing.map((r,i)=>`<li><button data-sequence-operation="${r.operation.id}" data-start="${r.operation.start}" data-end="${r.operation.end}"><span class="queue-number">${i+1}</span><span><b>${r.label} → ${r.order}</b><small>${clock(r.operation.start)}–${clock(r.operation.end)} · ${r.operation.resource} / ${r.operation.worker}</small></span><i>↗</i></button></li>`).join('');
  const inversion=sequence.inversion;
  if(inversion){
    const a=inversion.preparedFirst,b=inversion.cookedFirst;
    const targets=[...new Set(sequence.packing.filter(r=>r.operation.batch_id===b.batch.id&&r.meal).map(r=>`${r.order} ${clock(r.meal.departure)}`))];
    const overlaps=sequence.cooking.filter(r=>r.batch.id!==b.batch.id&&r.cook.start<b.cook.end&&b.cook.start<r.cook.end);
    $('#sequence-insight').innerHTML=`<summary>${a.batch.menu} preps first. ${b.batch.menu} cooks first.</summary><p>${b.label} supplies ${targets.join(' + ')}. ${overlaps.length?`Its cooking overlaps ${overlaps.map(r=>r.label).join(' + ')}.`:`It cooks ${clock(b.cook.start)}–${clock(b.cook.end)} on ${b.cook.resource}.`}</p>`;
  }else $('#sequence-insight').innerHTML='<summary>How to read this sequence</summary><p>Each batch keeps its recipe order. The timeline shows when separate batches overlap, and when cleaning frees a cooker.</p>';
}
function updateSequence(){
  $('#sequence-now').textContent=`NOW · ${clock(time)}`;
  $('#sequence-active').textContent=activeOperations(current,time).map(o=>`${label(o)} / ${o.resource}`).join(' + ')||'No operation running';
  const next=adjacentEvent(sequence,time,1);
  $('#next-event-label').textContent=time>=sequence.end?'Last departure reached':`${clock(next)} · ${eventDescription(current,next)}`;
  $('#next-event-label').title=$('#next-event-label').textContent;
  $('#previous-event').disabled=time<=0;$('#next-event').disabled=time>=sequence.end;
  for(const list of [$('#cooking-order'),$('#packing-order')]){
    let nextMarked=false;
    for(const el of list.querySelectorAll('[data-sequence-operation]')){
      const start=Number(el.dataset.start),end=Number(el.dataset.end),active=start<=time&&time<end;
      el.classList.toggle('is-running',active);el.classList.toggle('is-complete',time>=end);
      const queued=start>time&&!nextMarked;el.classList.toggle('is-next',queued);if(queued)nextMarked=true;
      el.setAttribute('aria-current',active?'step':'false');
    }
  }
  for(const el of $('#timeline').querySelectorAll('[data-operation]')){
    const op=allOperations(current).find(o=>o.id===el.dataset.operation);
    el.classList.toggle('is-running',op.start<=time&&time<op.end);
  }
}
function updateLayout(){
  document.documentElement.style.setProperty('--plan-top',`${Math.ceil($('.decision-strip').getBoundingClientRect().bottom+10)}px`);
  document.documentElement.style.setProperty('--plan-bottom',`${Math.ceil(innerHeight-$('.replay').getBoundingClientRect().top+10)}px`);
}
function openSequence(open=true){
  if(open){openInspector(false);openTrace(false);}
  document.body.classList.toggle('sequence-open',open);$('#sequence-toggle').setAttribute('aria-expanded',String(open));
}
function followOperation(id){
  const op=allOperations(current).find(o=>o.id===id);if(!op)return;
  seek(op.start,op.recovery?-2:current.options.findIndex(p=>p.id===op.batch_id));
  for(const resource of RESOURCES)$(`#station-${resource}`).classList.toggle('is-focused',resource===op.resource);
}
function updateWorkers(){
  ['W1','W2','W3'].map(id=>({el:$(`#chef-${id}`),pose:workerPoseAt(workerTracks.get(id),time)})).sort((a,b)=>a.pose.y-b.pose.y).forEach(({el,pose})=>{renderWorker(el,pose);$('#workers').append(el);});
}
function updateDynamic(){
  if(!current)return;
  renderKitchen(current,time);updateWorkers();
  $('#time').textContent=clock(time);$('#scene-clock').textContent=clock(time);$('#scrubber').value=time;
  $('#cursor').style.left=`${time/playbackEnd(current)*100}%`;
  updateSequence();
  const active=activeOperations(current,time),orders=mealOrders(current),chosen=selectedPrograms(current);
  $('#event-title').textContent=time<current.snapshot.current_time?'Before the decision':active.length?active.map(label).join(' + '):'Between kitchen operations';
  $('#event-copy').textContent=active.length?active.map(o=>`${o.resource} · ${time<o.attended_end?o.worker:'unattended'}`).join(' / '):CASES[current.id].event;
  $('#meal-count').textContent=`${deliveredMeals(current,time)} / ${requestedMeals(current)} served`;
  const waste=discardedComponents(current,time);
  $('#waste-count').textContent=waste;
  $('#waste-count').classList.toggle('has-waste',waste>0);
  $('#orders').innerHTML=orders.map(m=>{
    const hidden=time<m.revealed,departed=time>=m.departure,ready=m.ready_at!==null&&time>=m.ready_at;
    const status=hidden?'unrevealed':departed?(m.handed?'served':'missed'):ready?'ready to leave':m.handed?'scheduled':'incomplete';
    const courses=['main','side'].map(course=>componentStatus(current,m,course,time));
    return `<button class="order ${ready?'ready':''} ${departed&&m.handed?'delivered':''} ${departed&&!m.handed?'missed':''}" data-meal="${m.id}" aria-label="Follow ${orderName(m)} departure at ${clock(m.departure)}"><div class="order-title"><b>${hidden?'Not yet revealed':`${orderName(m)} · ${current.instance.lot_size} meals`}</b><span>${status}</span></div><small class="order-departure">LEAVES ${clock(m.departure)}${m.revealed?' · urgent':''}</small>${hidden?'':courses.map(course=>`<span class="order-course ${course.state}"><b>${course.label}</b><span>${course.status}</span></span>`).join('')}</button>`;
  }).join('');
  for(const id of RESOURCES){
    const el=$(`#station-${id}`),state=stationState(current,id,time),op=state.operation;
    el.classList.toggle('active',!!op);el.classList.toggle('cooking',op?.kind==='cook');el.classList.toggle('offline',offline(current,id,time)||state.mode==='awaiting_clean');
    el.classList.toggle('committed',!!op&&current.snapshot.fixed_batches.some(b=>b.id===op.batch_id));
    $(`#status-${id}`).textContent=state.mode==='offline'?'Under repair':state.mode==='awaiting_clean'?'Waiting for recovery clean':op?`${op.recovery?'Recovery clean':label(op)} · ${state.remaining}m`:state.next?`Next ${clock(state.next.start)}`:'Clear';
  }
  $('#crew-list').innerHTML=['W1','W2','W3'].map(id=>{const op=workerOperation(current,id,time);return `<div class="crew-row"><span class="crew-dot"></span><span>${id} · ${id==='W1'?'Prep / pack':id==='W2'?'Cleaning':'Cooking'}</span><small>${op?`${label(op)} / ${op.resource}`:'Available'}</small></div>`;}).join('');
  $('#live-state').textContent=decodeTour?'DECODING':playing?'PLAYING':'PAUSED';
  $('#action-link').textContent=`${packedMeals(current,time)} complete meals packed · ${discardedComponents(current,time)} component portions discarded`;
  document.querySelectorAll('[data-bit]').forEach(el=>{const i=Number(el.dataset.bit);el.classList.toggle('executing',!!current.bits[i]&&!!current.options[i]&&active.some(o=>o.batch_id===current.options[i].id));});
  $('#kitchen').setAttribute('aria-label',`Kitchen at ${clock(time)}. ${active.map(label).join('. ')}. ${deliveredMeals(current,time)} complete meals served.`);
  if(decodeTour)renderDecode();
}
function provenance(){
  const kind=current.manual?'MANUAL INTERVENTION':current.key==='qaoa'?'QAOA SIMULATOR':current.label.toUpperCase();
  $('#proof').textContent=`${kind} · U/W/B/R = (${tuple(current.metrics)}) · CHECKED`;
  $('#run-scope').textContent=`${current.manual?'Checked skip-batch intervention · not a solver result':`${current.key==='raw'?'Independent scheduling reference · full declared physical grid':current.description} · ${current.reference_status}`}`;
  $('#source').innerHTML=`<a href="${repo(current.source.path)}" target="_blank" rel="noopener">${current.source.path} ↗</a><br>${current.manual?'Checked manual intervention derived from this source':current.execution_kind}${current.shots&&!current.manual?` · ${current.valid_shots}/${current.shots} valid shots · displayed sample count ${current.count}`:''}`;
  $('#hash').textContent=`Source SHA-256: ${current.source.sha256}${current.bundle_sha256?`\nBundle SHA-256: ${current.bundle_sha256}`:''}`;
  $('#scope-note').textContent=current.id==='CELL'?'All 32 local programs of the declared small grid are included. QAOA and both simple controls attain the optimum.':'This QAOA plan comes from changing, restricted portfolios. Its result trails the full-grid classical reference. Compare methods using the selector above.';
}
function loadCase(id,key='qaoa'){
  if(!data)return;
  endHold=0;
  for(const resource of RESOURCES)$(`#station-${resource}`).classList.remove('is-focused');
  cancelDecode();fixture=data.cases.find(c=>c.id===id);referenceCase=activateRun(fixture,key);current=referenceCase;sequence=productionSequence(current);time=current.snapshot.current_time;inspected=firstChoice();
  $('#scenario').disabled=false;$('#method').disabled=false;$('#scenario').value=id;$('#method').innerHTML=fixture.runs.map(r=>`<option value="${r.key}">${r.label}</option>`).join('');$('#method').value=key;
  $('#scrubber').max=playbackEnd(current);$('#end-time').textContent=`/ ${clock(playbackEnd(current))}`;
  workerTracks=new Map(['W1','W2','W3'].map(id=>[id,buildWorkerTrack(current,id)]));
  drawBits();drawInspector();drawTranslation();drawSequence();provenance();updateDynamic();updateLayout();
}
function setPlaying(value){playing=value;document.body.classList.toggle('is-paused',!value);$('#play').innerHTML=value?'Ⅱ <span>Pause</span>':'▶ <span>Play</span>';$('#play').setAttribute('aria-label',value?'Pause replay':'Play replay');if(current)updateDynamic();}
function openInspector(value=true){if(value){openSequence(false);cancelDecode();openTrace(false);setPlaying(false);}document.body.classList.toggle('inspector-open',value);$('#inspect-toggle').setAttribute('aria-expanded',String(value));}
function openTrace(value=true){$('#solution-trace').hidden=!value;$('#trace-toggle').setAttribute('aria-expanded',String(value));document.body.classList.toggle('trace-open',value);if(value){openSequence(false);cancelDecode();openInspector(false);setPlaying(false);}}
function seek(t,index=inspected){cancelDecode();endHold=0;time=Number(t);inspected=index;setPlaying(false);drawBits();drawInspector();updateDynamic();}
function setVectorOpen(value){document.body.classList.toggle('vector-collapsed',!value);$('#vector-toggle').textContent=value?'Hide full x':'Show full x';$('#vector-toggle').setAttribute('aria-expanded',String(value));}
function cancelDecode(){if(!decodeTour)return;decodeTour=null;document.body.classList.remove('decoding');delete document.body.dataset.decodeStage;$('#decode-step').hidden=true;$('#decode-controls').hidden=true;document.querySelectorAll('.decode-target,.decode-selected').forEach(el=>el.classList.remove('decode-target','decode-selected'));setVectorOpen(vectorBeforeTour);}
function renderDecode(){
  const step=decodeTour[decodeStage];document.body.dataset.decodeStage=decodeStage;
  $('#event-title').textContent=step.title;$('#event-copy').textContent=step.copy;$('#decode-step').hidden=false;$('#decode-controls').hidden=false;$('#decode-step').textContent=`SOLUTION → ACTIONS / ${decodeStage+1} OF ${decodeTour.length}`;
  $('#decode-prev').disabled=decodeStage===0;$('#decode-next').textContent=decodeStage===decodeTour.length-1?'Run kitchen ▶':'Next →';$('#decode-auto').textContent=decodeAuto?'Pause steps':'Auto steps';$('#decode-auto').setAttribute('aria-pressed',String(decodeAuto));
  document.querySelectorAll('[data-bit]').forEach(el=>el.classList.toggle('decode-selected',!!current.bits[Number(el.dataset.bit)]));
  const actions=decodedActions(current,firstChoice());
  for(const id of RESOURCES)$(`#station-${id}`).classList.toggle('decode-target',decodeStage===3&&actions.some(a=>a.resource===id));
}
function startDecode(){openSequence(false);cancelDecode();openTrace(false);openInspector(false);setPlaying(false);time=current.snapshot.current_time;vectorBeforeTour=!document.body.classList.contains('vector-collapsed');setVectorOpen(true);decodeTour=decisionSteps(current);decodeStage=0;decodeElapsed=0;decodeAuto=!reduced;document.body.classList.add('decoding');updateDynamic();}
function finishDecode(){cancelDecode();time=current.snapshot.current_time;setPlaying(true);}
function stepDecode(delta,manual=false){if(!decodeTour)return;if(manual)decodeAuto=false;if(decodeStage+delta>=decodeTour.length){finishDecode();return;}decodeStage=Math.max(0,decodeStage+delta);decodeElapsed=0;renderDecode();}
function replayAlternative(index){cancelDecode();current=current.manual?referenceCase:withAlternative(referenceCase,index);sequence=productionSequence(current);time=current.snapshot.current_time;inspected=firstChoice();workerTracks=new Map(['W1','W2','W3'].map(id=>[id,buildWorkerTrack(current,id)]));drawBits();drawInspector();drawTranslation();drawSequence();provenance();openTrace(false);openInspector(false);setPlaying(true);}
function evidenceContent(){
  const rows=data.evidence.pilot.rows;
  $('#results-table').innerHTML=`<thead><tr><th>Scenario / seed</th><th>QAOA (U,W,B,R)</th><th>Raw CP optimum</th><th>Max bits</th></tr></thead><tbody>${rows.map(r=>`<tr><th>${r.case}</th><td>(${tuple(r.final)})</td><td>(${tuple(r.reference)})</td><td>${r.max_qubits}</td></tr>`).join('')}</tbody>`;
}
$('#scenario').addEventListener('change',e=>{loadCase(e.target.value);setPlaying(!reduced);});
$('#method').addEventListener('change',e=>{loadCase(current.id,e.target.value);setPlaying(!reduced);});
$('#trace-toggle').onclick=()=>openTrace($('#solution-trace').hidden);$('#close-trace').onclick=()=>openTrace(false);
$('#inspect-toggle').onclick=()=>openInspector(!document.body.classList.contains('inspector-open'));$('#close-inspector').onclick=()=>openInspector(false);
$('#vector-toggle').onclick=()=>{cancelDecode();setVectorOpen(document.body.classList.contains('vector-collapsed'));};
$('#decoded-strip').onclick=e=>{const b=e.target.closest('[data-program]');if(b){inspected=Number(b.dataset.program);drawBits();drawInspector();drawTranslation();openInspector();}};
$('#trace-content').onclick=e=>{const b=e.target.closest('[data-seek]');if(b)seek(b.dataset.seek);};
$('#program-phases').onclick=e=>{const b=e.target.closest('[data-program-seek]');if(b&& (inspected<0||current.bits[inspected]))seek(b.dataset.programSeek);};
$('#bits').onclick=e=>{const b=e.target.closest('[data-bit]');if(b){inspected=Number(b.dataset.bit);drawBits();drawInspector();openInspector();}};
$('#timeline').onclick=e=>{const b=e.target.closest('[data-operation]'),d=e.target.closest('[data-departure]');if(b)followOperation(b.dataset.operation);else if(d)seek(d.dataset.departure);};
$('#orders').onclick=e=>{const b=e.target.closest('[data-meal]');if(!b)return;const m=mealOrders(current).find(m=>m.id===b.dataset.meal);seek(m.departure);};
function inspectStation(id){const op=activeOperations(current,time).find(o=>o.resource===id)??allOperations(current).find(o=>o.resource===id&&o.start>time);if(op)inspected=op.recovery?-2:current.options.findIndex(p=>p.id===op.batch_id);drawBits();drawInspector();openInspector();}
$('#kitchen').onclick=e=>{const b=e.target.closest('[data-station]');if(b)inspectStation(b.dataset.station);};
$('#kitchen').onkeydown=e=>{const b=e.target.closest('[data-station]');if(b&&['Enter',' '].includes(e.key)){e.preventDefault();inspectStation(b.dataset.station);}};
$('#try-program').onclick=()=>replayAlternative(inspected);$('#restore-plan').onclick=()=>{loadCase(current.id,current.key);setPlaying(true);};
$('#tradeoff-content').onclick=e=>{const b=e.target.closest('[data-alternative]');if(b)replayAlternative(Number(b.dataset.alternative));};
for(const [id,tradeoff] of [['instructions-tab',false],['tradeoff-tab',true]])$(`#${id}`).onclick=()=>{$('#trace-content').hidden=tradeoff;$('#tradeoff-content').hidden=!tradeoff;$('#instructions-tab').setAttribute('aria-pressed',String(!tradeoff));$('#tradeoff-tab').setAttribute('aria-pressed',String(tradeoff));};
$('#why-bits').onclick=()=>{const value=$('#bit-explanation').hidden;$('#bit-explanation').hidden=!value;$('#why-bits').setAttribute('aria-expanded',String(value));};
$('#run-solution').onclick=startDecode;$('#decode-prev').onclick=()=>stepDecode(-1,true);$('#decode-next').onclick=()=>stepDecode(1,true);$('#decode-skip').onclick=finishDecode;$('#decode-auto').onclick=()=>{decodeAuto=!decodeAuto;renderDecode();};
function togglePlayback(){cancelDecode();if(!playing&&time>=playbackEnd(current)){time=0;endHold=0;}setPlaying(!playing);}
$('#play').onclick=togglePlayback;$('#restart').onclick=()=>seek(0);
$('#scrubber').oninput=e=>seek(e.target.value);$('#speed').onchange=e=>speed=Number(e.target.value);$('#loop').onclick=()=>{looping=!looping;$('#loop').setAttribute('aria-pressed',String(looping));};
$('#timeline-toggle').onclick=()=>{const closed=document.body.classList.toggle('timeline-closed');$('#timeline-toggle').setAttribute('aria-expanded',String(!closed));};
$('#sequence-toggle').onclick=()=>openSequence(!document.body.classList.contains('sequence-open'));$('#close-sequence').onclick=()=>openSequence(false);
$('#previous-event').onclick=()=>seek(adjacentEvent(sequence,time,-1));$('#next-event').onclick=()=>seek(adjacentEvent(sequence,time,1));
$('#production-sequence').addEventListener('click',e=>{const b=e.target.closest('[data-sequence-operation]');if(b)followOperation(b.dataset.sequenceOperation);});
for(const [id,view] of [['batch-view','batch'],['equipment-view','equipment']])$(`#${id}`).onclick=()=>{timelineView=view;drawTimeline();updateDynamic();};
for(const [id,packing] of [['cooking-queue-tab',false],['packing-queue-tab',true]])$(`#${id}`).onclick=()=>{$('#cooking-order').hidden=packing;$('#packing-order').hidden=!packing;$('#cooking-queue-tab').setAttribute('aria-pressed',String(!packing));$('#packing-queue-tab').setAttribute('aria-pressed',String(packing));$('#queue-caption').textContent=packing?'One packing line · portions go to these orders.':'Start order · separate cookers can overlap.';};
const layoutObserver=new ResizeObserver(updateLayout);layoutObserver.observe($('.decision-strip'));layoutObserver.observe($('.replay'));window.addEventListener('resize',updateLayout);
if(matchMedia('(max-width:760px)').matches)openSequence(false);
function showEvidence(open){$('#evidence').hidden=!open;$('#evidence-toggle').setAttribute('aria-expanded',String(open));if(open){cancelDecode();setPlaying(false);$('#close-evidence').focus();}else $('#evidence-toggle').focus();}
$('#evidence-toggle').onclick=()=>showEvidence($('#evidence').hidden);$('#close-evidence').onclick=()=>showEvidence(false);
for(const button of document.querySelectorAll('[data-evidence-tab]'))button.onclick=()=>{for(const b of document.querySelectorAll('[data-evidence-tab]'))b.setAttribute('aria-pressed',String(b===button));for(const p of document.querySelectorAll('[data-evidence-panel]'))p.hidden=p.dataset.evidencePanel!==button.dataset.evidenceTab;};
document.addEventListener('keydown',e=>{if(e.key==='Tab'&&!$('#evidence').hidden){const focusable=[...$('#evidence').querySelectorAll('button,a[href]')].filter(el=>el.getClientRects().length);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}if(e.key==='Escape'){cancelDecode();openTrace(false);openInspector(false);showEvidence(false);updateDynamic();}if(e.code==='Space'&&!['INPUT','SELECT','BUTTON','A'].includes(document.activeElement.tagName)){e.preventDefault();togglePlayback();}});
document.addEventListener('visibilitychange',()=>lastFrame=0);
function frame(now){
  const elapsed=lastFrame?Math.min((now-lastFrame)/1000,.1):0;lastFrame=now;
  if(decodeTour&&decodeAuto&&!document.hidden){decodeElapsed+=elapsed;if(decodeElapsed>=decodeTour[decodeStage].duration)stepDecode(1);}
  if(current&&playing&&!document.hidden){
    time+=elapsed*speed*1.5;
    if(time>=playbackEnd(current)){
      time=playbackEnd(current);
      if(!looping)setPlaying(false);
      else{endHold+=elapsed;if(endHold>=3){time=0;endHold=0;}}
    }
    if(now-lastDraw>100){updateDynamic();lastDraw=now;}else updateWorkers();
  }
  requestAnimationFrame(frame);
}
try{await artReady;const response=await fetch('./replay-data.json');if(!response.ok)throw new Error(`Replay returned ${response.status}`);data=await response.json();if(data.schema!=='catering-kitchen-replay.v3')throw new Error('V3 evidence required');evidenceContent();loadCase('CELL');setPlaying(!reduced);requestAnimationFrame(frame);}catch(e){$('#error').hidden=false;$('#error').textContent=`Kitchen replay could not load: ${e.message}`;setPlaying(false);}
