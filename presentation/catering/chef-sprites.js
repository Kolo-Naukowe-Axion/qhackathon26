// Keep the 16 × 24 chef at seven world units per pixel. Transparent padding
// gives hand-held tools room to reach the work surface without shrinking the chef.
export const CHEF_FRAME={width:32,height:32,offsetX:8,offsetY:8,worldScale:7,x:-112,y:-224};
export function chefToolPose(direction,task,frame=0){
  const step=frame%2;
  let grip,tip;
  if(direction==='left'||direction==='right'){
    grip=[1,8-step];tip=task==='clean'?[-4+step,5]:[-4+step,-1];
  }else if(task==='prepare'){grip=[14,11+step];tip=[14,5+step];}
  else if(task==='pack'){grip=[3,8-step];tip=[3,6-step];}
  else{grip=[3,11-step];tip=[1,7-step];}
  const mirror=p=>direction==='right'?[16-p[0],p[1]]:p;
  return {grip:mirror(grip),tip:mirror(tip)};
}
const COLORS={W1:{apron:'#527747',skin:'#d49b67',hair:'#6a4430'},W2:{apron:'#69869a',skin:'#a77551',hair:'#453831'},W3:{apron:'#b87043',skin:'#edbd86',hair:'#8b5936'}};
export function drawChef(ctx,worker,direction,mode,frame,task=''){
  const c=COLORS[worker],ink='#4a392b',cream='#fff0c5',shadow='#d9c49c';
  const r=(x,y,w,h,color)=>{ctx.fillStyle=color;ctx.fillRect(x,y,w,h);};
  const walk=mode==='walk',work=mode==='work',side=direction==='left'||direction==='right';
  const stride=walk?[1,0,-1,0][frame]:0,hand=work?frame:0;
  ctx.clearRect(0,0,CHEF_FRAME.width,CHEF_FRAME.height);ctx.save();ctx.translate(CHEF_FRAME.offsetX,CHEF_FRAME.offsetY);
  if(direction==='right'){ctx.translate(16,0);ctx.scale(-1,1);}
  // Separate feet and arms make the walk cycle, without rotating the whole cook.
  r(5,19+Math.max(0,-stride),3,4-Math.max(0,-stride),ink);
  r(10,19+Math.max(0,stride),3,4-Math.max(0,stride),ink);
  r(4+(side?stride:0),22+Math.min(0,stride),4,1,ink);
  r(10-(side?stride:0),22+Math.min(0,-stride),4,1,ink);
  r(4,12,9,8,ink);r(5,12,7,7,cream);r(5,18,7,2,shadow);
  if(direction==='up'){r(5,15,7,1,c.apron);r(7,16,3,4,c.apron);}
  else{r(side?5:7,14,side?4:4,6,c.apron);r(6,12,1,4,c.apron);r(10,12,1,4,c.apron);}
  const line=(from,to,color)=>{
    const steps=Math.max(Math.abs(to[0]-from[0]),Math.abs(to[1]-from[1]));
    for(let i=0;i<=steps;i++)r(Math.round(from[0]+(to[0]-from[0])*i/Math.max(1,steps)),Math.round(from[1]+(to[1]-from[1])*i/Math.max(1,steps)),1,1,color);
  };
  if(side){
    r(3,13+(walk?stride:0),3,5,shadow);r(3,17+(walk?stride:0),2,2,c.skin);
    if(work){
      const {grip,tip}=chefToolPose('left',task,frame);
      // The raised forearm, hand and handle share the same pixel anchor.
      r(3,12,3,3,cream);r(1,10,3,3,cream);r(0,8-hand,2,3,c.skin);
      line(grip,tip,task==='clean'?'#658894':'#88613d');
      r(grip[0],grip[1],2,2,c.skin);
      if(task==='clean'){r(tip[0]-1,tip[1]-1,3,2,'#8fc0cc');r(tip[0]-1,tip[1]-1,3,1,'#d8e8d3');}
      else{r(tip[0]-1,tip[1]-1,3,2,'#bdbba4');r(tip[0],tip[1],1,1,'#6e7952');}
    }else{
      r(5,14-stride,3,4,cream);r(5,17-stride,2,2,c.skin);
    }
  }else{
    let ly=13+stride,ry=13-stride;
    if(work&&direction==='up'){
      ly=task==='pack'?5-hand:12-hand;
      ry=task==='prepare'?8+hand:11+hand;
    }
    r(2,ly,3,4,shadow);r(2,ly+3,2,2,c.skin);r(12,ry,3,4,cream);r(13,ry+3,2,2,c.skin);
    if(work&&task==='prepare'){
      const {grip,tip}=chefToolPose(direction,task,frame);
      r(grip[0],grip[1]-2,1,3,'#69452d');r(tip[0],tip[1],2,4,'#c1c6b6');
      r(grip[0]-1,grip[1],2,2,c.skin);
    }
    if(work&&task==='pack'){
      const {grip,tip}=chefToolPose(direction,task,frame);
      r(tip[0]-2,tip[1]-1,4,3,'#ba8a4f');r(tip[0]-2,tip[1]-1,4,1,'#ead09b');
      r(grip[0]-1,grip[1],2,1,c.skin);
    }
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
  const canvas=document.createElement('canvas');canvas.width=CHEF_FRAME.width;canvas.height=CHEF_FRAME.height;
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
