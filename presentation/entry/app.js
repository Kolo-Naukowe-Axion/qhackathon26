const $=s=>document.querySelector(s);
const data=await fetch('data.json').then(r=>{if(!r.ok)throw Error('Evidence unavailable');return r.json()});
const names={qaoa_xy:'QAOA · XY / CVaR .25',uniform_onehot:'Uniform one-hot sampling',sa_onehot:'Classical annealing'};
const labels={'P01/housing':'Housing','P01/rotor':'Rotor','P01/assembly':'Assembly','P01/qa':'Pump QA','urgent/qa':'Urgent QA'};
let active='outage-spare',live=false,busy=false;
function svg(tag,attrs,text){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))el.setAttribute(k,v);if(text!==undefined)el.textContent=text;return el;}
function timeline(problem,decoded){
 const width=1080,left=110,right=25,top=32,row=42,h=problem.horizon;
 const machines=Object.keys(problem.machines).sort();
 const root=svg('svg',{viewBox:`0 0 ${width} ${top+machines.length*row+28}`,role:'img','aria-label':decoded.valid?'Validated machine assignments, in minutes':'Sampled machine assignments with validation issues'});
 const x=t=>left+(width-left-right)*t/h;
 for(let t=0;t<=h;t+=30){root.append(svg('line',{x1:x(t),x2:x(t),y1:top-13,y2:top+machines.length*row,stroke:'#bdcdd3'}));root.append(svg('text',{x:x(t),y:14,'text-anchor':'middle',class:'axis'},`${t}m`));}
 machines.forEach((machine,i)=>{const y=top+i*row;
  root.append(svg('text',{x:0,y:y+22},machine==='QA1'?'QA1 / inspection':machine));
  if(machine==='F1'&&problem.machines.F1.available[0][0]>0){root.append(svg('rect',{x:x(0),y:y+3,width:x(60)-x(0),height:32,fill:'#cbb9aa',opacity:.8}));root.append(svg('text',{x:x(30),y:y+24,'text-anchor':'middle',class:'tiny'},'OUTAGE'));}
  for(const op of decoded.plan.filter(a=>a.machine===machine)){
   const urgent=op.operation==='urgent/qa';const group=svg('g',{});
   group.append(svg('rect',{x:x(op.start)+1,y:y+3,width:Math.max(1,x(op.end)-x(op.start)-2),height:32,fill:urgent?'#9f6d48':'#5c8396'}));
   group.append(svg('text',{x:(x(op.start)+x(op.end))/2,y:y+23,'text-anchor':'middle',style:'fill:#fff;font-size:11px'},`${labels[op.operation]} · ${op.worker==='machinist'?'M':'F'}`));
   group.append(svg('title',{},`${op.operation} · ${op.worker} · ${op.start}–${op.end} min`));root.append(group);
  }
 });
 root.append(svg('text',{x:left,y:top+machines.length*row+22,class:'axis'},'M = machinist · F = finisher · every bar uses its named worker for the full operation'));
 $('#timeline').replaceChildren(root);
}
function render(decoded=null,source=null){
 const c=data.cases[active],d=decoded||c.example;
 $('#tardy').textContent=d.valid?d.weighted_terminal_tardiness:'invalid';
 $('#finish').textContent=d.valid?`${d.makespan}m`:'—';$('#qubits').textContent=c.model.pruned_variables;
 $('#decision').textContent=active==='outage-spare'?'F2 takes the housing. The cross-trained machinist assembles while the finisher handles the urgent inspection. Both deadlines are met.':active==='outage-no-spare'?'Without F2, housing waits for F1. The pump ends at minute 150: 30 minutes late, weighted ×2. The urgent inspection stays on time.':active==='without-cross-skill'?'The finisher must choose between assembly and urgent QA. The best schedule still has 60 weighted late minutes. Cross-training removes that bottleneck.':'Even with both components ready, workers and the shared inspection station determine which operations can run together.';
 if(source&&(!d.valid||d.objective!==c.reference.objective))$('#decision').textContent=d.valid?`This fresh sample is feasible with objective ${d.objective}, above the certified optimum ${c.reference.objective}. The measured plan is shown unchanged.`:'This fresh sampled plan violates a scheduling constraint. No reference plan or repair has replaced it; inspect the saved validation issues.';
 timeline(c.problem,d);
 $('#comparison').replaceChildren(...c.methods.map(m=>{const tr=document.createElement('tr');if(m.method==='qaoa_xy')tr.className='highlight';for(const value of[names[m.method],`${m.valid}/${m.runs}`,`${m.schedule_optimal}/${m.runs}`,`${m.encoded_optimal}/${m.runs}`,`${(m.mean_seconds*1000).toFixed(1)} ms`]){const td=document.createElement('td');td.textContent=value;tr.append(td);}return tr;}));
 $('#run-source').textContent=source?`Fresh local run · seed ${source.seed} · ${source.created_utc}`:'Retained run · first declared TEST seed 101';
 $('#run-detail').textContent=source?`Reference ${source.reference.objective}; measured QUBO energy ${source.result.energy}; schedule objective ${d.objective}. ${source.elapsed_seconds.toFixed(3)} s including preparation + reference.`:`Measured energy ${d.energy}; schedule objective ${d.objective}; independent reference ${c.reference.objective}.`;
}
$('#case').value=active;$('#case').addEventListener('change',()=>{active=$('#case').value;$('#run-status').textContent='';render();});
$('#scaling-rows').replaceChildren(...data.scaling.map(r=>{const tr=document.createElement('tr');for(const value of[r.pumps,r.operations,r.variables.toLocaleString(),r.couplers.toLocaleString(),'No · compiled + CP reference']){const td=document.createElement('td');td.textContent=value;tr.append(td);}return tr;}));
$('#hash').textContent=`Source: ${data.source}\nSHA-256: ${data.source_sha256}`;
$('#run-form').addEventListener('submit',async event=>{
 event.preventDefault();if(!live||busy)return;busy=true;$('#run').disabled=true;$('#case').disabled=true;$('#run').textContent='Simulating…';$('#run-status').textContent='Fresh compile → W state → QAOA → Born sampling → raw schedule check → CP reference';
 try{const response=await fetch('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case:active,seed:Number($('#seed').value)})});const r=await response.json();if(!response.ok)throw Error(r.error||'Run failed');render(r.result.decoded,r);$('#run-status').textContent=`Saved ${r.local_artifact}/result.json · valid ${r.result.decoded.valid} · physical QPU 0 · VeloxQ 0`;}catch(e){$('#run-status').textContent=`Run could not complete: ${e.message}`;}finally{busy=false;$('#run').disabled=false;$('#case').disabled=false;$('#run').innerHTML='Run fresh QAOA <span>↗</span>';}
});
render();
try{const r=await fetch('/api/status');if(r.ok&&r.headers.get('content-type')?.includes('application/json'))live=(await r.json()).enabled===true;}catch{}
$('#run').disabled=!live;$('#run').innerHTML=live?'Run fresh QAOA <span>↗</span>':'Start local Python demo';
if(!live)$('#run-status').textContent='Saved evidence view. Enable fresh local runs with: .venv-stage2/bin/python -m stage2.entry_demo';
