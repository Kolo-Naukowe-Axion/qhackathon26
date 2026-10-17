// Display geometry only. Recorded graph-leg times and pickup/drop boundaries
// remain authoritative; the aisles are a schematic, not measured dimensions.
export function aislePath(from,to){
 const points=[from,[from[0],260],[to[0],260],to];
 return points.filter((p,i)=>i===0||p[0]!==points[i-1][0]||p[1]!==points[i-1][1]);
}
export function samplePath(points,fraction){
 const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1]));
 let distance=lengths.reduce((a,b)=>a+b,0)*Math.max(0,Math.min(1,fraction));
 for(let i=0;i<lengths.length;i++){
  if(lengths[i]&&distance<=lengths[i]){const ratio=distance/lengths[i],a=points[i],b=points[i+1];return {x:a[0]+(b[0]-a[0])*ratio,y:a[1]+(b[1]-a[1])*ratio,angle:Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI};}
  distance-=lengths[i];
 }
 const p=points.at(-1)??[0,0];return {x:p[0],y:p[1],angle:0};
}
export function transportPath(move,point){
 if(move.legs?.length)return move.legs.flatMap((leg,i)=>aislePath(point(leg.from),point(leg.to)).slice(i?1:0));
 if(Array.isArray(move.path)&&move.path.length&&move.path.every(p=>Array.isArray(p)&&p.length===2))return move.path;
 return aislePath(point(move.from),point(move.to));
}
export function activeTransportPath(move,tick,point){
 if(!move.legs?.length)return tick>=move.start&&tick<move.end?transportPath(move,point):[];
 const leg=move.legs.find(row=>row.start<=tick&&tick<row.end);
 return leg?aislePath(point(leg.from),point(leg.to)):[];
}
// Unwrap bearings so SVG transitions take the shortest turn across ±180°.
export function nearestHeading(previous,target){
 return previous+((target-previous+180)%360+360)%360-180;
}
export function transportPose(move,tick,point){
 const loaded=Boolean(move.unit_id)&&move.pickup_tick<=tick&&tick<move.drop_tick;
 if(move.legs?.length){
  const leg=move.legs.find(row=>row.start<=tick&&tick<row.end);
  if(leg)return {...samplePath(aislePath(point(leg.from),point(leg.to)),(tick-leg.start)/(leg.end-leg.start)),loaded,moving:true};
  const done=move.legs.filter(row=>row.end<=tick).at(-1),p=point(done?.to??move.legs[0].from);
  return {x:p[0],y:p[1],angle:0,loaded,moving:false};
 }
 return {...samplePath(transportPath(move,point),(tick-move.start)/(move.end-move.start)),loaded,moving:true};
}
export const processName=process=>({T:'Turning',F:'Milling',S:'Welding',WASH:'Washing',HEAT:'Heat treatment',QA:'Inspection',ASSEMBLY:'Assembly'}[process]??process??'Processing');

// These are illustrative mechanisms, shown only while the trace says processing.
export function machineEffect(process){
 const group=(name,content)=>`<g class="process-effect ${name}" aria-hidden="true">${content}</g>`;
 if(process==='T')return group('turning-effect','<g class="spinning-chuck"><circle cx="-8" cy="-25" r="9"/><path d="M-8-34v18m-9-9h18M-14-31l12 12m-12 0 12-12"/></g><path class="lathe-feed" d="M18-35v14h-9"/>');
 if(process==='F')return group('milling-effect','<g class="mill-head"><path d="M0-40v18"/><path class="mill-bit" d="M-6-23h12m-10 4h8"/></g><g class="cutting-chips"><path d="M-7-18l-6 5m20-5 6 5m-13-1v5"/></g>');
 if(process==='S')return group('welding-effect','<circle class="weld-glow" cx="6" cy="-18" r="13"/><g class="weld-sparks"><path d="M6-33v7M6-10v7M-9-18h7m16 0h7M-5-29l5 5m12 12 5 5m-22 0 5-5m12-12 5-5"/></g><circle cx="6" cy="-18" r="3"/>');
 if(process==='WASH')return group('washing-effect','<g class="wash-bubbles"><circle cx="-14" cy="-20" r="3"/><circle cx="1" cy="-25" r="2.5"/><circle cx="15" cy="-19" r="3"/></g><path class="wash-water" d="M-20-17q6-4 12 0t12 0t12 0"/>');
 if(process==='HEAT')return group('heat-effect','<rect class="furnace-glow" x="-19" y="-34" width="38" height="23" rx="2"/><g class="heat-shimmer"><path d="M-13-40q-4-4 0-8M1-40q-4-4 0-8M15-40q-4-4 0-8"/></g>');
 if(process==='QA')return group('qa-effect','<path class="qa-scan" d="M-16-42h32"/><path class="qa-wave" d="M-9-32h5l3-7 5 11 4-4h4"/><path class="workpiece-scan" d="M-15-19h30"/>');
 if(process==='ASSEMBLY')return group('assembly-effect','<g class="assembly-arm-left"><path d="M-24-36v13l16 8"/><circle cx="-24" cy="-23" r="3"/></g><g class="assembly-arm-right"><path d="M24-36v13l-16 8"/><circle cx="24" cy="-23" r="3"/></g>');
 return '';
}

// Keep unchanged SVG nodes alive so CSS animation, focus and hover survive replay.
export function reconcileSVG(layer,cache,records){
 const retained=new Set();
 for(const record of records){
  const {key,signature}=record;
  retained.add(key);let entry=cache.get(key);
  if(!entry||entry.signature!==signature){
   const holder=document.createElementNS('http://www.w3.org/2000/svg','g');holder.innerHTML=record.markup;
   const node=holder.firstElementChild;
   const focused=entry?.node.contains(document.activeElement),focusUnit=focused?document.activeElement.getAttribute('data-unit'):null;
   if(entry)entry.node.replaceWith(node);else layer.append(node);
   entry={node,signature};cache.set(key,entry);
   if(focused){const replacement=focusUnit?[...node.querySelectorAll('[data-unit]')].find(el=>el.getAttribute('data-unit')===focusUnit):node;(replacement??node).focus({preventScroll:true});}
  }
 }
 for(const [key,entry] of cache)if(!retained.has(key)){entry.node.remove();cache.delete(key);}
}
