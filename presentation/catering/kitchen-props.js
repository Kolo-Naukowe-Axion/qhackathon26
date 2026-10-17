// Live cookware is drawn on the same 384 × 256 grid as the environment.
import { kitchenVisualState } from './kitchen-state.js';
const r=(ctx,x,y,w,h,color)=>{ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),w,h);};
function pot(ctx,x,y,menu,mode,frame,progress){
  const q=(a,b,w,h,c)=>r(ctx,x+a,y+b,w,h,c);
  q(-11,-5,22,3,'#44414a');q(-12,-3,3,3,'#aaa9a0');q(9,-3,3,3,'#aaa9a0');
  q(-9,-4,18,12,'#393e46');q(-8,-3,16,10,'#8a9497');q(-7,-2,4,8,'#b8c1b6');q(5,-2,3,9,'#646f78');
  q(-9,-6,18,3,'#d2d4c2');q(-7,-5,14,3,mode==='clean'?'#6b706b':menu==='A'?'#df9344':'#b6bd6b');
  if(mode==='cook'){
    for(let i=0;i<4;i++)q(-5+(i*4+frame)%12,-5+((i+frame)%2),2,1,(i+frame)%2?'#f0d68c':'#6c8d43');
    for(let i=0;i<3;i++){const sx=-6+i*6,sy=-12-((frame+i)%3)*2;q(sx,sy,1,3,'#eee5c3');q(sx+1,sy-2,1,2,'#eee5c3');}
    for(let i=0;i<3;i++){q(-7+i*6,17,3,2+(i+frame)%3,'#dc7934');q(-6+i*6,16+(i+frame)%2,1,3,'#f0bd55');}
  }else{
    for(let i=0;i<4;i++){const bx=-5+i*3,by=-5-((frame+i)%3);q(bx,by,3,2,'#dbe8d6');q(bx+1,by-1,1,1,'#87b9c4');}
    if(progress>.5)q(-4,-5,8,1,'#e4ecdc');
  }
}
function prep(ctx,state){
  const q=(x,y,w,h,c)=>r(ctx,x+14,y,w,h,c),p=state.progress;
  q(86,128,32,14,'#80512d');q(87,128,30,12,'#d5a05d');q(88,129,28,1,'#ebba73');
  const chopped=Math.floor(p*8);
  for(let i=0;i<8;i++){
    if(i<chopped)q(91+(i%4)*3,132+Math.floor(i/4)*3,2,2,i%2?'#ce813b':'#7e9946');
    else{q(126+(i%4)*5,130+Math.floor(i/4)*5,4,3,i%2?'#dc9c46':'#597f36');q(127+(i%4)*5,129+Math.floor(i/4)*5,2,1,'#aac66b');}
  }
}
function tray(ctx,x,y,fill,menu){
  r(ctx,x,y,13,9,'#654b36');r(ctx,x+1,y,11,8,'#eee4c5');r(ctx,x+2,y+1,9,6,'#b7b6a0');
  for(let i=0;i<6;i++)if(i/6<fill)r(ctx,x+3+(i%3)*3,y+2+Math.floor(i/3)*3,2,2,menu==='A'?'#dc9749':'#7b9946');
}
function crate(ctx,x,y){r(ctx,x,y,13,9,'#725132');r(ctx,x+1,y,11,7,'#bd8d52');r(ctx,x+1,y,11,2,'#e8bf7c');r(ctx,x+6,y,2,8,'#d9ad6b');}
export function drawKitchenProps(ctx,c,time){
  const state=kitchenVisualState(c,time),frame=Math.floor(time*4)%4;
  for(const id of ['C1','C2']){
    const s=state.stations[id];
    if(s.mode==='cook'||s.mode==='clean')pot(ctx,id==='C1'?144:240,77,s.batch?.menu,s.mode,frame,s.progress);
  }
  if(state.stations.P1.mode==='prepare')prep(ctx,state.stations.P1);
  state.waitingPrep.forEach((b,i)=>{r(ctx,148-i*10,133,8,5,'#68694a');r(ctx,147-i*10,132,10,2,'#dfd4ab');r(ctx,149-i*10,131,6,2,b.menu==='A'?'#d8984a':'#6e9045');});
  const packing=state.stations.K1;
  if(packing.mode==='pack'){
    tray(ctx,258,130,packing.progress,packing.batch.menu);
    tray(ctx,277,130,0,packing.batch.menu);
    r(ctx,263,143,13,2,'#b58a54');r(ctx,264,142,11,1,'#ead1a0');
  }
  state.ready.forEach((a,i)=>crate(ctx,303+(i%3)*12,211-Math.floor(i/3)*8));
  state.departing.forEach((a,i)=>crate(ctx,307+a.progress*28,208-a.progress*7-i*5));
  return state;
}
