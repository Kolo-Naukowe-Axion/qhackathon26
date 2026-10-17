// Capture the actual loopback studio. No solver training, service or QPU calls.
import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile,cp} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const args=process.argv.slice(2),value=(name,fallback)=>{const i=args.indexOf(name);return i<0?fallback:args[i+1];};
const output=resolve(value('--output','output/playwright/catering-showcase-v1/captures'));
const base=value('--url','http://127.0.0.1:4193/');
const require=createRequire(import.meta.url);
let playwright;
try{playwright=require('playwright');}catch(error){if(!process.env.AXION_NODE_MODULES)throw new Error('Install playwright or set AXION_NODE_MODULES to the bundled Node package directory.');playwright=createRequire(resolve(process.env.AXION_NODE_MODULES,'package.json'))('playwright');}
await mkdir(output,{recursive:true});
const studioRoot=resolve(dirname(fileURLToPath(import.meta.url)),'catering-showcase');
const sourceHashes={};
for(const name of ['index.html','studio.js','playback.js','studio.css','story.json','evidence.json','live-parameters.json']){
 sourceHashes[name]=createHash('sha256').update(await readFile(resolve(studioRoot,name))).digest('hex');
}
const browser=await playwright.chromium.launch({headless:true});
let context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,reducedMotion:'reduce'});
let page=await context.newPage();const errors=[];
page.on('pageerror',error=>errors.push(error.message));
const url=new URL(base);url.searchParams.set('clean','1');url.searchParams.set('autolaunch','1');
await page.goto(url.toString());await page.waitForFunction(()=>window.axionStudio?.ready===true);
const story=JSON.parse(await readFile(resolve(studioRoot,'story.json'),'utf8'));let start=0;const chapters=story.map(c=>{const entry={...c,start};start+=c.duration;return entry;});const timings=chapters.map(c=>c.start+c.duration*.45);const captures=[];
for(const [index,t]of timings.entries()){
 await page.evaluate(t=>window.axionStudio.setTime(t),t);
 if(chapters[index].id==='run')await page.waitForFunction(()=>window.axionStudio.state.lastRun!==null);
 await page.waitForTimeout(130);
 const filename=`scene-${String(index+1).padStart(2,'0')}.png`;
 await page.screenshot({path:resolve(output,filename)});
 captures.push({time:t,filename,chapter:await page.evaluate(()=>window.axionStudio.state.chapter)});
}
if(errors.length)throw new Error(errors.join('\n'));
await page.evaluate(()=>{window.axionStudio.setMode('live');window.axionStudio.setTime(118);});
await page.screenshot({path:resolve(output,'live-mode.png')});
let videoPath=null;
if(args.includes('--record')){
 await context.close();
 context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,
   recordVideo:{dir:output,size:{width:1920,height:1080}},reducedMotion:'reduce'});
 page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
 await page.goto(url.toString());await page.waitForFunction(()=>window.axionStudio?.ready===true);
 await page.evaluate(()=>{window.axionStudio.setMode('video');window.axionStudio.setTime(0);window.axionStudio.play();});
 const started=Date.now();let nextLog=15;
 while(await page.evaluate(()=>window.axionStudio.state.playing)){
   await page.waitForTimeout(250);
   if((Date.now()-started)/1000>=nextLog){const state=await page.evaluate(()=>window.axionStudio.state);console.log(JSON.stringify({recording_seconds:Math.round((Date.now()-started)/1000),timeline_seconds:Math.round(state.time),chapter:state.chapter}));nextLog+=15;}
 }
 await page.waitForTimeout(100);
 videoPath=await page.video().path();
}
const state=await page.evaluate(()=>window.axionStudio.state);
if(errors.length)throw new Error(errors.join('\n'));
await context.close();await browser.close();
const receipt={status:'Local silent rough cut; not submitted or uploaded',width:1920,height:1080,captures,errors,live_route_seconds:165,video_route_seconds:260,
 studio_source_sha256:sourceHashes,fresh_sampling_receipt:state.lastRun,continuous_studio_capture:args.includes('--record'),training_runs:0,veloxq_calls:0,physical_qpu_calls:0,
 placeholders:['Human voiceover and final team rehearsal'],raw_video:videoPath};
if(state.lastRun?.status==='completed'){
 const retained=resolve(output,'fresh-sampling');
 await cp(dirname(state.lastRun.source_result),retained,{recursive:true});
 receipt.preserved_fresh_sampling_directory=retained;
}
if(videoPath){
 const target=resolve(output,'axion-kitchen-silent-rough-cut.mp4');
 // Trim the browser startup; the final continuous studio sequence lasts260s.
 const duration=260.1;
 await new Promise((resolvePromise,reject)=>{const ff=spawn('ffmpeg',['-y','-loglevel','error','-sseof',`-${duration}`,'-i',videoPath,'-t','260','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',target]);let stderr='';ff.stderr.on('data',d=>stderr+=d);ff.on('exit',code=>code===0?resolvePromise():reject(new Error(stderr)));});
 receipt.mp4=target;receipt.mp4_sha256=createHash('sha256').update(await readFile(target)).digest('hex');
}
await writeFile(resolve(output,'capture-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt));
