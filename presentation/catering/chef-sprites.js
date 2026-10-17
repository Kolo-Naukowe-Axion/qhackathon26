// Native 16 × 24 game sprites: aligned, directional frames with moving limbs.
const COLORS={W1:{apron:'#527747',skin:'#d49b67',hair:'#6a4430'},W2:{apron:'#69869a',skin:'#a77551',hair:'#453831'},W3:{apron:'#b87043',skin:'#edbd86',hair:'#8b5936'}};
export function drawChef(ctx,worker,direction,mode,frame,task=''){
  const c=COLORS[worker],ink='#4a392b',cream='#fff0c5',shadow='#d9c49c';
  const r=(x,y,w,h,color)=>{ctx.fillStyle=color;ctx.fillRect(x,y,w,h);};
  const walk=mode==='walk',work=mode==='work',side=direction==='left'||direction==='right';
  const stride=walk?[1,0,-1,0][frame]:0,hand=work?frame:0;
  ctx.clearRect(0,0,16,24);ctx.save();
  if(direction==='right'){ctx.translate(16,0);ctx.scale(-1,1);}
  // Separate feet and arms make the walk cycle, without rotating the whole cook.
  r(5,19+Math.max(0,-stride),3,4-Math.max(0,-stride),ink);
  r(10,19+Math.max(0,stride),3,4-Math.max(0,stride),ink);
  r(4+(side?stride:0),22+Math.min(0,stride),4,1,ink);
  r(10-(side?stride:0),22+Math.min(0,-stride),4,1,ink);
  r(4,12,9,8,ink);r(5,12,7,7,cream);r(5,18,7,2,shadow);
  if(direction==='up'){r(5,15,7,1,c.apron);r(7,16,3,4,c.apron);}
  else{r(side?5:7,14,side?4:4,6,c.apron);r(6,12,1,4,c.apron);r(10,12,1,4,c.apron);}
  if(side){
    r(3,13+(walk?stride:0),3,5,shadow);r(3,17+(walk?stride:0),2,2,c.skin);
    r(work?1:5,work?13-hand:14-(walk?stride:0),3,4,cream);
    r(work?0:5,work?12-hand:17-(walk?stride:0),2,2,c.skin);
    if(work){r(0,11-hand,3,1,task==='clean'?'#8eb3c0':'#b6b4a2');r(0,10-hand,1,3,task==='clean'?'#8eb3c0':'#816342');}
  }else{
    const ly=work&&direction==='up'?12-hand:13+stride,ry=work&&direction==='up'?11+hand:13-stride;
    r(2,ly,3,4,shadow);r(2,ly+3,2,2,c.skin);r(12,ry,3,4,cream);r(13,ry+3,2,2,c.skin);
    if(work&&task==='prepare')r(13,ry-2,1,4,'#c1c6b6');
    if(work&&task==='pack'){r(2,11+hand,3,3,'#ba8a4f');r(2,11+hand,3,1,'#ead09b');}
  }
  r(4,6,8,7,ink);r(5,7,6,5,c.skin);r(5,6,6,2,c.hair);
  if(direction==='up'){r(5,7,6,5,c.hair);r(6,8,4,2,'#805239');}
  else if(side){r(4,8,2,3,c.skin);r(5,8,1,1,ink);r(9,7,2,4,c.hair);}
  else{r(6,8,1,1,ink);r(10,8,1,1,ink);r(8,10,1,1,'#a16445');}
  // The same hat silhouette and foot anchor in every frame prevent jitter.
  r(5,0,6,1,ink);r(3,1,10,1,ink);r(2,2,12,3,ink);r(3,5,10,2,ink);
  r(5,1,6,1,cream);r(3,2,10,2,cream);r(4,4,8,2,cream);r(4,6,8,1,shadow);
  ctx.restore();
}
export function createChefFrames(){
  const canvas=document.createElement('canvas');canvas.width=16;canvas.height=24;
  const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
  const frames=new Map();
  for(const worker of Object.keys(COLORS))for(const direction of ['up','down','left','right'])for(const mode of ['idle','walk','work']){
    const count=mode==='walk'?4:mode==='work'?2:1;
    for(const task of mode==='work'?['prepare','cook','clean','pack']:[''])for(let frame=0;frame<count;frame++){
      drawChef(ctx,worker,direction,mode,frame,task);frames.set(`${worker}/${direction}/${mode}/${frame}/${task}`,canvas.toDataURL());
    }
  }
  return frames;
}
