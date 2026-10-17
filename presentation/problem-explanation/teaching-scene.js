import {createScene} from '../scene.js';
import {slideReplay} from '../data.js';
export function mountTeachingScene(root,onPart){
 let time=0,selected=null,playing=!matchMedia('(prefers-reduced-motion: reduce)').matches,previous=0,frame=0;
 const end=Math.max(...slideReplay.schedule.map(op=>op.end));
 const canvas=root.querySelector('#manual-scene'),button=root.querySelector('#manual-scene-play'),scrub=root.querySelector('#manual-scene-time'),clock=root.querySelector('#manual-scene-clock');
 const scene=createScene(canvas,slideReplay,id=>{selected=id;onPart(id);draw();});
 function draw(){scene.update(time,selected,playing);scrub.value=time;clock.textContent=`${time.toFixed(1)} / ${end} h`;button.textContent=playing?'Ⅱ Pause':time>=end?'↻ Replay':'▶ Play';button.setAttribute('aria-label',playing?'Pause teaching animation':'Play teaching animation');}
 function animate(now){if(playing&&!document.hidden){if(previous)time=Math.min(end,time+Math.min(.1,(now-previous)/1000)*.65);if(time>=end)playing=false;draw();}previous=now;frame=requestAnimationFrame(animate);}
 button.addEventListener('click',()=>{if(time>=end)time=0;playing=!playing;previous=0;draw();});
 scrub.addEventListener('input',()=>{playing=false;time=Number(scrub.value);draw();});
 scrub.max=end;draw();frame=requestAnimationFrame(animate);
 return ()=>cancelAnimationFrame(frame);
}
