import {INSTANCES,permutations,earliestSchedule} from './schedule-model.js';
import {problemWalkthrough,mountProblemMotion} from '../stage2/problem-motion.js';

const $=selector=>document.querySelector(selector);
function setView(view,updateURL=true){
 for(const name of ['concept','math']){const selected=view===name;$(`#${name}`).hidden=!selected;$(`#${name}-tab`).setAttribute('aria-selected',selected);$(`#${name}-tab`).tabIndex=selected?0:-1;}
 if(updateURL)history.replaceState(null,'',`#${view}`);
}
for(const name of ['concept','math']){
 $(`#${name}-tab`).addEventListener('click',()=>setView(name));
 $(`#${name}-tab`).addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?'concept':event.key==='End'?'math':name==='concept'?'math':'concept';setView(next);$(`#${next}-tab`).focus();}});
}
setView(location.hash==='#math'?'math':'concept',false);
let choice=0,orders=[];
function drawSchedule(){
 const instance=INSTANCES[$('#baseline-size').value],order=orders[choice],schedule=earliestSchedule(instance,order),max=Math.max(...orders.map(row=>earliestSchedule(instance,row).makespan));
 $('#schedule-finish').textContent=`${schedule.makespan} h`;
 $('#schedule-orders').innerHTML=orders.map((row,i)=>`<button data-order="${i}" aria-pressed="${choice===i}">${row.join(' → ')}</button>`).join('');
 const x=time=>100+time/max*570;
 $('#schedule-chart').innerHTML=`<svg viewBox="0 0 710 ${instance.machines.length*64+50}" role="img" aria-label="${order.join(' then ')} finishes in ${schedule.makespan} hours">${Array.from({length:max+1},(_,h)=>`<line class="time-grid" x1="${x(h)}" x2="${x(h)}" y1="18" y2="${instance.machines.length*64+8}"/><text class="axis" x="${x(h)}" y="${instance.machines.length*64+30}" text-anchor="middle">${h}</text>`).join('')}${instance.machines.map((name,i)=>`<text class="row-label" x="82" y="${i*64+45}" text-anchor="end">${name}</text>`).join('')}${schedule.operations.map(op=>`<g class="job-${op.job}"><rect x="${x(op.start)}" y="${op.machine*64+23}" width="${x(op.end)-x(op.start)}" height="36" rx="3"/><text x="${(x(op.start)+x(op.end))/2}" y="${op.machine*64+46}" text-anchor="middle">${op.job}</text></g>`).join('')}</svg>`;
}
function resetSchedule(){orders=permutations(INSTANCES[$('#baseline-size').value].jobs.map(row=>row.id));choice=orders.findIndex(row=>row[0]==='Z2');drawSchedule();}
$('#baseline-size').addEventListener('change',resetSchedule);
$('#schedule-orders').addEventListener('click',event=>{const button=event.target.closest('[data-order]');if(button){choice=Number(button.dataset.order);drawSchedule();$('#schedule-orders').querySelector(`[data-order="${choice}"]`).focus({preventScroll:true});}});
resetSchedule();
$('#pump-explanation').innerHTML=problemWalkthrough();mountProblemMotion($('#pump-explanation'));
