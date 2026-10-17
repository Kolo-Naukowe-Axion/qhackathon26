import {CASES,PHASES,RESOURCES,clock,activeOperations,allOperations,workerOperation,offline,deliveredMeals,packedMeals,requestedMeals,mealOrders,selectedPrograms,bitDescription,activateRun,discardedComponents} from './model.js';
import {kitchenSVG,prepareScene,renderWorker,renderKitchen} from './scene.js';
import {buildWorkerTrack,workerPoseAt} from './worker-motion.js';
import {decodedActions,stationState,withAlternative} from './kitchen-state.js';
import {decisionSteps,decisionComparison} from './decision-story.js';

const $=s=>document.querySelector(s),reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let data,current,referenceCase,fixture,inspected=-1,time=20,playing=false,looping=true,speed=1,lastFrame=0,lastDraw=0,workerTracks=new Map();
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
  const H=current.instance.horizon_minutes;
  const bar=o=>`<button class="op ${o.recovery?'recovery':o.kind} ${current.plan.batches.find(b=>b.id===o.batch_id)?.menu==='A'?'committed':''}" data-operation="${o.id}" title="${clock(o.start)}–${clock(o.end)} · ${label(o)} · ${o.worker}" style="left:${o.start/H*100}%;width:${(o.end-o.start)/H*100}%">${o.recovery?'CLEAN':o.kind==='cook'?'COOK':PHASES[o.kind]}</button>`;
  $('#timeline').innerHTML=`<div class="timeline-grid"><div class="ruler">${Array.from({length:Math.floor(H/20)+1},(_,i)=>`<span style="left:${i*20/H*100}%">${clock(i*20)}</span>`).join('')}</div>${RESOURCES.map(id=>`<div class="resource-row"><span class="resource-label">${id}</span>${current.snapshot.outages.filter(o=>o.resource===id).map(o=>`<span class="outage" style="left:${o.start/H*100}%;width:${(o.end-o.start)/H*100}%">OFF</span>`).join('')}${allOperations(current).filter(o=>o.resource===id).map(bar).join('')}</div>`).join('')}<div id="cursor" class="cursor"></div></div>`;
}
function updateWorkers(){
  ['W1','W2','W3'].map(id=>({el:$(`#chef-${id}`),pose:workerPoseAt(workerTracks.get(id),time)})).sort((a,b)=>a.pose.y-b.pose.y).forEach(({el,pose})=>{renderWorker(el,pose);$('#workers').append(el);});
}
function updateDynamic(){
  if(!current)return;
  renderKitchen(current,time);updateWorkers();
  $('#time').textContent=clock(time);$('#scene-clock').textContent=clock(time);$('#scrubber').value=time;
  $('#cursor').style.left=`${time/current.instance.horizon_minutes*100}%`;
  const active=activeOperations(current,time),orders=mealOrders(current),chosen=selectedPrograms(current);
  $('#event-title').textContent=time<current.snapshot.current_time?'Before the decision':active.length?active.map(label).join(' + '):'Between kitchen operations';
  $('#event-copy').textContent=active.length?active.map(o=>`${o.resource} · ${time<o.attended_end?o.worker:'unattended'}`).join(' / '):CASES[current.id].event;
  $('#meal-count').textContent=`${deliveredMeals(current,time)} / ${requestedMeals(current)} served`;
  $('#orders').innerHTML=orders.map(m=>{
    const hidden=time<m.revealed,departed=time>=m.departure,ready=m.ready_at!==null&&time>=m.ready_at;
    const status=hidden?'unrevealed':departed?(m.handed?'served':'missed'):ready?'both packed':m.handed?'scheduled':'incomplete';
    const a=m.allocations.filter(Boolean).length;
    return `<button class="order ${ready?'ready':''} ${departed&&m.handed?'delivered':''} ${departed&&!m.handed?'missed':''}" data-meal="${m.id}"><span class="order-icon">${hidden?'?':departed?(m.handed?'✓':'×'):ready?'▪':'·'}</span><div><b>${hidden?'Not yet revealed':`${current.instance.lot_size} × ${m.id==='committed'?'A + side':'B + side'}`}</b><small>${clock(m.departure)}${m.revealed?' · urgent':''} · ${hidden?'':`${a}/2 courses scheduled`}</small></div><span>${status}</span></button>`;
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
  cancelDecode();fixture=data.cases.find(c=>c.id===id);referenceCase=activateRun(fixture,key);current=referenceCase;time=current.snapshot.current_time;inspected=firstChoice();
  $('#scenario').disabled=false;$('#method').disabled=false;$('#scenario').value=id;$('#method').innerHTML=fixture.runs.map(r=>`<option value="${r.key}">${r.label}</option>`).join('');$('#method').value=key;
  $('#scrubber').max=current.instance.horizon_minutes;$('#end-time').textContent=`/ ${clock(current.instance.horizon_minutes)}`;
  workerTracks=new Map(['W1','W2','W3'].map(id=>[id,buildWorkerTrack(current,id)]));
  drawBits();drawInspector();drawTranslation();provenance();updateDynamic();
}
function setPlaying(value){playing=value;document.body.classList.toggle('is-paused',!value);$('#play').innerHTML=value?'Ⅱ <span>Pause</span>':'▶ <span>Play</span>';$('#play').setAttribute('aria-label',value?'Pause replay':'Play replay');if(current)updateDynamic();}
function openInspector(value=true){if(value){cancelDecode();openTrace(false);setPlaying(false);}document.body.classList.toggle('inspector-open',value);$('#inspect-toggle').setAttribute('aria-expanded',String(value));}
function openTrace(value=true){$('#solution-trace').hidden=!value;$('#trace-toggle').setAttribute('aria-expanded',String(value));document.body.classList.toggle('trace-open',value);if(value){cancelDecode();openInspector(false);setPlaying(false);}}
function seek(t,index=inspected){cancelDecode();time=Number(t);inspected=index;setPlaying(false);drawBits();drawInspector();updateDynamic();}
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
function startDecode(){cancelDecode();openTrace(false);openInspector(false);setPlaying(false);time=current.snapshot.current_time;vectorBeforeTour=!document.body.classList.contains('vector-collapsed');setVectorOpen(true);decodeTour=decisionSteps(current);decodeStage=0;decodeElapsed=0;decodeAuto=!reduced;document.body.classList.add('decoding');updateDynamic();}
function finishDecode(){cancelDecode();time=current.snapshot.current_time;setPlaying(true);}
function stepDecode(delta,manual=false){if(!decodeTour)return;if(manual)decodeAuto=false;if(decodeStage+delta>=decodeTour.length){finishDecode();return;}decodeStage=Math.max(0,decodeStage+delta);decodeElapsed=0;renderDecode();}
function replayAlternative(index){cancelDecode();current=current.manual?referenceCase:withAlternative(referenceCase,index);time=current.snapshot.current_time;inspected=firstChoice();workerTracks=new Map(['W1','W2','W3'].map(id=>[id,buildWorkerTrack(current,id)]));drawBits();drawInspector();drawTranslation();provenance();openTrace(false);openInspector(false);setPlaying(true);}
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
$('#timeline').onclick=e=>{const b=e.target.closest('[data-operation]');if(!b)return;const op=allOperations(current).find(o=>o.id===b.dataset.operation);seek(op.start,op.recovery?-2:current.options.findIndex(p=>p.id===op.batch_id));openInspector();};
$('#orders').onclick=e=>{const b=e.target.closest('[data-meal]');if(!b)return;const m=mealOrders(current).find(m=>m.id===b.dataset.meal);seek(m.departure);};
function inspectStation(id){const op=activeOperations(current,time).find(o=>o.resource===id)??allOperations(current).find(o=>o.resource===id&&o.start>time);if(op)inspected=op.recovery?-2:current.options.findIndex(p=>p.id===op.batch_id);drawBits();drawInspector();openInspector();}
$('#kitchen').onclick=e=>{const b=e.target.closest('[data-station]');if(b)inspectStation(b.dataset.station);};
$('#kitchen').onkeydown=e=>{const b=e.target.closest('[data-station]');if(b&&['Enter',' '].includes(e.key)){e.preventDefault();inspectStation(b.dataset.station);}};
$('#try-program').onclick=()=>replayAlternative(inspected);$('#restore-plan').onclick=()=>{loadCase(current.id,current.key);setPlaying(true);};
$('#tradeoff-content').onclick=e=>{const b=e.target.closest('[data-alternative]');if(b)replayAlternative(Number(b.dataset.alternative));};
for(const [id,tradeoff] of [['instructions-tab',false],['tradeoff-tab',true]])$(`#${id}`).onclick=()=>{$('#trace-content').hidden=tradeoff;$('#tradeoff-content').hidden=!tradeoff;$('#instructions-tab').setAttribute('aria-pressed',String(!tradeoff));$('#tradeoff-tab').setAttribute('aria-pressed',String(tradeoff));};
$('#why-bits').onclick=()=>{const value=$('#bit-explanation').hidden;$('#bit-explanation').hidden=!value;$('#why-bits').setAttribute('aria-expanded',String(value));};
$('#run-solution').onclick=startDecode;$('#decode-prev').onclick=()=>stepDecode(-1,true);$('#decode-next').onclick=()=>stepDecode(1,true);$('#decode-skip').onclick=finishDecode;$('#decode-auto').onclick=()=>{decodeAuto=!decodeAuto;renderDecode();};
$('#play').onclick=()=>{cancelDecode();if(time>=current.instance.horizon_minutes)time=0;setPlaying(!playing);};$('#restart').onclick=()=>seek(0);
$('#scrubber').oninput=e=>seek(e.target.value);$('#speed').onchange=e=>speed=Number(e.target.value);$('#loop').onclick=()=>{looping=!looping;$('#loop').setAttribute('aria-pressed',String(looping));};
$('#timeline-toggle').onclick=()=>{const closed=document.body.classList.toggle('timeline-closed');$('#timeline-toggle').setAttribute('aria-expanded',String(!closed));};
function showEvidence(open){$('#evidence').hidden=!open;$('#evidence-toggle').setAttribute('aria-expanded',String(open));if(open){cancelDecode();setPlaying(false);$('#close-evidence').focus();}else $('#evidence-toggle').focus();}
$('#evidence-toggle').onclick=()=>showEvidence($('#evidence').hidden);$('#close-evidence').onclick=()=>showEvidence(false);
for(const button of document.querySelectorAll('[data-evidence-tab]'))button.onclick=()=>{for(const b of document.querySelectorAll('[data-evidence-tab]'))b.setAttribute('aria-pressed',String(b===button));for(const p of document.querySelectorAll('[data-evidence-panel]'))p.hidden=p.dataset.evidencePanel!==button.dataset.evidenceTab;};
document.addEventListener('keydown',e=>{if(e.key==='Tab'&&!$('#evidence').hidden){const focusable=[...$('#evidence').querySelectorAll('button,a[href]')].filter(el=>el.getClientRects().length);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}if(e.key==='Escape'){cancelDecode();openTrace(false);openInspector(false);showEvidence(false);updateDynamic();}if(e.code==='Space'&&!['INPUT','SELECT','BUTTON','A'].includes(document.activeElement.tagName)){e.preventDefault();cancelDecode();setPlaying(!playing);}});
document.addEventListener('visibilitychange',()=>lastFrame=0);
function frame(now){const elapsed=lastFrame?Math.min((now-lastFrame)/1000,.1):0;lastFrame=now;if(decodeTour&&decodeAuto&&!document.hidden){decodeElapsed+=elapsed;if(decodeElapsed>=decodeTour[decodeStage].duration)stepDecode(1);}if(current&&playing&&!document.hidden){time+=elapsed*speed*1.5;if(time>=current.instance.horizon_minutes){if(looping)time=0;else{time=current.instance.horizon_minutes;setPlaying(false);}}if(now-lastDraw>100){updateDynamic();lastDraw=now;}else updateWorkers();}requestAnimationFrame(frame);}
try{await artReady;const response=await fetch('./replay-data.json');if(!response.ok)throw new Error(`Replay returned ${response.status}`);data=await response.json();if(data.schema!=='catering-kitchen-replay.v3')throw new Error('V3 evidence required');evidenceContent();loadCase('CELL');setPlaying(!reduced);requestAnimationFrame(frame);}catch(e){$('#error').hidden=false;$('#error').textContent=`Kitchen replay could not load: ${e.message}`;setPlaying(false);}
