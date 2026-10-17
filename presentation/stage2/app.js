import {blueprint,fixture,normalizeTrace,snapshot,machineStatus,metricsAt,unitGenealogy,resourceOccupancy,deadlineEvidence,escapeHTML as esc} from './model.js';
import {mountResearch} from './research.js';
import {fetchLinkedTrace} from './trace-loader.js';
import {buildFactoryTour,tourRate} from './factory-tour.js';
import {orderIds,orderJourney,nextActivityTick,partGlyph} from './factory-story.js';
import {activeTransportPath,nearestHeading,transportPose,processName,machineEffect,reconcileSVG} from './factory-motion.js';
import {point,dockPoint as transportPoint,processLabel} from './factory-layout.js';
import {FINAL_REPLAYS,DEFAULT_REPLAY,replayPreset} from './replay-presets.js';
import {completionRecord,completionAt,factoryDuration} from './run-completion.js';
import {unitKind,operationProgress,stationPieces,pieceTransform,glyphBody} from './factory-parts.js';

const $=selector=>document.querySelector(selector);
let trace=blueprint(),comparison=null,tick=0,playing=false,overlay='flow',selected=null,lastFrame=0,lastDraw=0,lastDetails=0;
const floorViews=new Map();
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
let rosterSignature='';
let factoryVisited=false,tourChapters=[],tourIndex=-1,savedSpeed='4',tourAuto=false,tourHoldUntil=0,presenting=false,followOrder='',highlightOrder=false,storySignature='';
const colors={T:'#65869f',F:'#7596a6',S:'#b48e7b',WASH:'#79a2af',HEAT:'#b78a6d',QA:'#8e9cae',ASSEMBLY:'#729b96'};
const color=process=>colors[process]??'#65869f';
const formatTime=value=>{const mins=Math.round(value*trace.tick_minutes);return `${String(Math.floor(mins/60)).padStart(2,'0')}:${String(mins%60).padStart(2,'0')}`;};
const safe=value=>esc(value);
const validationPassed=run=>run.validation.valid===true&&['passed','valid'].includes(run.validation.status);
const runLabel=run=>`${run.provenance.viewer_replay?.label??run.run_id}${run.provenance.weights?.selector?` / ${run.provenance.weights.selector.toUpperCase()}`:''}${run.provenance.physical_kit_recovery?` / recovery ${run.provenance.physical_kit_recovery.enabled?'ON':'OFF'}`:''}`;
const tardinessMinutes=run=>deadlineEvidence(run).primaryMinutes??0;
function machineSprite(machine,run,state){
 const [x,y]=point(machine.id),status=machineStatus(run,machine.id,tick),op=status.operation,fill=status.state==='outage'?'#b77562':status.state==='output held'?'#ac9b76':color(machine.process),sel=selected?.kind==='machine'&&selected.id===machine.id&&(selected.source==='b'?run===comparison:run===trace);
 const progress=op?Math.min(1,(tick-op.start)/(op.end-op.start)):0;
 const units=[...state.location.entries()].filter(([,at])=>at===machine.id).map(([unit])=>unit);
 const attending=op?(Array.isArray(op.worker_intervals)?op.worker_intervals.filter(row=>row.start<=tick&&tick<row.end).map(row=>row.worker_id):op.worker_ids):[];
 const workerCount=attending.length,toolCount=op?.tool_ids.length??0;
 const feature=machine.process==='T'?'<rect x="-28" y="-33" width="49" height="13" fill="#2c465b"/><rect x="-18" y="-31" width="19" height="9" fill="#c5d9df"/><path d="M22-33v26M18-20h10" stroke="#e5eeed" stroke-width="4"/>':machine.process==='HEAT'?'<rect x="-27" y="-42" width="54" height="37" fill="#5f6570"/><rect x="-19" y="-34" width="38" height="23" fill="#ccaa7b"/><path d="M-8-30v15M4-30v15M15-30v15" stroke="#ffe2ac" stroke-width="3"/>':machine.process==='QA'?'<rect x="-18" y="-49" width="36" height="27" fill="#435d74"/><rect x="-12" y="-43" width="24" height="16" fill="#b9d7da"/><path d="M0-21v13M-14-7h28" stroke="#355e7c" stroke-width="5"/>':machine.process==='ASSEMBLY'?'<rect x="-35" y="-24" width="70" height="12" fill="#bccbd0"/><rect x="-20" y="-40" width="16" height="16" fill="#e5eeed"/><rect x="7" y="-34" width="23" height="10" fill="#496a7e"/>':machine.process==='S'?'<path d="M-25-8v-29h30l14 15" fill="none" stroke="#d5dfe3" stroke-width="7"/><rect x="-10" y="-18" width="28" height="9" fill="#42596a"/>':machine.process==='WASH'?'<rect x="-27" y="-38" width="54" height="30" fill="#425e72"/><rect x="-21" y="-32" width="42" height="19" fill="#b4d7de"/><path d="M-17-27h6m8 0h6m8 0h6" stroke="#e5f0ed" stroke-width="3"/>':'<rect x="-24" y="-47" width="48" height="38" fill="#3c576d"/><rect x="-16" y="-39" width="32" height="24" fill="#b1c5cf"/><path d="M0-38v16m-7 0h14" stroke="#355e7c" stroke-width="5"/>';
 const working=Boolean(op),effect=op&&(!op.kind||op.kind==='process')?machineEffect(machine.process):'';
 const pieces=stationPieces(machine,state,tick);
 const workpieces=pieces.map(piece=>`<g class="station-workpiece ${piece.assembly?'assembly-piece':''}" data-piece="${safe(piece.id)}" data-index="${piece.index??0}" data-count="${piece.count??1}" transform="${pieceTransform(piece,machine.process)}"><title>${safe(piece.id)}</title><g class="workpiece-shape">${glyphBody(piece.kind)}</g></g>`).join('');
 const job=op?.unit_id?.split('/').slice(0,2).join(' / ')??'';
 return `<g class="selectable factory-machine ${working?'is-working':status.state==='outage'?'is-outage':status.state==='output held'?'is-held':'is-idle'} process-${safe(machine.process)} ${sel?'selected':''}" data-machine="${safe(machine.id)}" tabindex="0" role="button" aria-label="${safe(machine.id)}: ${safe(status.state)}" transform="translate(${x} ${y})"><title>${safe(machine.id)} · ${safe(processName(machine.process))} · ${safe(status.state)}${op?` · ${safe(op.unit_id)}`:''}</title>
 <path class="machine-dock" d="M48-30h38v40H48"/><ellipse class="machine-ground-shadow" cx="2" cy="32" rx="56" ry="12"/>
 <rect class="machine-plinth" x="-54" y="-54" width="108" height="95" rx="7"/>
 <rect class="selection-ring" x="-59" y="-62" width="118" height="119" rx="7" fill="none"/>
 ${working?'<path class="working-corners" d="M-54-39v-15h15m78 0h15v15m0 65v15H39m-78 0h-15V26"/>':''}
 <g class="machine-housing"><path d="M-37 23v9h12v-9M20 23v9h12v-9" fill="#2c465b"/><path class="machine-body" d="M-44-19H35l10 9v35h-89z" fill="${fill}"/><path d="M-44-19H35l10 9h-79z" fill="#e5eeed" opacity=".55"/><path d="M-44-19v44h79" fill="none" stroke="#2c465b" stroke-opacity=".55" stroke-width="2"/><path d="M35-19l10 9v35H35z" fill="#243b4e55"/><rect x="-44" y="-3" width="79" height="6" fill="#edf3f2" opacity=".55"/>${feature}<g class="station-workpieces">${workpieces}</g>${effect}<path d="M-35 8h24m-24 4h24m-24 4h24" stroke="#2c465b" stroke-width="2"/><rect x="4" y="7" width="10" height="12" fill="#e5eeed" opacity=".35"/><path d="M6 10h6m-6 3h6m-6 3h6" stroke="#2c465b"/><circle class="machine-status-led" cx="24" cy="12" r="4" fill="${status.state==='outage'?'#e3a084':working?'#a9f0d2':status.state==='output held'?'#e9c88e':'#90aabd'}"/></g>
 <g class="machine-nameplate"><rect class="machine-id-plate" x="-49" y="39" width="98" height="30" rx="4"/><text class="machine-id" x="${units.length&&overlay==='flow'?-7:0}" y="52" text-anchor="middle">${safe(machine.id)} · ${safe(processLabel(machine.process))}</text><text class="machine-caption" x="0" y="65" text-anchor="middle">${safe(working?job||op.kind||'Working':status.state==='output held'?'Awaiting pickup':status.state==='outage'?'Unavailable':'Idle')}</text>${overlay==='flow'&&units.length?`<g class="part-count"><title>${units.length} part${units.length===1?'':'s'} at ${safe(machine.id)}</title><circle cx="40" cy="48" r="6"/><text x="40" y="50.5" text-anchor="middle">${units.length}</text></g>`:''}</g>
 ${working?'<rect class="machine-progress-track" x="-43" y="31" width="86" height="4" rx="2"/><rect class="machine-progress" x="-43" y="31" width="'+progress*86+'" height="4" rx="2"/>':''}
 ${status.state==='outage'?'<path class="outage-symbol" d="M-10-53h20l8 18h-36z"/><text x="0" y="-39" font-size="13" fill="#f1f5f4" text-anchor="middle">!</text>':''}
 ${overlay==='people'&&op?`<g class="crew-assignment" transform="translate(-48 75)"><circle cx="0" cy="0" r="5" fill="#d6bc86"/><path d="M-6 7h12v12h-12z" fill="#355e7c"/><text x="12" y="8" font-size="9">${workerCount?`${workerCount} crew`:'automatic'} / ${toolCount} tools</text></g>`:''}
 ${overlay==='energy'&&op?`<text class="machine-power" x="0" y="82" text-anchor="middle">${safe(op.power_kw??'?')} kW · ${safe(op.mode??'mode ?')}</text>`:''}</g>`;

}
function robotSprite(agv){
 return `<g class="agv-sprite selectable" data-agv="${safe(agv.id)}" tabindex="0" role="button" aria-label="${safe(agv.id)}"><title>${safe(agv.id)}</title><ellipse class="robot-shadow" cy="12" rx="20" ry="8"/><circle class="robot-selection" r="25"/><g class="robot-facing"><path class="robot-headlight" d="M15-5L49-21V21L15 5Z"/><rect class="robot-tread" x="-17" y="-14" width="33" height="6" rx="2"/><rect class="robot-tread" x="-17" y="8" width="33" height="6" rx="2"/><path class="robot-tread-motion" d="M-13-11h25M-13 11h25"/><rect class="robot-body" x="-17" y="-10" width="34" height="20" rx="6"/><path class="robot-bumper" d="M12-8q6 8 0 16"/><rect class="robot-glass" x="7" y="-6" width="5" height="12" rx="2"/><rect class="robot-bay" x="-12" y="-6" width="15" height="12" rx="2"/><g class="robot-cargo"><path d="M-10-8H0V6H-10Z"/><path d="M-10-8l4-3H4L0-8M0-8H4V3L0 6M-6-11V-7"/></g><circle class="robot-led" cx="-13" cy="0" r="2"/></g><g class="robot-cluster"><title></title><circle cx="18" cy="-14" r="8"/><text x="18" y="-11" text-anchor="middle"></text></g><g class="robot-label"><rect x="-17" y="19" width="34" height="13" rx="3"/><text x="0" y="28" text-anchor="middle">${safe(agv.id.replace(/^AGV/,'R'))}</text></g></g>`;
}
function renderFloor(run,target){
 const state=snapshot(run,tick),journey=run===trace&&highlightOrder&&followOrder?orderJourney(run,followOrder,tick,state.location):null;
 const floor=run.resources.machines,robotMarkers=[];
 const delivered=state.events.filter(event=>event.type==='ship').length;
 let view=floorViews.get(target);
 if(!view||view.run!==run){
 const hall=(x,name)=>`<g><path d="M${x+8} 90h418v474H${x+8}z" fill="#344b5d" opacity=".45"/><path d="M${x} 76h418v474H${x}z" fill="#536778"/><path d="M${x+5} 88h408v450H${x+5}z" fill="#d5dfe3"/><path d="M${x+5} 88h408v450H${x+5}z" fill="url(#tiles-${target.slice(1)})"/><path d="M${x} 60h418v30H${x}z" fill="#a6bdca" stroke="#536778" stroke-width="2"/><path d="M${x} 60h418v7H${x}z" fill="#f1f5f4"/><path d="M${x+5} 87h408" stroke="#869ba8" stroke-width="3"/><path d="M${x} 90v147m0 46v267m418-460v147m0 46v267" stroke="#869ba8" stroke-width="7"/><path d="M${x-3} 90v147m0 46v254m418-447v147m0 46v254" stroke="#e8edef" stroke-width="2"/><path d="M${x} 538h418v12H${x}z" fill="#bac9d0"/><path d="M${x} 538h418v3H${x}z" fill="#f1f5f4"/><path d="M${x} 550h418v8H${x}z" fill="#42596a"/><path d="M${x+25} 105h365" stroke="#a6bdca" stroke-width="4"/><path d="M${x+40} 105v18m325-18v18" stroke="#8196a3" stroke-width="3"/><rect x="${x+14}" y="70" width="83" height="25" fill="#355e7c"/><text x="${x+55}" y="87" text-anchor="middle" font-size="11" letter-spacing="2" fill="#f1f5f4" style="fill:#f1f5f4">HALL ${name}</text><text x="${x+112}" y="83" font-size="8" style="fill:#3e6176" letter-spacing=".5">${name==='A'?'MACHINING + TREATMENT':'FINISHING + ASSEMBLY'}</text>${[120,365,510].map(y=>`<rect x="${x+3}" y="${y}" width="9" height="21" fill="#a6bdca"/><rect x="${x+406}" y="${y}" width="9" height="21" fill="#a6bdca"/>`).join('')}<path d="M${x+15} 505v18h18m352 0h18v-18" fill="none" stroke="#a6bdca" stroke-width="2"/><path d="M${x+20} 260h378" stroke="#7f8e9b" stroke-width="37"/><path d="M${x+20} 243h378m-378 34h378" stroke="#a6bdca" stroke-width="2"/><path d="M${x+15} 260h388" stroke="#e2eaed" stroke-width="2" stroke-dasharray="13 12"/></g>`;
 const terrain=Array.from({length:45},(_,i)=>{const x=(i*173+21)%1170,y=(i*97+13)%605;return `<path d="M${x} ${y}h${i%3*3+4}v3h-3v2h-4z" fill="${i%2?'#8798a6':'#526478'}" opacity=".5"/>`;}).join('');
 $(target).innerHTML=`<svg class="factory-scene" viewBox="0 50 1190 520" role="group" aria-label="Two factory halls with ${floor.length} machines; ${state.active.length} active operations" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="tiles-${target.slice(1)}" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0v34" stroke="#b8c7ce" stroke-width="1" fill="none"/><path d="M1 2h31" stroke="#e8edef" stroke-width="1" fill="none"/></pattern><pattern id="stripe-${target.slice(1)}" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="14" fill="#c4b28d"/></pattern></defs>${terrain}<path d="M40 260h1095" stroke="#536778" stroke-width="55"/><path d="M500 246h145v45H500z" fill="#344b5d"/><path d="M500 237h145v46H500z" fill="#7f8e9b" stroke="#42596a" stroke-width="3"/><path d="M500 260h145" stroke="#d5dfe3" stroke-width="2" stroke-dasharray="13 12"/><rect x="505" y="238" width="135" height="5" fill="url(#stripe-${target.slice(1)})"/><rect x="505" y="277" width="135" height="5" fill="url(#stripe-${target.slice(1)})"/>${hall(82,'A')}${hall(645,'B')}<g><path d="M495 227h8v16h-8m142-16h8v16h-8M495 277h8v16h-8m142-16h8v16h-8" fill="#a6bdca"/><rect x="523" y="204" width="102" height="19" fill="#42596a"/><text x="574" y="217" class="world-label" text-anchor="middle" font-size="8" letter-spacing="1">SINGLE LANE</text><text x="574" y="311" class="world-label bridge-state" text-anchor="middle" font-size="8">ONE ROBOT AT A TIME</text><g transform="translate(25 295)"><rect x="4" y="6" width="48" height="65" fill="#344b5d" opacity=".4"/><rect width="48" height="65" fill="#8196a3"/><path d="M4 5h40v53H4z" fill="#42596a"/><path d="M7 9h14v17H7zM26 9h14v17H26zM7 31h14v17H7zM26 31h14v17H26z" fill="#c6b695" stroke="#e5d6b4"/><path d="M0 28h48M0 54h48" stroke="#a6bdca" stroke-width="3"/><text x="24" y="83" text-anchor="middle" font-size="8" class="world-label" letter-spacing="1">STOCK</text></g><g class="shipping-zone" transform="translate(1080 390)"><path d="M5 10h78v60H5z" fill="#344b5d" opacity=".4"/><path d="M0 0h78v60H0z" fill="#a6bdca"/><path d="M5 10h63v35H5z" fill="#42596a"/><path d="M8 15h18v24H8zM30 15h18v24H30zM52 15h12v24H52z" fill="#c6b695"/><path d="M0 0h78v5H0zM0 52h78v4H0z" fill="#d5dfe3"/><text x="39" y="78" text-anchor="middle" font-size="9" class="world-label"><tspan class="ship-count">SHIP ${delivered||'—'}</tspan></text></g><g fill="#42596a" stroke="#a6bdca" stroke-width="2"><rect x="37" y="125" width="35" height="47"/><rect x="1102" y="125" width="35" height="47"/></g><g fill="#b8ddd4"><path d="M55 131l-8 17h8l-5 17 15-23h-9z"/><path d="M1120 131l-8 17h8l-5 17 15-23h-9z"/></g><text x="55" y="190" text-anchor="middle" font-size="8" class="world-label">CHARGE A</text><text x="1120" y="190" text-anchor="middle" font-size="8" class="world-label">CHARGE B</text></g><g class="station-docks" aria-hidden="true"><rect x="35" y="254" width="40" height="39" rx="5"/><rect x="1097" y="328" width="46" height="45" rx="5"/><rect x="35" y="200" width="40" height="39" rx="5"/><rect x="1100" y="200" width="40" height="39" rx="5"/><path d="M1120 373v17M55 293v2"/></g><g class="flow-route-layer"></g><g class="machine-layer"></g><g class="robot-layer"></g><g class="floor-energy-layer"></g><g class="delivery-layer"></g>${run.provenance.kind==='blueprint'?'<text x="590" y="568" text-anchor="middle" font-size="9" class="world-label">DESIGN BLUEPRINT · NO ACTIVITY OR RESULTS LOADED</text>':''}</svg>`;
  view={run,svg:$(target).querySelector('svg'),machines:new Map(),routes:new Map(),robots:new Map(),energySignature:null};floorViews.set(target,view);
 }
 view.svg.setAttribute('aria-label',`Two factory halls with ${floor.length} machines; ${state.active.length} active operations`);
 reconcileSVG(view.svg.querySelector('.machine-layer'),view.machines,floor.map(machine=>{
  const status=machineStatus(run,machine.id,tick),op=status.operation;
  const units=[...state.location].filter(([,at])=>at===machine.id).map(([unit])=>unit);
  const attending=op?.worker_intervals?.filter(row=>row.start<=tick&&tick<row.end).map(row=>row.worker_id);
  const signature=JSON.stringify([status.state,op?.id,overlay,selected?.kind,selected?.id,selected?.source,units,attending]);
  return {key:machine.id,signature,get markup(){return machineSprite(machine,run,state);}};
 }));
 for(const {node} of view.machines.values()){
  node.classList.toggle('story-muted',Boolean(journey&&!journey.relatedMachines.has(node.dataset.machine)&&!node.classList.contains('selected')));
  node.classList.toggle('story-related',Boolean(journey&&journey.relatedMachines.has(node.dataset.machine)));
  const op=state.active.find(row=>row.machine_id===node.dataset.machine);
  if(op){
   const progress=operationProgress(op,tick);node.querySelector('.machine-progress')?.setAttribute('width',progress*86);
   for(const piece of node.querySelectorAll('.assembly-piece'))piece.setAttribute('transform',pieceTransform({assembly:true,index:Number(piece.dataset.index),count:Number(piece.dataset.count),progress},'ASSEMBLY'));
   node.querySelector('.workpiece-scan')?.setAttribute('transform',`translate(0 ${progress*18})`);
  }
 }
 reconcileSVG(view.svg.querySelector('.flow-route-layer'),view.routes,overlay==='flow'?state.moves.flatMap(move=>{
  const points=activeTransportPath(move,tick,transportPoint).map(p=>p.join(',')).join(' ');if(!points)return [];
  const loaded=Boolean(move.unit_id)&&move.pickup_tick<=tick&&tick<move.drop_tick;
  const relevant=!journey||journey.components.some(row=>row.id===move.unit_id)||journey.pump===move.unit_id||selected?.id===move.agv_id;
  return [{key:move.id,signature:`${loaded}/${relevant}/${points}`,get markup(){return `<g class="transport-route ${loaded?'route-loaded':'route-empty'} ${relevant?'':'story-muted'}"><polyline class="route-underlay" points="${points}"/><polyline class="route-motion" points="${points}"/></g>`;}}];
 }):[]);
 reconcileSVG(view.svg.querySelector('.robot-layer'),view.robots,run.resources.agvs.map(agv=>({key:agv.id,signature:agv.id,markup:robotSprite(agv)})));
 for(const agv of run.resources.agvs){
  const entry=view.robots.get(agv.id),node=entry.node,move=state.moves.find(row=>row.agv_id===agv.id),previous=run.moves.filter(row=>row.agv_id===agv.id&&row.end<=tick).sort((a,b)=>b.end-a.end)[0];
  const initial=previous?transportPoint(previous.to):transportPoint(agv.initial_location??'CHARGE_A');
  const pose=move?transportPose(move,tick,transportPoint):{x:initial[0],y:initial[1],angle:0,loaded:false,moving:false};
  node.setAttribute('transform',`translate(${pose.x} ${pose.y})`);
  entry.heading=pose.moving?nearestHeading(entry.heading??pose.angle,pose.angle):entry.heading??pose.angle;
  node.querySelector('.robot-facing').setAttribute('transform',`rotate(${entry.heading})`);
  const cargo=pose.loaded?unitKind(move?.unit_id):null,cargoKey=pose.loaded?cargo??'crate':'';
  if(entry.cargoKey!==cargoKey){entry.cargoKey=cargoKey;node.querySelector('.robot-cargo').innerHTML=cargo?`<g class="cargo-part" transform="translate(-13 -9) scale(.5)">${glyphBody(cargo)}</g>`:'<path d="M-10-8H0V6H-10Z"/><path d="M-10-8l4-3H4L0-8M0-8H4V3L0 6M-6-11V-7"/>';}
  node.dataset.moving=pose.moving;node.dataset.loaded=pose.loaded;
  node.dataset.present=String(Boolean(move)||selected?.kind==='agv'&&selected.id===agv.id);
  node.classList.toggle('story-muted',Boolean(journey&&!journey.relatedRobots.has(agv.id)&&selected?.id!==agv.id));
  node.classList.toggle('selected',selected?.kind==='agv'&&selected.id===agv.id&&(selected.source==='b'?run===comparison:run===trace));
  const task=move?.kind==='charge'&&tick>=(move.charge_start??move.end)?`charging at ${move.to}`:move?`${pose.loaded?'carrying '+move.unit_id:move.kind==='charge'?'heading to charger':'empty / awaiting pickup'} to ${move.to}`:'parked';
  const description=`${agv.id}: ${task}`;
  node.setAttribute('aria-label',description);node.querySelector('title').textContent=description;robotMarkers.push({node,pose});
 }
 // Several robots can share a schematic dock; show a count instead of stacked sprites.
 const dockGroups=new Map();
 for(const marker of robotMarkers){marker.node.dataset.clustered='false';marker.node.querySelector('.robot-cluster').style.display='none';if(marker.pose.moving||marker.node.dataset.present!=='true')continue;const key=`${marker.pose.x.toFixed(3)}/${marker.pose.y.toFixed(3)}`;if(!dockGroups.has(key))dockGroups.set(key,[]);dockGroups.get(key).push(marker);}
 for(const group of dockGroups.values())if(group.length>1){const lead=group.find(row=>row.node.classList.contains('selected'))??group[0];for(const row of group)row.node.dataset.clustered=String(row!==lead);lead.node.querySelector('.robot-cluster').style.display='';lead.node.querySelector('.robot-cluster text').textContent='×'+group.length;lead.node.querySelector('.robot-cluster title').textContent=`${group.length} robots at this dock`;}
 const deliveryFocus=journey?.shipped;
 const deliveryLayer=view.svg.querySelector('.delivery-layer');
 const deliveryKey=deliveryFocus?`${journey.orderId}/${deliveryFocus.tick}`:'';
 if(view.deliveryKey!==deliveryKey){view.deliveryKey=deliveryKey;deliveryLayer.innerHTML=deliveryFocus?`<g class="delivery-marker" transform="translate(1120 420)"><rect x="-21" y="-20" width="42" height="36" rx="5"/><svg x="-18" y="-20" width="36" height="36" viewBox="0 0 36 36">${partGlyph('pump').replace(/<svg[^>]*>|<\/svg>/g,'')}</svg><rect class="delivery-tag" x="-51" y="65" width="102" height="23" rx="4"/><text x="0" y="80" text-anchor="middle">✓ ${safe(journey.orderId)} shipped</text></g>`:'';}
 view.svg.querySelector('.ship-count').textContent=`SHIPPED ${delivered}`;
 const crossing=state.moves.filter(move=>move.legs?.some(leg=>leg.start<=tick&&tick<leg.end&&((leg.from==='HUB_A'&&leg.to==='HUB_B')||(leg.from==='HUB_B'&&leg.to==='HUB_A'))));
 view.svg.querySelector('.bridge-state').textContent=crossing.length?`${crossing.map(move=>move.agv_id).join(' + ')} CROSSING`:'ONE ROBOT AT A TIME';
 view.svg.querySelector('.shipping-zone').classList.toggle('has-shipped',delivered>0);
 const energy=state.energy,energySignature=overlay==='energy'?JSON.stringify(energy):'';
 if(view.energySignature!==energySignature){view.energySignature=energySignature;view.svg.querySelector('.floor-energy-layer').innerHTML=overlay==='energy'?`<g transform="translate(470 553)"><rect x="0" y="-18" width="272" height="34" fill="#e2eaed"/><text x="12" y="3" font-size="11">${energy?`GRID ${safe(energy.grid_kw)} / ${safe(energy.cap_kw)} kW · SOLAR ${safe(energy.solar_kw??'?')}`:'No energy telemetry in trace'}</text></g>`:'';}
 return state;

}
function renderTimeline(){
 const runs=comparison?[trace,comparison]:[trace],rowH=20,left=74,top=28,width=1100,plot=width-left-20,horizon=Math.max(...runs.map(run=>run.horizon_ticks)),rows=runs.flatMap((run,index)=>run.resources.machines.map(machine=>({run,index,machine}))),height=top+rows.length*rowH+12;
 const grid=Array.from({length:9},(_,i)=>{const x=left+plot*i/8;return `<path d="M${x} ${top-6}v${rows.length*rowH}" stroke="#8196a335"/><text x="${x}" y="12" font-size="9" fill="#536b7b" text-anchor="middle">${Math.round(horizon*i/8*trace.tick_minutes/60)}h</text>`;}).join('');
 const rowMarks=rows.map(({run,index,machine},i)=>{const y=top+i*rowH;return `<text x="4" y="${y+12}" font-size="9">${comparison?`${index?'B':'A'} / `:''}${safe(machine.id)}</text><path d="M${left} ${y+rowH-1}h${plot}" stroke="#8196a325"/>${run.operations.filter(op=>op.machine_id===machine.id).map(op=>`<g class="op-bar" data-operation="${safe(op.id)}" data-run="${index}" role="button" tabindex="0" aria-label="${safe(op.id)} ${safe(op.unit_id)} ${op.start} to ${op.end}"><title>${safe(op.id)} · ${safe(op.unit_id)} · ${op.start}–${op.end} ticks</title><rect x="${left+op.start/horizon*plot}" y="${y+2}" width="${Math.max(1,(op.end-op.start)/horizon*plot)}" height="14" fill="${color(op.process??machine.process)}" opacity="${selected?.kind==='unit'&&selected.id!==op.unit_id?.toString()?'.25':'1'}"/>${(op.end-op.start)/horizon*plot>38?`<text x="${left+op.start/horizon*plot+3}" y="${y+12}" font-size="8" fill="#f1f5f4" pointer-events="none">${safe(op.unit_id)}</text>`:''}</g>`).join('')}`;}).join('');
 $('#timeline').innerHTML=`<svg class="timeline-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="group" aria-label="Machine operation reservations over time">${grid}${rowMarks}<path id="timeline-cursor" d="M${left+tick/horizon*plot} 17v${height-25}" stroke="#ae6e55" stroke-width="1.5"/></svg>`;
 $('#timeline-description').textContent=trace.operations.length?`${trace.operations.length} operations${comparison?` / ${comparison.operations.length} in B`:''} · intervals [start, end)`:'Blueprint only · no activity reservations';
}
function renderTelemetry(){
 const target=$('#telemetry');target.hidden=overlay!=='energy';if(target.hidden)return;
 if(target.previousElementSibling!==$('.inspector-top'))$('.inspector-top').after(target);
 if(!trace.energy.length){target.innerHTML='<p>No energy telemetry supplied. This view does not infer consumption from machine count.</p>';return;}
 const width=360,height=126,left=45,plot=300,max=Math.max(1,...trace.energy.flatMap(row=>[row.grid_kw??0,row.cap_kw??0,row.load_kw??0]));
 const x=t=>left+t/trace.horizon_ticks*plot,y=value=>104-(value??0)/max*80;
 const line=key=>trace.energy.filter(row=>Number.isFinite(row[key])).map(row=>`${x(row.tick)},${y(row[key])}`).join(' ');
 target.innerHTML=`<div class="telemetry-heading"><span class="eyebrow">ELECTRICITY / FULL RECORDED RUN</span><span><i style="background:#355e7c"></i>Grid import <i style="background:#ae6e55"></i>Grid cap <i style="background:#bd9f6b"></i>Solar</span></div><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Recorded grid electricity, capacity and solar power over the run"><path d="M${left} 104h${plot}" stroke="#8196a350"/><text x="5" y="28" font-size="10">${Math.ceil(max)} kW</text><text x="5" y="107" font-size="10">0</text><polyline points="${line('cap_kw')}" fill="none" stroke="#ae6e55" stroke-width="1.5" stroke-dasharray="6 4"/><polyline points="${line('grid_kw')}" fill="none" stroke="#355e7c" stroke-width="2"/><polyline points="${line('solar_kw')}" fill="none" stroke="#bd9f6b" stroke-width="1.5"/><path d="M${x(tick)} 18v89" stroke="#243b4e" stroke-width="1"/></svg>`;
}
function validationDetails(run){
 const checks=run.validation.checks??run.validation.coverage,violations=run.validation.violations??run.validation.errors??run.validation.issues;
 const features=run.instance.feature_status;
 return `${checks?`<h3 style="margin-top:18px">SUPPLIED CHECKER COVERAGE</h3><ul class="trace-checks">${(Array.isArray(checks)?checks:Object.entries(checks).map(([key,value])=>`${key}: ${typeof value==='object'?JSON.stringify(value):value}`)).map(check=>`<li>${safe(typeof check==='object'?JSON.stringify(check):check)}</li>`).join('')}</ul>`:''}${Array.isArray(violations)&&violations.length?`<div class="evidence-warning">${violations.length} supplied violation(s). ${safe(JSON.stringify(violations.slice(0,5)))}</div>`:''}${run.validation.unsupported?.length?`<details class="feature-details evidence-warning"><summary>${run.validation.unsupported.length} unsupported checks / mechanisms</summary><ul class="trace-checks">${run.validation.unsupported.map(item=>`<li>${safe(item)}</li>`).join('')}</ul></details>`:''}${features?`<details class="feature-details"><summary>Implemented / unsupported features</summary><dl>${Object.entries(features).map(([key,value])=>`<div><dt>${safe(key.replaceAll('_',' '))}</dt><dd>${safe(value)}</dd></div>`).join('')}</dl></details>`:''}`;
}
const fact=(label,value)=>`<div class="fact-row"><span>${safe(label)}</span><strong>${safe(value)}</strong></div>`;
function renderInspector(){
 const inspected=selected?.source==='b'&&comparison?comparison:trace;
 $('#clear-selection').hidden=!selected;
 $('.inspector').classList.toggle('has-selection',Boolean(selected)||overlay==='energy');
 const state=snapshot(inspected,tick),metrics=metricsAt(inspected,tick);
 if(!selected){$('#inspector-content').innerHTML=`<h2>${inspected.provenance.kind==='blueprint'?'Factory layout':'Factory state'}</h2><p>${inspected.provenance.kind==='blueprint'?'Load a trace to see activity.':'Select a machine, robot or part.'}</p><div class="fact-grid">${inspected.metrics.orders!==undefined?fact('Terminal shipped',`${inspected.metrics.shipped??'?'} / ${inspected.metrics.orders}`):''}${inspected.metrics.total_tardiness_ticks!==undefined?fact(deadlineEvidence(inspected).label,`${tardinessMinutes(inspected).toLocaleString()} min`):''}${fact('Machines',inspected.resources.machines.length)}${fact('AGVs',inspected.resources.agvs.length)}${fact('Workers',inspected.resources.workers.length)}${fact('Tool IDs in run',inspected.resources.tools.length)}${fact('Processing now',inspected.provenance.kind==='blueprint'?'—':metrics.active)}${fact('Operations finished',inspected.provenance.kind==='blueprint'?'—':`${metrics.completed} / ${metrics.operations}`)}</div><h3>${overlay==='energy'?'ENERGY':'MATERIAL FLOW'}</h3><p class="quiet">${overlay==='energy'?state.energy?`Grid ${safe(state.energy.grid_kw)} / ${safe(state.energy.cap_kw)} kW. Solar ${safe(state.energy.solar_kw??'not supplied')} kW. Battery SOC ${safe(state.energy.soc??'not supplied')}.`:'This trace contains no energy telemetry.':inspected.operations.length?'Mint marks active processing. Amber markers are parts or loaded cargo. Robot travel follows recorded move intervals.':'Housing + rotor + flange → assembly → final inspection → shipment.'}</p>${state.events.length?`<h3>REVEALED EVENTS</h3><ul class="route-list">${state.events.slice(-3).map(event=>`<li>${safe(event.type)}<small>${formatTime(event.tick)} · ${safe(event.resource_id)}</small></li>`).join('')}</ul>`:''}`;return;}
 if(selected.kind==='agv'){
 const agv=inspected.resources.agvs.find(row=>row.id===selected.id);if(!agv)return;
 const move=state.moves.find(row=>row.agv_id===agv.id),previous=inspected.moves.filter(row=>row.agv_id===agv.id&&row.end<=tick).sort((a,b)=>b.end-a.end)[0];
 const loaded=move&&Boolean(move.unit_id)&&move.pickup_tick<=tick&&tick<move.drop_tick;
 const robotState=!move?'Parked':move.kind==='charge'?tick>=(move.charge_start??move.end)?'Charging':'Heading to charger':loaded?'Carrying cargo':move.unit_id?'Empty / awaiting pickup':'Empty repositioning';
 $('#inspector-content').innerHTML=`<h2>${safe(agv.id)}</h2><p>Battery-powered transport robot</p>${fact('State',robotState)}${move?`${fact('From → to',`${move.from} → ${move.to}`)}${fact('Recorded move',`${formatTime(move.start)} → ${formatTime(move.end)}`)}${move.unit_id?`${fact('Cargo type',move.entity_type??'part')}<h3>${loaded?'ON BOARD':'ASSIGNED CARGO'}</h3>${move.entity_type==='tool'?`<p>${safe(move.unit_id)}</p>`:`<button class="unit-link" data-unit="${safe(move.unit_id)}">${safe(move.unit_id)} ↗</button>`}${fact('Pickup / drop',`${formatTime(move.pickup_tick)} / ${formatTime(move.drop_tick)}`)}`:fact('Task',move.kind==='charge'?'Recharge · no cargo':'Empty robot movement')}`:fact('Last recorded stop',previous?.to??agv.initial_location??'not supplied')}<p class="quiet">Routes follow recorded graph-leg intervals. Floor distances and machine mechanisms are schematic.</p>`;
 }else if(selected.kind==='machine'){
 const machine=inspected.resources.machines.find(row=>row.id===selected.id);if(!machine)return;
 const occupancy=resourceOccupancy(inspected,tick).buffers.find(row=>row.machine_id===machine.id);const status=machineStatus(inspected,machine.id,tick),op=status.operation,units=[...state.location].filter(([,location])=>location===machine.id).map(([unit])=>unit);
 $('#inspector-content').innerHTML=`<h2>${safe(machine.id)}${comparison?` <small>${selected.source==='b'?'B':'A'}</small>`:''}</h2><p>Hall ${safe(machine.hall??'?')} · ${safe(processName(machine.process))}</p>${fact('State',status.state)}${fact('Here + incoming',`${occupancy?.input.length??0} + ${occupancy?.reserved.length??0} / ${machine.input_capacity??'?'}`)}${fact('Awaiting pickup',occupancy?.output.length??0)}${op?`${fact('Operation',op.id)}${fact('Mode',op.mode??'not supplied')}${fact('Assigned crew',op.worker_ids.join(', ')||'not supplied')}${fact('Shared tools',op.tool_ids.join(', ')||'not supplied')}<h3>PROCESSING</h3><button class="unit-link" data-unit="${safe(op.unit_id)}">${safe(op.unit_id)} ↗</button><p>${formatTime(op.start)} → ${formatTime(op.end)}</p>`:'<p>No processing activity at this time.</p>'}${units.length?`<h3>RECORDED PARTS</h3>${units.map(unit=>`<button class="unit-link" data-unit="${safe(unit)}">${safe(unit)} ↗</button>`).join('<br>')}`:''}<p class="quiet">Buffer occupancy, setups and blocked status require explicit trace records; idle does not certify availability.</p>`;
 }else{
 const genealogy=unitGenealogy(inspected,selected.id);
 $('#inspector-content').innerHTML=`<h2>${safe(selected.id)}</h2><p>Recorded location: ${safe(state.location.get(selected.id)??'not supplied')}</p>${genealogy.parents.length?`<h3>ASSEMBLY LINEAGE</h3><div class="genealogy"><div class="parents">${genealogy.parents.map(unit=>`<button class="unit-link" data-unit="${safe(unit)}">${safe(unit)}</button>`).join('')}</div><span>→</span><strong>${safe(selected.id)}</strong></div>`:''}${genealogy.children.length?`<h3>CONSUMED BY</h3>${genealogy.children.map(unit=>`<button class="unit-link" data-unit="${safe(unit)}">${safe(unit)} ↗</button>`).join('')}`:''}<h3>OPERATION ROUTE</h3><ol class="route-list">${genealogy.operations.map(op=>`<li class="${op.start<=tick&&tick<op.end?'active':''}">${safe(op.process??op.id)} / ${safe(op.machine_id)}<small>${formatTime(op.start)} → ${formatTime(op.end)} · ${op.end<=tick?'finished':op.start<=tick?'processing':'planned'}</small></li>`).join('')}</ol>`;
 }
}
function runReading(run){
 const context=run.provenance.viewer_replay,m=run.metrics,measured=run.provenance.kind==='measured',hasCounts=Number.isFinite(m.shipped)&&Number.isFinite(m.orders),left=hasCounts?Math.max(0,m.orders-m.shipped):null;
 const completion=completionRecord(run);
 const title=hasCounts?`${m.shipped} of ${m.orders} orders reached shipping.`:run.provenance.kind==='blueprint'?'A design layout, awaiting a measured run.':'A display trace with limited supplied evidence.';
 return `<section class="run-reading"><span class="eyebrow">FINAL RESULT / ${safe(run.provenance.kind.toUpperCase())} / ${numberForReading(run.horizon_ticks*run.tick_minutes/60)} HOUR CUTOFF</span><h3>${safe(title)}</h3>${context?`<p class="run-reading-limit"><strong>${safe(context.label)}</strong>. ${safe(context.horizon_scope)} ${context.posthoc_audit_only?'Extra posthoc audit execution; excluded from the 256-tape estimates and predeclared replay counts. The original frozen evaluation row remains included. ':''}<a href="${safe(context.evidence_url)}" target="_blank" rel="noopener">Trace, certificate and fresh checker digests ↗</a></p>`:''}<p>${hasCounts?left?`${left} order${left===1?' remains':'s remain'} unshipped at the cutoff.`:'Every realized order shipped by the cutoff. Late deliveries still count as shipped.':measured?'Shipment counts were not supplied for this trace.':'This view is not a measured success claim.'}</p><dl>${completion.completionTick!==null?`<div><dt>All orders shipped at · factory time</dt><dd>${factoryDuration(completion.completionTick,run.tick_minutes)}</dd></div>`:''}<div><dt>Left unshipped</dt><dd>${left??'—'}</dd></div><div><dt>${safe(deadlineEvidence(run).label)}</dt><dd>${m.total_tardiness_ticks!==undefined?numberForReading(tardinessMinutes(run)):'—'}</dd></div><div><dt>Supplied physical checks</dt><dd>${validationPassed(run)?'Passed':safe(run.validation.status)}</dd></div>${context?`<div><dt>Model total cost</dt><dd>${numberForReading(m.total_cost)}</dd></div>`:''}</dl><p class="run-reading-limit">${safe(deadlineEvidence(run).explanation)} ${deadlineEvidence(run).incomplete&&deadlineEvidence(run).deliveredOnlyMinutes!==null?`Delivered-only tardiness: ${numberForReading(deadlineEvidence(run).deliveredOnlyMinutes)} minutes. `:''}A passed checker establishes its declared physical checks. It does not establish optimality or on-time delivery.${run.validation.unsupported?.length?` ${run.validation.unsupported.length} unsupported mechanisms are disclosed below.`:''}</p></section>`;
}
const numberForReading=value=>Number(value).toLocaleString('en',{maximumFractionDigits:1});
function renderEvidence(){
 $('#provenance').innerHTML=`<div class="provenance-grid">${[trace,...(comparison?[comparison]:[])].map((run,index)=>{const p=run.provenance;const fields=[['Run',run.run_id],['Data kind',p.kind],['Controller',p.viewer_replay?.selection?.method_id??p.solver??'not supplied'],['Instance',p.instance??'not supplied'],['Code revision',p.code_revision??'not supplied'],['Instance SHA256',p.instance_sha256??'not supplied'],['Selector',p.weights?.selector??'not supplied'],['Generated',p.generated_at??'not supplied'],['Checker status',run.validation.status],['Schema',run.schema]];return `<div class="provenance-run"><h3>${comparison?`${index?'B':'A'} / `:''}${safe(run.run_id)}</h3>${runReading(run)}<details class="reading-details provenance-details"><summary>Trace provenance, checker coverage and limits</summary><dl>${fields.map(([label,value])=>`<div><dt>${safe(label)}</dt><dd>${safe(value)}</dd></div>`).join('')}</dl>${p.kind!=='measured'||!validationPassed(run)?`<div class="evidence-warning">${safe(p.description??'This trace has not been established as an independently validated measured result.')}</div>`:''}${Object.keys(run.metrics).length?`<h3 style="margin-top:18px">SUPPLIED RUN METRICS</h3><dl>${Object.entries(run.metrics).map(([key,value])=>`<div><dt>${safe(key)}</dt><dd>${safe(typeof value==='object'?JSON.stringify(value):value)}</dd></div>`).join('')}</dl>`:''}${validationDetails(run)}</details></div>`;}).join('')}</div>`;
}
function setText(selector,text){const element=$(selector);if(element.textContent!==String(text))element.textContent=text;}
function playbackUI(){document.body.dataset.playing=String(playing);setText('#play',playing?'Ⅱ Pause':'▶ Play');}
function renderRunProgress(){
 const progress=completionAt(trace,tick),panel=$('#run-progress');
 document.body.dataset.productionComplete=String(progress.complete);
 panel.hidden=!progress.total;panel.dataset.complete=String(progress.complete);
 const preset=replayPreset(trace);
 setText('#run-progress-source',preset?'RECORDED CLASSICAL CONTROLLER':trace.provenance.kind==='synthetic'?'DISPLAY FIXTURE':'RECORDED EXECUTION');
 setText('#run-progress-title',progress.complete?`✓ All ${progress.total} orders shipped`:progress.atCutoff?`${progress.shipped} / ${progress.total} shipped · cutoff reached`:`${progress.shipped} / ${progress.total} orders shipped`);
 $('.run-finish-time').hidden=!progress.complete;
 if(progress.complete){setText('#run-finish-time',factoryDuration(progress.completionTick,trace.tick_minutes));setText('#run-finish-context',`Factory time · ${factoryDuration(trace.horizon_ticks,trace.tick_minutes)} cutoff`);}
 setText('#show-finish',progress.complete?'Run result ↗':progress.completionTick!==null?'Show finish →':'Show cutoff →');
 const meter=panel.querySelector('.shipment-meter');meter.setAttribute('aria-valuemin',0);meter.setAttribute('aria-valuemax',progress.total);meter.setAttribute('aria-valuenow',progress.shipped);meter.querySelector('i').style.width=`${progress.shipped/progress.total*100}%`;
 if(tourIndex>=0&&tourChapters[tourIndex].id==='completion'&&progress.complete){setText('#tour-title','All orders shipped.');setText('#tour-description',`Final shipment: ${factoryDuration(progress.completionTick,trace.tick_minutes)}. Factory cutoff: ${factoryDuration(trace.horizon_ticks,trace.tick_minutes)}.`);}
}
$('#show-finish').addEventListener('click',()=>{
 const progress=completionAt(trace,tick);if(progress.complete){setView('evidence');return;}
 const index=tourChapters.findIndex(chapter=>chapter.id==='completion');
 if(index>=0){goTour(index);setTourAuto(false);tick=tourChapters[index].end;}
 else{exitTour(false);tick=progress.completionTick??trace.horizon_ticks;}
 playing=false;lastFrame=0;draw(true);
});
function renderRobotRoster(state){
 const robots=trace.resources.agvs.map(agv=>{const move=state.moves.find(row=>row.agv_id===agv.id),pose=move?transportPose(move,tick,transportPoint):null;const status=!move?'Idle':move.kind==='charge'&&tick>=(move.charge_start??move.end)?'Charging':pose.moving?'Moving':'At dock';return {id:agv.id,label:agv.id.replace(/^AGV/,'R'),status};});
 const signature=JSON.stringify(robots);if(signature===rosterSignature)return;rosterSignature=signature;
 const hadFocus=$('#robot-roster').contains(document.activeElement),focusId=document.activeElement.dataset?.agv;
 $('#robot-roster').innerHTML='<span>Robots</span>'+robots.map(robot=>`<button data-agv="${safe(robot.id)}" data-state="${safe(robot.status)}" aria-label="Inspect ${safe(robot.id)}: ${safe(robot.status)}"><i></i><strong>${safe(robot.label)}</strong><span>${safe(robot.status)}</span></button>`).join('');
 if(hadFocus)[...$('#robot-roster').querySelectorAll('button')].find(button=>button.dataset.agv===focusId)?.focus({preventScroll:true});
}
function renderActivity(state){
 renderRobotRoster(state);
 const active=state.active.filter(op=>!op.kind||op.kind==='process'),focus=active.find(op=>selected?.kind==='machine'&&selected.id===op.machine_id||selected?.kind==='unit'&&op.unit_ids.includes(selected.id))??active[0];
 const shipped=state.events.filter(event=>event.type==='ship').length;
 const travelling=state.moves.filter(move=>transportPose(move,tick,transportPoint).moving).length,charging=state.moves.filter(move=>move.kind==='charge'&&tick>=(move.charge_start??move.end)).length;
 setText('#live-processing',active.length);setText('#live-transport',state.moves.length);setText('#live-shipped',shipped);setText('#tour-shipped',shipped);
 const completion=completionAt(trace,tick);
 setText('#floor-live-state',completion.complete?'PRODUCTION COMPLETE':trace.provenance.kind==='blueprint'?'DESIGN BLUEPRINT':playing?'REPLAY PLAYING':'REPLAY PAUSED');
 setText('#floor-live-action',completion.complete?`Final shipment at ${factoryDuration(completion.completionTick,trace.tick_minutes)} of factory time.`:trace.provenance.kind==='blueprint'?'Load a trace.':focus?`${focus.machine_id} · ${processName(focus.process)} ${focus.unit_id.split('/').slice(0,2).join(' / ')}`:travelling?`${travelling} robot${travelling===1?'':'s'} moving.`:charging?`${charging} robot${charging===1?'':'s'} charging.`:state.moves.length?'Robots at docks.':tick>=trace.horizon_ticks?'Run cutoff':'Waiting for the next activity');
}
function draw(full=false){
 document.body.dataset.selected=String(Boolean(selected));document.body.dataset.overlay=overlay;
 setText('#geometry-note',overlay==='people'?'Recorded crew and tool assignments':overlay==='energy'?'Recorded power and modes':'Replay data · schematic floor');
 const state=renderFloor(trace,'#floor-a');if(comparison)renderFloor(comparison,'#floor-b');renderActivity(state);renderRunProgress();playbackUI();
 if(tourIndex>=0){const chapter=tourChapters[tourIndex];$('#tour-progress').style.width=`${Math.min(100,Math.max(0,(tick-chapter.start)/(chapter.end-chapter.start)*100))}%`;setText('#tour-state',tick>=chapter.end?'Clip complete':playing?'Playing clip':'Paused');}
 const now=performance.now();if(full||!playing||now-lastDetails>220){renderInspector();renderTelemetry();renderStory(state);lastDetails=now;}
 setText('#time',formatTime(tick));setText('#horizon',`/ ${Math.round(Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0)*trace.tick_minutes/60)} h`);$('#scrub').value=tick;
 if(full)renderTimeline();else{const cursor=$('#timeline-cursor'),horizon=Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0),x=74+tick/horizon*1006;if(cursor){const height=28+(trace.resources.machines.length+(comparison?.resources.machines.length??0))*20+12;cursor.setAttribute('d',`M${x} 17v${height-25}`);}}
}
function compactRunStatus(run){
 if(run.provenance.kind==='blueprint')return 'Layout only';
 if(run.provenance.kind==='synthetic')return 'Display fixture · unvalidated';
 const m=run.metrics,hasCounts=Number.isFinite(m.shipped)&&Number.isFinite(m.orders),left=hasCounts?Math.max(0,m.orders-m.shipped):0;
 const preset=replayPreset(run);
 return [run.provenance.viewer_replay?.posthoc_audit_only?'AUDIT ONLY · EXCLUDED FROM ESTIMATES':'',preset?'Classical · final tape 10004':'',run.provenance.kind!=='measured'?'Unverified trace':'',hasCounts&&!preset?`${m.shipped}/${m.orders} shipped`:'',left&&!preset?`${left} unfinished`:'',preset?`${preset.hours} h`:'',validationPassed(run)?'checker passed':`checker ${run.validation.status}`].filter(Boolean).join(' · ');
}
function load(run){exitTour(false);trace=run;const preset=replayPreset(run);$('#replay-preset').value=preset?.id??'custom';document.body.dataset.replayRole=preset?'final':run.provenance.kind;rosterSignature='';tourChapters=buildFactoryTour(run);followOrder=orderIds(run)[0]??'';storySignature='';$('#story-order').innerHTML=orderIds(run).map(id=>`<option>${safe(id)}</option>`).join('');$('#order-story').hidden=!followOrder;$('#order-empty').hidden=Boolean(followOrder);setText('#order-empty-copy',run.provenance.kind==='blueprint'?'Load a trace to replay work and deliveries.':'No order IDs in this trace.');$('#tour-start').disabled=!tourChapters.length;const picker=$('#run-select');const imported=picker.querySelector('[value=loaded]');if(imported)imported.remove();if(trace.provenance.kind==='blueprint')picker.value='blueprint';else if(trace.provenance.kind==='synthetic')picker.value='fixture';else{picker.add(new Option(preset?`Final · ${preset.orders} orders / ${preset.hours} h`:'Imported execution','loaded'));picker.value='loaded';}tick=0;playing=false;selected=null;$('#run-name').textContent=preset?`Classical · ${preset.orders} orders / ${preset.hours} h`:trace.run_id;$('#run-name').title=runLabel(trace);$('#play').disabled=!trace.operations.length&&!trace.moves.length;$('#play').textContent='▶ Play';$('#evidence-status').textContent=trace.provenance.kind==='measured'?`${trace.provenance.viewer_replay?.posthoc_audit_only?'AUDIT ONLY · EXCLUDED FROM ESTIMATES · ':''}MEASURED · ${validationPassed(trace)?'CHECKER PASSED':String(trace.validation.status).toUpperCase()}${trace.metrics.all_orders_fulfilled===false?` · ${trace.metrics.shipped??'?'} / ${trace.metrics.orders??'?'} SHIPPED · INCOMPLETE`:trace.metrics.all_orders_fulfilled===true?` · ${trace.metrics.shipped}/${trace.metrics.orders} SHIPPED`:''}${tardinessMinutes(trace)>0?` · ${deadlineEvidence(trace).label.toUpperCase()} ${tardinessMinutes(trace).toLocaleString()} MIN`:''}`:`${trace.provenance.kind.toUpperCase()} · NO MEASURED RESULTS`;setText('#presentation-status',compactRunStatus(run));$('#run-provenance').textContent=preset?`Recorded ${preset.method} execution · tape 10004`:trace.provenance.solver??trace.provenance.description??'Imported trace';$('#floor-counts').textContent=`${trace.resources.machines.length} machines · ${new Set(trace.resources.machines.map(m=>m.hall)).size} halls · ${trace.resources.agvs.length} robots`;$('#clock-note').textContent=trace.operations.length?`${trace.tick_minutes} min / tick · Space to play`:'No activity trace loaded';setComparisonUI();draw(true);renderEvidence();}
function setComparisonUI(){const enabled=Boolean(comparison);$('#comparison-column').hidden=!enabled;$('#label-a').hidden=!enabled;$('#close-comparison').hidden=!enabled;$('#floors').classList.toggle('comparing',enabled);$('#label-a').textContent=`A / ${runLabel(trace)}`;$('#label-b').textContent=comparison?`B / ${runLabel(comparison)} · ${comparison.provenance.kind} · ${comparison.validation.status}${comparison.metrics.all_orders_fulfilled===false?' · incomplete':''}`:'';$('#scrub').max=Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0);}
function togglePlay(){if($('#play').disabled)return;tourHoldUntil=0;if(tourIndex>=0&&!playing&&tick>=tourChapters[tourIndex].end)tick=tourChapters[tourIndex].start;if(!playing&&tick>=Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0))tick=0;playing=!playing;lastFrame=0;playbackUI();draw();}
function selectTarget(event){
 const unit=event.target.closest('[data-unit]'),machine=event.target.closest('[data-machine]'),agv=event.target.closest('[data-agv]'),operation=event.target.closest('[data-operation]');
 const source=operation?operation.dataset.run==='1'?'b':'a':event.target.closest('#comparison-column')?'b':event.target.closest('.inspector')?selected?.source??'a':'a';
 if((agv||unit||machine||operation)&&presenting){exitTour(false);setPresentation(false);}
 if(agv)selected={kind:'agv',id:agv.dataset.agv,source};
 else if(unit)selected={kind:'unit',id:unit.dataset.unit,source};
 else if(machine)selected={kind:'machine',id:machine.dataset.machine,source};
 else if(operation){const run=source==='b'?comparison:trace;const op=run?.operations.find(row=>row.id===operation.dataset.operation);if(!op)return;tick=op.start;selected={kind:'unit',id:op.unit_id,source};setView('factory');}
 else return;
 draw(true);
}
document.addEventListener('click',selectTarget);document.addEventListener('keydown',event=>{if((event.key==='Enter'||event.key===' ')&&event.target.matches('[data-machine],[data-unit],[data-agv],[data-operation]')){event.preventDefault();selectTarget(event);}else if(event.code==='Space'&&['factory','ledger'].includes($('main').dataset.record)&&!document.querySelector('dialog[open]')&&!event.target.matches('button,input,select,a')){event.preventDefault();togglePlay();}});
function setView(view){
 if(view!=='factory'){exitTour(false);if(presenting)setPresentation(false);}
 const url=new URL(location.href);url.searchParams.set('view',view);if(view!=='research')url.searchParams.delete('section');history.replaceState(null,'',url);
 $('main').dataset.record=view;
 $('#ledger').hidden=view!=='ledger';$('#evidence').hidden=view!=='evidence';
 $('#research').hidden=view!=='research';if(view==='research'){playing=false;playbackUI();mountResearch($('#research'));}
 if(view==='factory'&&!factoryVisited){factoryVisited=true;if(!reducedMotion.matches&&!$('#play').disabled){playing=true;lastFrame=0;playbackUI();}}
 document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===view)));
}
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
let cameraZoom=1,cameraX=0,cameraY=0,cameraDrag=null;
const camera=$('#floors');
function applyCamera(){camera.classList.toggle('zoomed',cameraZoom>1);camera.style.setProperty('--camera-zoom',cameraZoom);camera.style.setProperty('--camera-x',`${cameraX}px`);camera.style.setProperty('--camera-y',`${cameraY}px`);$('#zoom-fit').textContent=cameraZoom===1?'Fit':`${Math.round(cameraZoom*100)}%`;$('#zoom-out').disabled=cameraZoom<=1;$('#zoom-in').disabled=cameraZoom>=2.4;}
$('#zoom-in').addEventListener('click',()=>{cameraZoom=Math.min(2.4,cameraZoom+.2);applyCamera();});
$('#zoom-out').addEventListener('click',()=>{cameraZoom=Math.max(1,Math.round((cameraZoom-.2)*10)/10);if(cameraZoom===1)cameraX=cameraY=0;applyCamera();});
$('#zoom-fit').addEventListener('click',()=>{cameraZoom=1;cameraX=cameraY=0;applyCamera();});
camera.addEventListener('pointerdown',event=>{if(cameraZoom===1||event.target.closest('[role="button"]')||event.button!==0)return;cameraDrag={x:event.clientX,y:event.clientY,startX:cameraX,startY:cameraY};camera.setPointerCapture(event.pointerId);camera.classList.add('dragging');});
camera.addEventListener('pointermove',event=>{if(!cameraDrag)return;const limitX=Math.max(camera.clientWidth*(cameraZoom-1)/2,Math.abs(cameraDrag.startX)),limitY=Math.max(camera.clientHeight*(cameraZoom-1)/2,Math.abs(cameraDrag.startY));cameraX=Math.max(-limitX,Math.min(limitX,cameraDrag.startX+event.clientX-cameraDrag.x));cameraY=Math.max(-limitY,Math.min(limitY,cameraDrag.startY+event.clientY-cameraDrag.y));applyCamera();});
function endCameraDrag(){cameraDrag=null;camera.classList.remove('dragging');}
camera.addEventListener('pointerup',endCameraDrag);camera.addEventListener('pointercancel',endCameraDrag);
document.addEventListener('keydown',event=>{if(event.key==='Escape'){if(document.querySelector('dialog[open]'))return;exitTour(false);if(presenting)setPresentation(false);selected=null;setView('factory');draw(true);}});
applyCamera();
$('#replay-preset').addEventListener('change',event=>{const preset=FINAL_REPLAYS.find(row=>row.id===event.target.value);if(!preset)return;const url=new URL(location.href);url.searchParams.set('trace',preset.path);url.searchParams.delete('compare');url.searchParams.delete('mode');location.assign(url);});
$('#run-select').addEventListener('change',event=>load(event.target.value==='fixture'?fixture():blueprint()));
$('#play').addEventListener('click',togglePlay);$('#restart').addEventListener('click',()=>{exitTour(false);tick=0;draw();});$('#scrub').addEventListener('input',event=>{exitTour(false);tick=Number(event.target.value);draw();});
$('#clear-selection').addEventListener('click',()=>{selected=null;draw(true);});$('#close-comparison').addEventListener('click',()=>{comparison=null;setComparisonUI();draw(true);renderEvidence();});
document.querySelectorAll('[data-overlay]').forEach(button=>button.addEventListener('click',()=>{overlay=button.dataset.overlay;document.querySelectorAll('[data-overlay]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));draw();}));
$('#provenance-button').addEventListener('click',()=>setView('evidence'));
$('#fullscreen').addEventListener('click',()=>{setPresentation(!presenting);if(presenting&&tourChapters.length){setTourAuto(!reducedMotion.matches);goTour(0);}else if(!presenting)exitTour();});
for(const suffix of ['a','b']){$(`#import-${suffix}`).addEventListener('click',()=>$(`#file-${suffix}`).click());$(`#file-${suffix}`).addEventListener('change',async event=>{try{const file=event.target.files[0];if(!file)return;const run=normalizeTrace(JSON.parse(await file.text()));if(suffix==='b'){if(run.tick_minutes!==trace.tick_minutes)throw new Error('Comparison traces must use the same tick duration.');comparison=run;setComparisonUI();draw(true);renderEvidence();}else load(run);$('#message').textContent=`Loaded ${file.name}. Display shape checked; inspect Run evidence.`;}catch(error){$('#message').textContent=`Trace not loaded: ${error.message}`;}event.target.value='';});}
$('#export').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(trace.raw,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`${trace.run_id.replace(/[^a-z0-9-]/gi,'_')}.json`;link.click();URL.revokeObjectURL(url);});
function exitTour(redraw=true){
 if(tourIndex<0)return;setTourAuto(false);tourHoldUntil=0;const url=new URL(location.href);url.searchParams.delete('tour');history.replaceState(null,'',url);tourIndex=-1;playing=false;lastFrame=0;cameraZoom=1;cameraX=cameraY=0;applyCamera();$('#floor-tour').hidden=true;$('#speed').disabled=false;$('#speed').value=savedSpeed;$('#speed').querySelector('[value="guided"]')?.remove();document.body.dataset.tour='false';playbackUI();if(redraw)draw(true);
}
function focusTour(chapter){
 const floor=$('#floor-a'),scale=Math.min(floor.clientWidth/1190,floor.clientHeight/520);
 let target=point(chapter.selection.id);
 if(chapter.selection.kind==='agv'){
  const move=trace.moves.find(row=>row.agv_id===chapter.selection.id&&row.start<=chapter.start&&chapter.start<row.end);
  if(move){const pose=transportPose(move,(chapter.start+chapter.end)/2,transportPoint);target=[pose.x,pose.y];}
 }else if(chapter.selection.kind==='unit'){
  const delivery=trace.moves.find(row=>row.unit_id===chapter.selection.id&&row.drop_tick===chapter.end);target=point(delivery?.to??'SHIP_B');
 }
 if(presenting&&chapter.id==='parts'&&innerWidth>780)target=[595,310];
 const stationZoom=Math.min(2.2,Math.max(1.65,1.15/scale,floor.clientHeight/(520*scale)*.94));
 cameraZoom=presenting?(innerWidth<=780?2.1:chapter.id==='parts'?1:stationZoom):(innerWidth<=780?1.8:1.55);
 const limitX=Math.max(0,(1190*scale*cameraZoom-floor.clientWidth)/2),limitY=Math.max(0,(520*scale*cameraZoom-floor.clientHeight)/2);
 cameraX=Math.max(-limitX,Math.min(limitX,(595-target[0])*scale*cameraZoom));cameraY=Math.max(-limitY,Math.min(limitY,(310-target[1])*scale*cameraZoom));applyCamera();
}
const tourResize=new ResizeObserver(()=>{if(tourIndex>=0)focusTour(tourChapters[tourIndex]);});tourResize.observe(camera);
function goTour(index){
 if(!tourChapters.length)return;
 const url=new URL(location.href);url.searchParams.set('tour','1');history.replaceState(null,'',url);
 if(tourIndex<0){savedSpeed=$('#speed').value;$('#speed').add(new Option('Guided','guided'));}
 tourIndex=Math.max(0,Math.min(tourChapters.length-1,index));tourHoldUntil=0;const chapter=tourChapters[tourIndex];
 tick=chapter.start;selected=chapter.selection;playing=tourAuto||!reducedMotion.matches;lastFrame=0;
 if(chapter.orderId&&followOrder!==chapter.orderId){followOrder=chapter.orderId;$('#story-order').value=followOrder;storySignature='';}
 overlay='flow';document.querySelectorAll('[data-overlay]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.overlay==='flow')));
 $('#speed').value='guided';$('#speed').disabled=true;$('#floor-tour').hidden=false;document.body.dataset.tour='true';
 const station=chapter.selection.kind==='machine'?trace.resources.machines.find(row=>row.id===chapter.selection.id):null;
 setText('#tour-position',`${String(tourIndex+1).padStart(2,'0')} / ${String(tourChapters.length).padStart(2,'0')}${station&&chapter.id!=='parts'?` · HALL ${station.hall}`:''}`);
 setText('#tour-title',chapter.title);setText('#tour-description',chapter.description);setText('#tour-window',`${formatTime(chapter.start)} → ${formatTime(chapter.end)}`);
 const chapterHadFocus=$('#tour-chapters').contains(document.activeElement);
 $('#tour-chapters').innerHTML=tourChapters.map((row,i)=>`<button data-chapter="${i}" aria-label="Moment ${i+1}: ${safe(row.title)}" aria-current="${i===tourIndex?'step':'false'}"><span>${i+1}</span><small>${({parts:'Parts',sharing:'Queue',transport:'Bridge',assembly:'Build',inspection:'Check',shipment:'Ship',completion:'Finish'})[row.id]??row.id}</small></button>`).join('');
 if(chapterHadFocus)$('#tour-chapters').querySelector('[aria-current=step]')?.focus({preventScroll:true});
 $('#tour-previous').disabled=tourIndex===0;setText('#tour-next',tourIndex===tourChapters.length-1?'Run result ↗':'Next →');
 focusTour(chapter);draw(true);
}
$('#tour-start').addEventListener('click',()=>{setPresentation(true);goTour(0);});
$('#tour-close').addEventListener('click',()=>exitTour());
$('#tour-previous').addEventListener('click',()=>goTour(tourIndex-1));
$('#tour-next').addEventListener('click',()=>{if(tourIndex===tourChapters.length-1){exitTour(false);tick=Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0);selected=null;draw(true);setView('evidence');}else goTour(tourIndex+1);});
function renderStory(state){
 if(!followOrder)return;
 const journey=orderJourney(trace,followOrder,tick,state.location),{components,phase,deadline}=journey;
 const remaining=deadline?Math.ceil(Math.abs(deadline.difference)*trace.tick_minutes):0,duration=remaining>=60?`${Math.floor(remaining/60)}h ${remaining%60}m`:`${remaining}m`;
 setText('#story-deadline',deadline?`Due ${formatTime(deadline.due)} · ${deadline.shipped?deadline.difference<0?`shipped ${duration} late`:'shipped on time':deadline.difference<0?`${duration} late so far`:`${duration} left`}`:'Deadline not supplied in this trace');
 $('#story-deadline').dataset.late=String(Boolean(deadline&&deadline.difference<0));
 const signature=JSON.stringify([followOrder,phase,components.map(row=>[row.finished,row.current?.id,row.location,row.consumed]),journey.shipped?.tick]);
 if(signature===storySignature)return;storySignature=signature;
 const short={T:'Turn',F:'Mill',S:'Weld',WASH:'Wash',HEAT:'Heat',QA:'Check',ASSEMBLY:'Build'};
 const name=phase==='unreleased'?'This order has not arrived yet':phase==='shipped'?'This pump reached shipping':phase==='scrapped'?'This pump was scrapped':phase==='assembly'?'The parts become one pump':phase==='awaiting-inspection'?'Built. Final inspection is next.':phase==='rework'?'The pump needs rework':phase==='awaiting-rework'?'Inspection found a defect':phase==='inspection'?'Checking the assembled pump':phase==='delivery'?'Inspected. Shipping is next.':components.length===3?'Three parts, separate recipes':`${components.length} parts, separate recipes`;
 const phaseIndex=phase==='shipped'?3:['inspection','delivery','awaiting-inspection','rework','awaiting-rework','scrapped'].includes(phase)?2:phase==='assembly'?1:0;
 $('#story-content').innerHTML=`<div class="story-status ${phase==='shipped'?'is-delivered':''}"><span>${phase==='shipped'?'✓ ORDER SHIPPED':phase==='scrapped'?'ORDER SCRAPPED':'ORDER IN PROGRESS'}</span><h3>${safe(name)}</h3></div><ol class="story-pipeline">${['Parts','Assemble','Inspect','Ship'].map((label,i)=>`<li class="${i<phaseIndex||phase==='shipped'?'done':i===phaseIndex?'current':''}"><i>${i<phaseIndex||phase==='shipped'?'✓':i+1}</i>${label}</li>`).join('')}</ol><div class="story-components">${components.map(row=>{
 const where=phase==='unreleased'?'Not released yet':row.consumed?journey.assembly.end<=tick?'Used in pump':'In assembly':row.current?`${processName(row.current.process)} at ${row.current.machine_id}`:row.location?.startsWith('AGV')?`On robot ${row.location.slice(3)}`:['STOCK','RAW_A'].includes(row.location)?'At stock':row.location?`Waiting at ${row.location}`:'Awaiting first operation';
 return `<article title="${safe(where)}" class="story-component ${row.current?'component-working':''} ${row.consumed?'component-consumed':''}"><div class="component-icon">${partGlyph(row.kind)}</div><div><div class="component-title"><strong>${safe(row.kind)}</strong><span>${row.consumed?'✓':row.finished+'/'+row.steps.length+' steps'}</span></div><small>${safe(where)}</small><div class="component-recipe" aria-label="Recorded recipe">${row.steps.map(op=>`<span class="${op.end<=tick?'done':op.start<=tick&&tick<op.end?'current':''}" title="${safe(processName(op.process))} at ${safe(op.machine_id)}: ${formatTime(op.start)}–${formatTime(op.end)}">${safe(short[op.process]??op.process)}</span>`).join('')}</div></div></article>`;
 }).join('')}</div>${journey.pump?`<div data-built="${Boolean(journey.assembly&&journey.assembly.end<=tick)}" class="story-pump ${phase==='shipped'?'is-delivered':''}">${partGlyph('pump')}<div><strong>${safe(journey.pump.split('/')[0])} pump</strong><small>${phase==='shipped'?`Shipped at ${formatTime(journey.shipped.tick)}`:phase==='unreleased'?'Not released yet.':phase==='components'?'Waiting for parts.':phase==='assembly'?'Assembling.':phase==='rework'?'Reworking.':phase==='awaiting-rework'?'Check failed. Awaiting rework.':phase==='scrapped'?'Scrapped. No shipment recorded.':phase==='inspection'?'Inspecting.':phase==='awaiting-inspection'?'Awaiting inspection.':'Awaiting shipping.'}</small></div></div>`:''}`;
}
function setTourAuto(enabled){tourAuto=enabled;$('#tour-auto').setAttribute('aria-pressed',String(enabled));setText('#tour-auto',enabled?'Ⅱ Hold':'Auto-play');if(!enabled)tourHoldUntil=0;}
function setPresentation(enabled){
 if(enabled&&$('main').dataset.record!=='factory')setView('factory');
 presenting=enabled;document.body.dataset.presentation=String(enabled);
 const url=new URL(location.href);if(enabled)url.searchParams.set('present','1');else url.searchParams.delete('present');history.replaceState(null,'',url);
 $('#fullscreen').setAttribute('aria-pressed',String(enabled));$('#fullscreen').setAttribute('aria-label',enabled?'Exit presentation':'Present factory');$('#fullscreen span').textContent=enabled?'Exit presentation':'Present factory';
 if(enabled){$('.inspector').insertBefore($('#floor-tour'),$('#order-story'));highlightOrder=true;}
 else{$('.world').insertBefore($('#floor-tour'),$('#floors'));highlightOrder=false;}
 $('#story-highlight').setAttribute('aria-pressed',String(highlightOrder));setText('#story-highlight',highlightOrder?'Show all orders':'Highlight order');
 if(tourIndex>=0)focusTour(tourChapters[tourIndex]);draw(true);
}
$('#story-order').addEventListener('change',event=>{exitTour(false);selected=null;followOrder=event.target.value;storySignature='';draw(true);});
$('#story-highlight').addEventListener('click',()=>{highlightOrder=!highlightOrder;$('#story-highlight').setAttribute('aria-pressed',String(highlightOrder));setText('#story-highlight',highlightOrder?'Show all orders':'Highlight order');draw();});
$('#next-activity').addEventListener('click',()=>{exitTour(false);tick=nextActivityTick(trace,tick);lastFrame=0;draw(true);});
$('#tour-replay').addEventListener('click',()=>{goTour(tourIndex);playing=true;draw();});
$('#tour-auto').addEventListener('click',()=>{setTourAuto(!tourAuto);if(tourAuto){if(tick>=tourChapters[tourIndex].end)goTour(tourIndex===tourChapters.length-1?0:tourIndex+1);else{playing=true;lastFrame=0;draw();}}else{playing=false;draw();}});
$('#tour-chapters').addEventListener('click',event=>{const button=event.target.closest('[data-chapter]');if(button)goTour(Number(button.dataset.chapter));});
document.addEventListener('keydown',event=>{
 if(event.target.matches('input,select,textarea')||document.querySelector('dialog[open]'))return;
 if(tourIndex>=0&&(event.key==='ArrowRight'||event.key==='ArrowLeft')){event.preventDefault();goTour(tourIndex+(event.key==='ArrowRight'?1:-1));}

});

function frame(now){
 if(playing&&!document.hidden){
  const finish=completionRecord(trace).completionTick;
  const max=tourIndex>=0?tourChapters[tourIndex].end:!comparison&&finish!==null&&tick<finish?finish:Math.max(trace.horizon_ticks,comparison?.horizon_ticks??0);
  if(lastFrame)tick+=Math.min(.2,(now-lastFrame)/1000)*(tourIndex>=0?tourRate(tourChapters[tourIndex]):Number($('#speed').value));lastFrame=now;
  const ended=tick>=max;
  if(ended){tick=max;playing=false;if(tourAuto&&tourIndex>=0&&tourIndex<tourChapters.length-1)tourHoldUntil=now+1600;else if(tourAuto)setTourAuto(false);}
  if(ended||now-lastDraw>16){draw();lastDraw=now;}
 }else{
  lastFrame=0;
  if(!document.hidden&&tourAuto&&tourHoldUntil&&now>=tourHoldUntil)goTour(tourIndex+1);
 }
 requestAnimationFrame(frame);
}
load(trace);requestAnimationFrame(frame);
const requestedTrace=new URLSearchParams(location.search).get('mode')==='blueprint'?null:(new URLSearchParams(location.search).get('trace')??DEFAULT_REPLAY);
if(requestedTrace){
 try{load(normalizeTrace(await fetchLinkedTrace(requestedTrace,location.href)));$('#message').textContent='Linked trace loaded. Inspect independent checker status and fulfillment in Run evidence.';}
 catch(error){$('#message').textContent=`Linked trace not loaded: ${error.message}`;}
}

const requestedComparison=new URLSearchParams(location.search).get('compare');
if(requestedComparison){
 try{const run=normalizeTrace(await fetchLinkedTrace(requestedComparison,location.href));if(run.tick_minutes!==trace.tick_minutes)throw new Error('Comparison traces must use the same tick duration.');comparison=run;setComparisonUI();draw(true);renderEvidence();}
 catch(error){$('#message').textContent=`Comparison not loaded: ${error.message}`;}
}
const requestedView=new URLSearchParams(location.search).get('view');setView(['factory','ledger','evidence','research'].includes(requestedView)?requestedView:'factory');
reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches){playing=false;playbackUI();draw();}});



const presentationRequested=new URLSearchParams(location.search).get('present')==='1';
if((presentationRequested||new URLSearchParams(location.search).get('tour')==='1')&&$('main').dataset.record==='factory'){setPresentation(true);if(tourChapters.length){setTourAuto(presentationRequested&&!reducedMotion.matches);goTour(0);}}
