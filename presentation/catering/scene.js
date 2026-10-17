// A 384 × 256 game world, with overlays in the same 1536 × 1024 coordinate system.
import { REST_SPOTS } from './worker-motion.js';
import { createChefFrames } from './chef-sprites.js';
import { drawKitchenProps } from './kitchen-props.js';
let worldContext,worldBackdrop;
let chefFrames;
const stations={P1:{x:470,y:477,box:[300,480,340,174],name:'PREP'},C1:{x:575,y:422,box:[515,270,130,135],name:'COOKER'},C2:{x:960,y:422,box:[895,270,130,135],name:'COOKER'},K1:{x:1085,y:477,box:[940,480,300,174],name:'PACK'}};
function station(id,s){
  const pinY=id.startsWith('C')?398:636;
  return `<g id="station-${id}" class="station" data-station="${id}" role="button" tabindex="0" aria-label="Inspect ${id}, ${s.name.toLowerCase()}"><rect class="station-hitbox" x="${s.box[0]}" y="${s.box[1]}" width="${s.box[2]}" height="${s.box[3]}" fill="transparent" pointer-events="all"/><rect class="station-halo" x="${s.box[0]-5}" y="${s.box[1]-5}" width="${s.box[2]+10}" height="${s.box[3]+10}"/><rect class="offline-shade" x="${s.box[0]}" y="${s.box[1]}" width="${s.box[2]}" height="${s.box[3]}"/><g class="offline-mark" transform="translate(${s.x} 319)"><path d="M-18-18h36v36h-36z" fill="#843d2f" stroke="#e9b46c" stroke-width="4"/><path d="M-8-8l16 16m0-16L-8 8" stroke="#fff0ba" stroke-width="5"/></g><g class="station-pin" transform="translate(${s.x} ${pinY})"><path d="M-23-9h46v18h-46z" fill="#523c2b" stroke="#b9945e" stroke-width="2"/><rect class="state-dot" x="-16" y="-2" width="4" height="4"/><text x="4" y="4" text-anchor="middle">${id}</text></g><g class="station-detail" transform="translate(${s.x} ${s.y-40})"><path d="M-88-20h176v42H-88z" fill="#f1d8a5" stroke="#6b4b2d" stroke-width="3"/><text class="station-title" text-anchor="middle" y="-4">${id} / ${s.name}</text><text id="status-${id}" class="station-status" text-anchor="middle" y="13">Idle</text></g></g>`;
}
function chef(id,color){const [x,y]=REST_SPOTS[id];return `<g id="chef-${id}" class="chef" transform="translate(${x} ${y})"><path d="M-18-1h36v6h-36z" fill="#55382b" opacity=".3"/><g class="chef-body"><image class="chef-sprite" x="-24" y="-72" width="48" height="72"/><g class="cargo"><path d="M-18-35h36v16h-36z" fill="#e0b578" stroke="#735032" stroke-width="3"/><path d="M-11-29h7v5h-7zm14 0h7v5H3z" fill="#72964d"/></g></g><path d="M-16 9h32v16h-32z" fill="${color}" stroke="#4b382b" stroke-width="3"/><text class="chef-label" y="21" text-anchor="middle">${id}</text></g>`;}
export function kitchenSVG(){return `<canvas id="world-canvas" class="world-canvas" width="384" height="256" aria-hidden="true"></canvas><svg class="game-overlay" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1536 1024" preserveAspectRatio="xMidYMid slice" role="group" aria-labelledby="world-title world-desc"><title id="world-title">The little catering kitchen</title><desc id="world-desc">A low-resolution pixel kitchen. Three cooks follow recorded prep, cooking, packing and cleaning operations. Click a workstation to inspect its program.</desc>${Object.entries(stations).map(([id,s])=>station(id,s)).join('')}<g id="workers">${chef('W1','#4c7751')}${chef('W2','#68829a')}${chef('W3','#b76843')}</g></svg>`;}
function loadImage(src){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error(`Could not load game art: ${src}`));im.src=src;});}
export async function prepareScene(container){
  const portrait=matchMedia('(max-width:760px)');
  const fit=()=>container.querySelector('svg').setAttribute('preserveAspectRatio','xMidYMid slice');
  portrait.addEventListener('change',fit);fit();
  const background=await loadImage('./assets/kitchen-empty-v3.png');
  const canvas=container.querySelector('#world-canvas');worldContext=canvas.getContext('2d');worldContext.imageSmoothingEnabled=false;
  worldBackdrop=document.createElement('canvas');worldBackdrop.width=384;worldBackdrop.height=256;
  const ctx=worldBackdrop.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(background,0,0,384,256);
  worldContext.drawImage(worldBackdrop,0,0);
  chefFrames=createChefFrames();
  container.querySelectorAll('.chef').forEach(el=>renderWorker(el,{x:REST_SPOTS[el.id.slice(5)][0],y:REST_SPOTS[el.id.slice(5)][1],direction:'down',mode:'idle',frame:0,task:''}));
}
export function renderWorker(el,pose){
  const worker=el.id.slice(5),key=`${worker}/${pose.direction}/${pose.mode}/${pose.frame}/${pose.task}`;
  if(chefFrames&&el.dataset.sprite!==key){
    el.querySelector('.chef-sprite').setAttribute('href',chefFrames.get(key));
    el.dataset.sprite=key;
  }
  el.dataset.direction=pose.direction;el.dataset.motion=pose.mode;el.dataset.frame=pose.frame;
  el.classList.toggle('walking',pose.mode==='walk');el.classList.toggle('working',pose.mode==='work');
  el.setAttribute('transform',`translate(${Math.round(pose.x/4)*4} ${Math.round(pose.y/4)*4})`);
}

export function renderKitchen(c,time){
  if(!worldContext)return;
  worldContext.drawImage(worldBackdrop,0,0);
  return drawKitchenProps(worldContext,c,time);
}
