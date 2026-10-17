import {allOperations} from './model.js';
// Walking is a display-only transition; it never changes the checked plan.
export const WORKER_SPOTS={P1:[470,668],C1:[662,458],C2:[1042,458],K1:[1090,668]};
export const REST_SPOTS={W1:[680,570],W2:[860,620],W3:[820,450]};
const SPEED=160; // World units per replay minute, not wall-clock seconds.
const same=(a,b)=>a[0]===b[0]&&a[1]===b[1];
const distance=(a,b)=>Math.abs(b[0]-a[0])+Math.abs(b[1]-a[1]);
export function corridorRoute(from,to,lane=760){
  // Parallel lanes keep cooks apart while they cross the central aisle.
  const points=from[0]===to[0]||from[1]===to[1]?[from,to]:[from,[lane,from[1]],[lane,to[1]],to];
  return points.filter((p,i)=>i===0||!same(p,points[i-1]));
}
const length=route=>route.slice(1).reduce((sum,p,i)=>sum+distance(route[i],p),0);
const facing=resource=>resource?.startsWith('C')?'left':'up';

export function buildWorkerTrack(c,worker){
  const rest=REST_SPOTS[worker],horizon=c.instance.horizon_minutes,ops=[];
  const lane={W1:710,W2:750,W3:870}[worker];
  const route=(from,to)=>corridorRoute(from,to,lane);
  for(const raw of allOperations(c).filter(o=>o.worker===worker).sort((a,b)=>a.start-b.start)){
    const o={...raw,end:raw.attended_end},prev=ops.at(-1);
    if(prev&&prev.end===o.start&&prev.resource===o.resource&&prev.kind===o.kind)prev.end=o.end;
    else ops.push(o);
  }
  const segments=[];
  const add=(start,end,mode,from,to=from,op=null)=>{
    if(end<=start)return;
    segments.push({start,end,mode,from,to,route:route(from,to),task:op?.kind??'',resource:op?.resource??'',direction:op?(worker==='W2'&&op.resource.startsWith('C')?'right':facing(op.resource)):'down'});
  };
  let end=0,pos=rest;
  for(const op of ops){
    const station=WORKER_SPOTS[op.resource];
    const target=worker==='W2'&&op.resource.startsWith('C')?[station[0]-168,420]:station,gap=op.start-end;
    if(gap>0){
      const back=length(route(pos,rest))/SPEED,approach=length(route(rest,target))/SPEED;
      if(gap>=back+approach+1){
        add(end,end+back,'walk',pos,rest);
        add(end+back,op.start-approach,'idle',rest);
        add(op.start-approach,op.start,'walk',rest,target);
      }else{
        const duration=Math.min(gap,length(route(pos,target))/SPEED);
        add(end,op.start-duration,'idle',pos);
        add(op.start-duration,op.start,'walk',pos,target);
      }
      pos=target;
    }
    let workStart=op.start;
    if(op.start===0)pos=target; // The replay begins at the first executed action.
    if(!same(pos,target)){
      // The core has no travel times. Keep adjacent handovers visually continuous,
      // with a short illustrative transition at the recorded attendance boundary.
      const duration=Math.min(length(route(pos,target))/SPEED,2.5,(op.end-op.start)/3);
      add(op.start,op.start+duration,'walk',pos,target);
      workStart+=duration;
    }
    add(workStart,op.end,'work',target,target,op);
    end=op.end;pos=target;
  }
  const home=Math.min(horizon-end,length(route(pos,rest))/SPEED);
  add(end,end+home,'walk',pos,rest);add(end+home,horizon,'idle',rest);
  return segments;
}

export function workerPoseAt(track,time){
  const s=track.find(s=>s.start<=time&&time<s.end)??track.at(-1);
  if(!s)return {x:760,y:540,direction:'down',mode:'idle',frame:0,task:''};
  if(time>=s.end)return {x:s.to[0],y:s.to[1],direction:'down',mode:'idle',frame:0,task:''};
  if(s.mode!=='walk')return {x:s.from[0],y:s.from[1],direction:s.direction,mode:s.mode,frame:s.mode==='work'?Math.floor((time-s.start)*3)%2:0,task:s.task};
  const total=length(s.route),travel=total*Math.max(0,Math.min(1,(time-s.start)/(s.end-s.start)));
  let remaining=travel;
  for(let i=1;i<s.route.length;i++){
    const a=s.route[i-1],b=s.route[i],d=distance(a,b);
    if(remaining<=d){const f=d?remaining/d:1,dx=b[0]-a[0],dy=b[1]-a[1];return {x:a[0]+dx*f,y:a[1]+dy*f,direction:Math.abs(dx)>Math.abs(dy)?dx>0?'right':'left':dy>0?'down':'up',mode:'walk',frame:Math.floor(travel/24)%4,task:''};}
    remaining-=d;
  }
  return {x:s.to[0],y:s.to[1],direction:'down',mode:'idle',frame:0,task:''};
}
