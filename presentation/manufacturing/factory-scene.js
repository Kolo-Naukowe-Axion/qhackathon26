import {colors,kind,pump} from './model.js';
import {glyphBody,operationProgress} from '../stage2/factory-parts.js';

// Display geometry only. None of these coordinates are manufacturing distances.
const stations={
 T1:[110,190,'A'],T2:[245,190,'A'],F1:[110,370,'A'],F2:[245,370,'A'],
 WASH1:[110,550,'A'],H1:[245,550,'A'],QA1:[380,550,'A'],
 F3:[590,190,'B'],S1:[700,190,'B'],S2:[810,190,'B'],
 WASH2:[590,370,'B'],H2:[700,370,'B'],QA2:[810,370,'B'],
 A1:[700,550,'B'],A2:[810,550,'B'],H3:[920,370,'B'],F4:[920,190,'B'],
};
const baseline=['T1','T2','F1','F2','WASH1','H1','QA1','F3','S1','S2','WASH2','H2','QA2','A1','A2'];
const process=id=>id.replace(/\d+$/,'');
const processNames={T:'TURNING',F:'MILLING',S:'WELDING',WASH:'WASHING',H:'HEAT TREAT',QA:'INSPECTION',A:'ASSEMBLY'};
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clamp=x=>Math.max(0,Math.min(1,x));
const minutes=value=>`${Math.round(value)}m`;

export function machineAvailability(problem,id,tick){
 const machine=problem.machines[id];
 if(!machine)return{state:'offline',label:'OFFLINE',detail:'Unavailable in this model'};
 const releases=problem.operations.filter(o=>Object.hasOwn(o.durations,id)).map(o=>o.machine_release?.[id]??0);
 const release=releases.length?Math.min(...releases):0;
 const windows=(machine.available??[]).map(([start,end])=>[Math.max(start,release),end]).filter(([start,end])=>start<end);
 const next=windows.find(([start])=>start>tick);
 if(windows.some(([start,end])=>start<=tick&&tick<end))return{state:'idle',label:'IDLE',detail:'No processing at this time'};
 return next?{state:'future',label:`FROM ${minutes(next[0])}`,detail:'Calendar or processing release not yet open'}:
  {state:'closed',label:'CLOSED',detail:'Outside the machine calendar'};
}

function equipment(type,active){
 const screen=active?'#b9e5b0':'#6b9397';
 const feet='<path d="M-37 26v8m74-8v8" stroke="#4c6868" stroke-width="7"/>';
 if(type==='T')return`${feet}<rect x="-45" y="-14" width="90" height="42" rx="7" fill="#6c9b9a"/><rect x="-44" y="-35" width="25" height="36" rx="4" fill="#bfd7cf"/><rect x="21" y="-29" width="23" height="25" rx="3" fill="#bfd7cf"/><path d="M-18-17H23" stroke="#496669" stroke-width="9"/><g class="factory-turn-spindle${active?' is-running':''}"><circle cx="-18" cy="-17" r="10" fill="#e2e7d5" stroke="#496669" stroke-width="3"/><path d="M-26-17h16m-8-8v16" stroke="#496669" stroke-width="2"/></g><rect x="-8" y="6" width="42" height="11" rx="3" fill="#466a6b"/><circle cx="-27" cy="12" r="5" fill="#f3c265"/>`;
 if(type==='F')return`${feet}<rect x="-43" y="-40" width="86" height="68" rx="7" fill="#81a5af"/><path d="M-43-29H43V-40H-35Q-43-40-43-32" fill="#b7d0d1"/><rect x="-31" y="-23" width="49" height="36" rx="4" fill="#304f5a"/><path d="M-5-24v18m-15 20h37" stroke="#b8d2d4" stroke-width="6"/><rect x="24" y="-22" width="12" height="17" rx="2" fill="${screen}"/><circle cx="30" cy="3" r="3" fill="#f4bd62"/><path d="M-30 22H30" stroke="#496977" stroke-width="3"/>`;
 if(type==='S')return`${feet}<rect x="-43" y="-6" width="86" height="31" rx="5" fill="#6e858c"/><path d="M-34-8H30M-25-7v-15l18-15 19 9-7 20" fill="none" stroke="#d89557" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/><circle cx="-8" cy="-35" r="6" fill="#f0bb76"/><circle cx="12" cy="-26" r="5" fill="#4c5d65"/><rect x="26" y="-35" width="14" height="22" rx="3" fill="#afc5bd"/>${active?'<path class="factory-weld-sparks" d="m5-8 4-8m-8 6-6-5m11 10 8-3" stroke="#fff0a3" stroke-width="3" stroke-linecap="round"/>':''}`;
 if(type==='WASH')return`${feet}<rect x="-44" y="-31" width="88" height="59" rx="9" fill="#8eb9bf"/><path d="M-38-31h76l-7-13h-62Z" fill="#c6dfd8"/><rect x="-34" y="-20" width="48" height="31" rx="6" fill="#5f909d"/><path d="M-27-6q8-8 16 0t16 0" fill="none" stroke="#bfe5e5" stroke-width="3"/><circle cx="28" cy="-15" r="5" fill="${screen}"/><path d="M23-1h11m-54 20h29" stroke="#527f8c" stroke-width="4"/>${active?'<circle class="factory-wash-bubbles" cx="-21" cy="-12" r="3" fill="#ddf1e5"/><circle cx="0" cy="-15" r="2" fill="#ddf1e5"/>':''}`;
 if(type==='H')return`${feet}<path d="M-39-37h78v65h-78Z" fill="#b77c59"/><path d="M-39-37h78l-8-12h-62Z" fill="#ddb08a"/><rect x="-28" y="-28" width="56" height="44" rx="9" fill="${active?'#82482f':'#5e6561'}" stroke="#ddb18a" stroke-width="5"/><path d="M-10-48v-12h20v12" fill="#9c866a"/><path d="M-32 25H32" stroke="#795740" stroke-width="4"/><circle cx="33" cy="-11" r="4" fill="${screen}"/>${active?'<path class="factory-heat-glow" d="M-17 7q-8-9 0-20 1 8 6 10 2-8 8-12 0 11 6 16 3 5-2 10" fill="#efa85c" opacity=".8"/>':''}`;
 if(type==='QA')return`${feet}<rect x="-43" y="7" width="86" height="16" rx="4" fill="#9eb99c"/><path d="M-31 6v-40h46v17M-30-34h45" fill="none" stroke="#52796f" stroke-width="8" stroke-linecap="round"/><rect x="7" y="-27" width="16" height="20" rx="3" fill="#c0d6b1"/><circle cx="15" cy="-7" r="5" fill="#567d71"/><rect x="25" y="-4" width="18" height="12" rx="2" fill="${screen}"/><path d="M-29 0H8" stroke="#d8e5c7" stroke-width="3"/>`;
 return`${feet}<rect x="-47" y="-2" width="94" height="18" rx="5" fill="#d3b277"/><path d="M-39 16v13m78-13v13M-33-5v-32h66v32" fill="none" stroke="#577f78" stroke-width="7"/><path d="M-25-28h50M-25-19h50" stroke="#c0d6c3" stroke-width="2"/><circle cx="-18" cy="-21" r="4" fill="#dda56a"/><path d="M14-29v15m-4-7h8" stroke="#edcb7e" stroke-width="4"/>`;
}

function worker(row){
 return`<g class="factory-worker" data-attending-worker="${esc(row.worker)}" transform="translate(43 20)"><title>${esc(row.worker)} attending until ${minutes(row.attended_end)}</title><ellipse cx="0" cy="19" rx="9" ry="4" fill="#5b6c5f" opacity=".25"/><path d="M-5 10v8m10-8v8" stroke="#365666" stroke-width="4" stroke-linecap="round"/><rect x="-7" y="-1" width="14" height="14" rx="5" fill="#638a99"/><circle cy="-6" r="7" fill="#e1b88d"/><path d="M-8-8q0-11 8-11T8-8Z" fill="#f2c76d"/><path d="M-10-8h20" stroke="#d29b44" stroke-width="3" stroke-linecap="round"/></g>`;
}

function station(c,s,id,point,tick,selectedOperation,selectedOrder,selectedMachine){
 const [x,y]=point,type=process(id),active=s.plan.find(r=>r.machine===id&&r.start<=tick&&tick<r.end);
 const selected=selectedMachine?selectedMachine===id:s.plan.find(r=>r.operation===selectedOperation)?.machine===id;
 const av=machineAvailability(c.problem,id,tick),state=active?'active':av.state;
 const part=active?kind(active.operation):null,tint=part?colors[part]:'#6f8d82';
 const muted=active&&selectedOrder&&pump(active.operation)!==selectedOrder;
 const upcoming=s.plan.filter(r=>r.machine===id&&r.start>tick).sort((a,b)=>a.start-b.start)[0];
 const status=active?'RUNNING':av.label,statusColor=active?'#3d8669':state==='offline'?'#a25f49':state==='future'?'#ad7f32':'#71877b';
 const progress=active?clamp(operationProgress(active,tick)):0;
 const aria=`${id}, ${processNames[type]??type}, ${status}${active?`, ${active.operation}, ${Math.round(progress*100)} percent complete`:''}`;
 return`<g class="factory-station factory-station--${state}${selected?' factory-station--selected':''}" data-machine="${esc(id)}" data-machine-state="${state}" tabindex="0" role="button" aria-label="${esc(aria)}" transform="translate(${x} ${y})">
  <title>${esc(aria)}${upcoming?`; next scheduled ${upcoming.operation} at ${minutes(upcoming.start)}`:''}</title>
  <rect class="factory-station-hit" x="-54" y="-68" width="108" height="165" rx="12" fill="${selected?'#fff2c6':'transparent'}" stroke="${selected?'#bc8a35':'transparent'}" stroke-width="2.5"/>
  <ellipse cx="0" cy="32" rx="49" ry="11" fill="#617a6d" opacity=".18"/>
  <rect x="-49" y="-46" width="98" height="80" rx="10" fill="${state==='offline'?'#ded9c9':'#d3ded0'}" stroke="#acbca9"/>
  <path d="M-43 29h86" stroke="${selected?'#d5a647':'#b8c8b5'}" stroke-width="4"/>
  <g opacity="${state==='offline'?.42:state==='future'||state==='closed'?.68:1}">${equipment(type,!!active)}</g>
  ${state==='offline'?'<path d="m-32-30 64 53m-64 0 64-53" stroke="#a66a52" stroke-width="5" opacity=".65"/><rect x="-39" y="-10" width="78" height="19" rx="4" fill="#f3e3cb"/><text x="0" y="3" text-anchor="middle" fill="#80523e" font-size="11" font-weight="800">OFFLINE</text>':''}
  ${active?`<g data-active-operation="${esc(active.operation)}" opacity="${muted?.48:1}" transform="translate(-12 -17) scale(.67)"><rect x="-3" y="-3" width="42" height="42" rx="9" fill="${tint}" stroke="#f4f0df" stroke-width="2"/><g fill="none" stroke="#fff7e9" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${glyphBody(part)}</g></g>${tick<active.attended_end?worker(active):''}`:''}
  <text x="0" y="54" text-anchor="middle" fill="#274b43" font-size="20" font-weight="800">${esc(id)}</text>
  <text x="0" y="70" text-anchor="middle" fill="#526f60" font-size="14" font-weight="700" letter-spacing=".4">${esc(processNames[type]??type)}</text>
  <circle cx="-38" cy="84" r="3.5" fill="${statusColor}"/><text x="-29" y="88" fill="${statusColor}" font-size="11" font-weight="800">${esc(status)}</text>
  ${active?`<rect x="-45" y="99" width="90" height="5" rx="2.5" fill="#becdbb"/><rect data-progress="${progress.toFixed(6)}" x="-45" y="99" width="${(90*progress).toFixed(3)}" height="5" rx="2.5" fill="${tint}"/><text x="0" y="120" text-anchor="middle" fill="#4e6c5d" font-size="11" font-weight="700">${esc(pump(active.operation))} · ${Math.round(progress*100)}%</text>`:
   upcoming&&state!=='offline'?`<text x="0" y="113" text-anchor="middle" fill="#6b7e6c" font-size="10">NEXT ${esc(pump(upcoming.operation))} · ${minutes(upcoming.start)}</text>`:''}
 </g>`;
}

/** Pure SVG renderer. c is a checked case with problem; s.plan is its real
 * schedule. tick is model minutes; selections are operation/order IDs. No DOM,
 * animation clock, network, inferred transport or material-location state. */
export function renderFactoryScene({c,s,tick,selectedOperation=null,selectedOrder=null,selectedMachine=null,playing=false}){
 const ids=[...new Set([...baseline,...Object.keys(c.problem.machines)])];
 const coordinates={...stations};
 for(const [index,id]of ids.filter(id=>!coordinates[id]).entries()){
  const hall=c.problem.machines[id]?.hall??'B';
  coordinates[id]=[(hall==='A'?110:590)+110*(index%3),550+180*Math.floor(index/3),hall];
 }
 const count=hall=>Object.values(c.problem.machines).filter(m=>m.hall===hall).length;
 return`<svg class="factory-scene" data-replay="${playing?'playing':'paused'}" style="--factory-phase:-${tick/30}s" viewBox="0 0 1000 710" role="group" aria-label="Two-hall factory schedule at minute ${Math.round(tick)}. Equipment layout is illustrative; processing and attendance follow the selected schedule." xmlns="http://www.w3.org/2000/svg">
 <defs><pattern id="factory-floor-grid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="#bac9ad" stroke-width=".55"/></pattern><pattern id="factory-hazard" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><rect width="12" height="12" fill="#e9cc78"/><path d="M0 0V12" stroke="#6c705b" stroke-width="5"/></pattern></defs>
 <style>.factory-scene text{font-family:inherit}.factory-scene .factory-station{cursor:pointer;outline:none}.factory-scene .factory-station:focus-visible .factory-station-hit{stroke:#345f70;stroke-width:4;fill:#fff2c6}.factory-scene .factory-station:hover .factory-station-hit{stroke:#89a08b;fill:#f0f0d8}.factory-scene .factory-station--selected:hover .factory-station-hit{stroke:#bc8a35}.factory-scene .factory-turn-spindle.is-running{transform-box:fill-box;transform-origin:center;animation:factory-spindle-turn 2.4s linear infinite}.factory-scene .factory-weld-sparks{animation:factory-process-glow 1.1s ease-in-out infinite alternate}.factory-scene .factory-heat-glow{animation:factory-process-glow 2s ease-in-out infinite alternate}.factory-scene .factory-wash-bubbles{animation:factory-process-glow 1.7s ease-in-out infinite alternate}@keyframes factory-spindle-turn{to{transform:rotate(360deg)}}@keyframes factory-process-glow{from{opacity:.45}to{opacity:.95}}@media(prefers-reduced-motion:reduce){.factory-scene .factory-turn-spindle.is-running,.factory-scene .factory-weld-sparks,.factory-scene .factory-heat-glow,.factory-scene .factory-wash-bubbles{animation:none!important}}</style>
 <rect x="0" y="0" width="1000" height="710" rx="20" fill="#e6ecd8"/>
 <path d="M481 6h38v684h-38Z" fill="#8fa49a"/><path d="M500 12v672" stroke="#e7e9ca" stroke-width="2" stroke-dasharray="13 11"/>
 <path d="M22 690h956v20H22Z" fill="#9eb0a0"/><path d="M36 700h928" stroke="#f4edcf" stroke-width="2" stroke-dasharray="15 11"/>
 ${[['A',25,440,'MACHINING'],['B',535,440,'JOIN + FINISH']].map(([hall,x,width,name])=>`<g><rect x="${x+5}" y="96" width="${width}" height="590" rx="11" fill="#758b72" opacity=".18"/><rect x="${x}" y="87" width="${width}" height="590" rx="11" fill="#d6e0c8" stroke="#a7b69a" stroke-width="2"/><rect x="${x+8}" y="101" width="${width-16}" height="568" rx="5" fill="url(#factory-floor-grid)"/><path d="M${x+4} 115V91Q${x+4} 81 ${x+15} 81H${x+width-15}Q${x+width-4} 81 ${x+width-4} 91V115" fill="none" stroke="#8fae95" stroke-width="12"/><path d="M${x+13} 86H${x+width-13}" stroke="#cad9bf" stroke-width="5"/><rect x="${x+17}" y="28" width="38" height="36" rx="10" fill="#416a58"/><text x="${x+36}" y="54" text-anchor="middle" font-size="24" font-weight="800" fill="#f2f0d7">${hall}</text><text x="${x+69}" y="48" fill="#365944" font-size="20" font-weight="800">${name}</text><text x="${x+69}" y="66" fill="#6b8069" font-size="12">${count(hall)} modeled machines</text><path d="M${x+12} 304H${x+width-12}M${x+12} 484H${x+width-12}" stroke="#ebecd2" stroke-width="16"/><path d="M${x+12} 304H${x+width-12}M${x+12} 484H${x+width-12}" stroke="#b6c4a7" stroke-width="1" stroke-dasharray="6 7"/></g>`).join('')}
 <path d="M455 291h90v27h-90Z" fill="#c1cfb4" stroke="#78977f" stroke-width="2"/><path d="M457 292h86M457 317h86" stroke="#e6d49a" stroke-width="4"/><path d="M476 295v18m12-18v18m12-18v18m12-18v18m12-18v18" stroke="#9bae91" stroke-width="2"/>
 <text x="500" y="275" text-anchor="middle" fill="#5f7868" font-size="10" font-weight="700">HALL LINK</text>
 ${ids.map(id=>station(c,s,id,coordinates[id],tick,selectedOperation,selectedOrder,selectedMachine)).join('')}
 </svg>`.replace(/<text\b([^>]*)>/g,(whole,attributes)=>{
  // Preserve station hierarchy against the legacy #floor text shorthand.
  const styles=['font-size','font-weight','fill','letter-spacing'].flatMap(name=>{
   const value=attributes.match(new RegExp(`${name}="([^"]+)"`))?.[1];
   return value?[`${name}:${value}${name==='font-size'||name==='letter-spacing'?'px':''}`]:[];
  });
  return `<text${attributes}${styles.length?` style="${styles.join(';')}"`:''}>`;
 });
}
