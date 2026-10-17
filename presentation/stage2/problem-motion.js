// A deliberately schematic teaching animation, separate from measured replay data.
const steps = [
  ['Make the components', 'A housing, rotor and flange follow their own processing steps.'],
  ['Bring the parts together', 'Robots bring accepted parts together. Assembly waits until all three arrive.'],
  ['Assemble one pump', 'Only matching, accepted components can become a finished pump.'],
  ['Inspect, then ship', 'An assembled pump counts as delivered only after inspection and transport.'],
];
const clamp = value => Math.max(0, Math.min(1, value));
const ease = value => { const t=clamp(value); return t*t*(3-2*t); };
const mix = (a,b,t) => a+(b-a)*ease(t);
const part = (kind) => kind==='housing'
  ? '<path d="M-20-15H12L22-5V15H-20Z"/><circle cx="0" cy="0" r="9"/>'
  : kind==='rotor' ? '<path d="M-24-5H24V5H-24Z"/><circle r="13"/><path d="M0-18V18M-18 0H18"/>'
  : '<path d="M-16-16H16V16H-16Z"/><circle r="10"/><circle cx="-12" cy="-12" r="1"/><circle cx="12" cy="12" r="1"/>';
const pump = '<path d="M-26 15H27V23H-26ZM-19 1H18V15H-19ZM-6-26H11V-9H-6ZM13-7H34V5H13Z"/><circle cy="-4" r="19"/><circle cy="-4" r="9"/><path d="M-8-10L7 1M7-10L-8 1"/>';

export function problemWalkthrough(){
 return `<section class="problem-motion" aria-label="Animated pump production walkthrough">
  <div class="motion-topline"><span><i aria-hidden="true"></i> ONE ORDER, FROM PARTS TO DELIVERY</span><span>SCHEMATIC · ILLUSTRATION ONLY</span></div>
  <div class="motion-stage"><svg class="production-animation" viewBox="0 0 900 330" role="img" aria-label="Three component routes converge at assembly, followed by final inspection and shipping">
   <defs><pattern id="motion-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#d7eeec" stroke-opacity=".06"/></pattern><linearGradient id="machine-metal" x2="0" y2="1"><stop stop-color="#7395a8"/><stop offset="1" stop-color="#3b596e"/></linearGradient></defs>
   <rect width="100%" height="100%" fill="url(#motion-grid)"/>
   <g class="production-routes"></g>
   <g class="component-machines">${['housing','rotor','flange'].map((kind,i)=>`<g data-machine="${i}" class="component-machine"><ellipse cy="25" rx="49" ry="10" class="machine-shadow"/><path d="M-45-22L-32-34H36L46-22V27H-45Z" class="machine-shell"/><path d="M-45-22H46M30-22V27" class="machine-seam"/><rect x="-34" y="-13" width="49" height="29" rx="3" class="machine-window"/><g class="machine-tool"><path d="M-10-12V-3M-17-12H-3"/></g><path d="M35-11H39M35-3H39" class="machine-light"/><g class="machine-workpiece" transform="translate(-9 7) scale(.35)">${part(kind)}</g><text x="-63" y="-7" text-anchor="end" class="component-name">${['Housing','Rotor','Flange'][i]}</text><text x="-63" y="12" text-anchor="end" class="component-sub">${['01 / BODY','02 / SHAFT','03 / JOINT'][i]}</text></g>`).join('')}</g>
   <g class="assembly-station"><ellipse cy="37" rx="64" ry="14" class="machine-shadow"/><path d="M-58-33L-43-47H44L59-33V39H-58Z" class="machine-shell"/><path d="M-58-33H59M43-33V39" class="machine-seam"/><rect x="-45" y="-22" width="74" height="49" rx="3" class="assembly-window"/><path d="M-24-21V-8L-9 0M11-21V-9L-4 0" class="assembly-arms"/><circle cx="49" cy="-14" r="3" class="assembly-status"/><g class="assembled-pump" transform="translate(-7 9) scale(.65)">${pump}</g><text y="72" text-anchor="middle" class="station-name">Assembly</text><text y="91" text-anchor="middle" class="station-sub">3 parts → 1 pump</text><g class="waiting-badge"><rect x="-72" y="-80" width="144" height="24" rx="12"/><text y="-64" text-anchor="middle">WAITING FOR FLANGE</text></g></g>
   <g class="inspection-station"><rect x="-23" y="-28" width="46" height="61" rx="4" class="machine-shell"/><path d="M-14 11L-3 22L15-1" class="inspection-check"/><path d="M-27-12H27" class="inspection-scan"/><text y="72" text-anchor="middle" class="station-name">Inspect</text></g>
   <g class="shipping-station"><path d="M-26-5H20L32 9V31H-26Z" class="machine-shell"/><path d="M-18-5V-23H11V-5M21 3H27V12H21" class="machine-seam"/><circle cx="-14" cy="32" r="7" class="truck-wheel"/><circle cx="22" cy="32" r="7" class="truck-wheel"/><text y="72" text-anchor="middle" class="station-name">Ship</text><g class="shipped-badge"><rect x="-48" y="-62" width="96" height="24" rx="12"/><text y="-46" text-anchor="middle">DELIVERED ✓</text></g></g>
   <g class="moving-components">${['housing','rotor','flange'].map((kind,i)=>`<g data-part="${i}" class="moving-part part-${i}"><rect x="-31" y="-23" width="62" height="46" rx="7"/><g>${part(kind)}</g></g>`).join('')}</g>
   <g class="pump-carrier"><ellipse cy="30" rx="34" ry="7" class="machine-shadow"/><path d="M-32 14H32V28H-32Z" class="carrier-base"/><circle cx="-22" cy="29" r="5" class="truck-wheel"/><circle cx="22" cy="29" r="5" class="truck-wheel"/><g class="cargo-pump">${pump}</g></g>
  </svg></div>
  <div class="motion-caption"><div><span class="motion-counter">01 / 04</span><h3 data-motion-title>${steps[0][0]}</h3><p data-motion-description>${steps[0][1]}</p></div><div class="motion-controls"><button data-motion-toggle aria-label="Pause production animation">Ⅱ Pause</button><button data-motion-restart aria-label="Restart production animation">↻ Replay</button></div></div>
  <div class="motion-chapters" role="group" aria-label="Production walkthrough steps">${['Make','Move','Assemble','Ship'].map((label,i)=>`<button data-motion-step="${i}" aria-pressed="${i===0}"><span>0${i+1}</span>${label}<i><b></b></i></button>`).join('')}</div>
 </section>`;
}

// elapsed is illustration time, never a factory timestamp.
export function productionFrame(elapsed){
 const t=Math.max(0,Math.min(16,elapsed)),step=Math.min(3,Math.floor(t/4));
 return {step,progress:clamp((t-step*4)/4),parts:[0,1,2].map(i=>({travel:ease((t-4-(i===2?1.5:0))/2.2),visible:t<9.6})),waiting:t>=5.5&&t<7.8,assembled:t>=9.6,delivery:clamp((t-12)/2.8),shipped:t>=14.8};
}

export function mountProblemMotion(root){
 const scene=root.querySelector('.problem-motion');if(!scene)return ()=>{};
 const svg=scene.querySelector('svg'),reduced=matchMedia('(prefers-reduced-motion: reduce)'),narrow=matchMedia('(max-width: 650px)');
 let elapsed=0,previous=0,frame=0,paused=reduced.matches,visible=false,lastStep=-1;
 let layout;
 const q=selector=>scene.querySelector(selector);
 function geometry(){
  const mobile=narrow.matches;
  layout=mobile?{x:160,ys:[80,190,300],join:374,y:190,inspect:493,ship:490,shipY:330}:{x:190,ys:[72,165,258],join:494,y:165,inspect:655,ship:792,shipY:165};
  const {x,ys,join,y,inspect,ship,shipY}=layout;
  svg.setAttribute('viewBox',mobile?'0 0 600 425':'0 0 900 330');
  scene.querySelectorAll('[data-machine]').forEach((node,i)=>node.setAttribute('transform',`translate(${x} ${ys[i]})`));
  q('.assembly-station').setAttribute('transform',`translate(${join} ${y})`);
  q('.inspection-station').setAttribute('transform',`translate(${inspect} ${y})`);
  q('.shipping-station').setAttribute('transform',`translate(${ship} ${shipY})`);
  q('.production-routes').innerHTML=ys.map((sy,i)=>`<path class="route-track" d="M${x+48} ${sy}H${join-105}Q${join-75} ${sy} ${join-75} ${sy+(y-sy)/2}V${y}H${join-59}"/><path class="route-flow" d="M${x+48} ${sy}H${join-105}Q${join-75} ${sy} ${join-75} ${sy+(y-sy)/2}V${y}H${join-59}" data-route="${i}"/>`).join('')+`<path class="route-track" d="M${join+60} ${y}H${inspect}V${shipY}H${ship}"/><path class="route-flow output-route" d="M${join+60} ${y}H${inspect}V${shipY}H${ship}"/>`;
  draw();
 }
 function draw(){
  const state=productionFrame(elapsed),{x,ys,join,y,inspect,ship,shipY}=layout;
  scene.dataset.step=state.step;scene.dataset.paused=paused;
  if(state.step!==lastStep){lastStep=state.step;q('[data-motion-title]').textContent=steps[state.step][0];q('[data-motion-description]').textContent=steps[state.step][1];q('.motion-counter').textContent=`0${state.step+1} / 04`;}
  scene.querySelectorAll('[data-motion-step]').forEach((node,i)=>{node.setAttribute('aria-pressed',i===state.step);node.style.setProperty('--chapter-progress',`${i<state.step?100:i===state.step?state.progress*100:0}%`);});
  scene.querySelectorAll('[data-part]').forEach((node,i)=>{const t=state.parts[i].travel;node.setAttribute('transform',`translate(${mix(x+52,join-8,t)} ${mix(ys[i],y,t)}) scale(${1-.25*t})`);node.style.opacity=state.parts[i].visible?'1':'0';});
  q('.waiting-badge').style.opacity=state.waiting?'1':'0';q('.assembled-pump').style.opacity=state.assembled&&state.step<3?'1':'0';
  q('.shipped-badge').style.opacity=state.shipped?'1':'0';
  q('.pump-carrier').style.opacity=state.step===3&&!state.shipped?'1':'0';
  const d=state.delivery,first=clamp(d/.48),second=clamp((d-.58)/.42);
  q('.pump-carrier').setAttribute('transform',`translate(${d<.58?mix(join,inspect,first):mix(inspect,ship,second)} ${mix(y,shipY,second)})`);
  q('.inspection-check').style.opacity=state.delivery>.58?'1':'.15';
  q('[data-motion-toggle]').textContent=paused?'▶ Play':'Ⅱ Pause';
  q('[data-motion-toggle]').setAttribute('aria-label',`${paused?'Play':'Pause'} production animation`);
 }
 function run(now){frame=0;if(!visible||paused||root.closest('[hidden]')){previous=0;return;}if(previous)elapsed+=(now-previous)/1000;previous=now;if(elapsed>17.5)elapsed=0;draw();frame=requestAnimationFrame(run);}
 function start(){previous=0;if(!frame&&visible&&!paused)frame=requestAnimationFrame(run);}
 q('[data-motion-toggle]').addEventListener('click',()=>{paused=!paused;draw();start();});
 q('[data-motion-restart]').addEventListener('click',()=>{elapsed=0;paused=reduced.matches;draw();start();});
 scene.querySelectorAll('[data-motion-step]').forEach(button=>button.addEventListener('click',()=>{elapsed=Number(button.dataset.motionStep)*4+2;paused=true;draw();}));
 const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible)start();},{threshold:.15});observer.observe(scene);
 const onReduced=()=>{paused=reduced.matches;draw();start();};
 reduced.addEventListener('change',onReduced);narrow.addEventListener('change',geometry);geometry();
 return ()=>{cancelAnimationFrame(frame);observer.disconnect();reduced.removeEventListener('change',onReduced);narrow.removeEventListener('change',geometry);};
}

export function inspectionFrame(dueFirst,minute){
 const sequence=dueFirst?[{id:'B',start:0,end:20},{id:'A',start:20,end:50}]:[{id:'A',start:0,end:30},{id:'B',start:30,end:50}];
 return sequence.map(row=>({...row,progress:clamp((minute-row.start)/(row.end-row.start)),late:Math.max(0,row.end-(row.id==='B'?40:60))}));
}

export function inspectionTimeline(dueFirst){
 const rows=inspectionFrame(dueFirst,0);
 return `<div class="inspection-clock"><span>ONE INSPECTOR · TWO ORDERS</span><output data-inspection-time>09:00</output><button data-inspection-replay>▶ Watch this order</button></div><div class="inspection-timeline" aria-label="Inspection schedule from 09:00 to 10:00"><div class="inspection-ticks"><span>09:00</span><span>09:20</span><span>09:40</span><span>10:00</span></div><div class="inspection-track">${rows.map(row=>`<div class="inspection-bar pump-${row.id.toLowerCase()}" data-inspection-pump="${row.id}" style="left:${row.start/60*100}%;width:${(row.end-row.start)/60*100}%"><i></i><strong>${row.id}</strong><span>${row.end-row.start} min</span></div>`).join('')}<div class="inspection-deadline"><span>B DUE</span></div><div class="inspection-playhead"></div></div><div class="inspection-status">${rows.map(row=>`<span data-inspection-status="${row.id}">Pump ${row.id} · ${row.late?`${row.late} min late`:'on time'}</span>`).join('')}</div></div>`;
}
export function mountInspection(root,dueFirst){
 const button=root.querySelector('[data-inspection-replay]');if(!button)return ()=>{};
 let frame=0,start=0;
 button.addEventListener('click',()=>{cancelAnimationFrame(frame);start=0;button.disabled=true;button.textContent='Inspecting…';frame=requestAnimationFrame(animate);});
 function animate(now){if(!root.isConnected||root.closest('[hidden]'))return;if(!start)start=now;const minute=Math.min(50,(now-start)/140);
  root.querySelector('[data-inspection-time]').textContent=`09:${String(Math.floor(minute)).padStart(2,'0')}`;
  root.querySelector('.inspection-playhead').style.left=`${minute/60*100}%`;
  for(const row of inspectionFrame(dueFirst,minute)){root.querySelector(`[data-inspection-pump="${row.id}"] i`).style.width=`${row.progress*100}%`;root.querySelector(`[data-inspection-status="${row.id}"]`).textContent=`Pump ${row.id} · ${row.progress>=1?(row.late?`${row.late} min late`:'shipped on time'):minute>=row.start?'inspecting':'waiting'}`;}
  if(minute<50)frame=requestAnimationFrame(animate);else{button.disabled=false;button.textContent='↻ Replay this order';}
 }
 return ()=>cancelAnimationFrame(frame);
}
