// Generate both speaker scripts from the chapter source; --check detects drift.
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const story=JSON.parse(await readFile(new URL('./story.json',import.meta.url),'utf8'));
const stamp=seconds=>`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
const words=text=>text.trim().split(/\s+/).length;
const videoSeconds=story.reduce((sum,c)=>sum+c.duration,0);
const live=story.filter(c=>c.live_duration);
const liveSeconds=live.reduce((sum,c)=>sum+c.live_duration,0);
let cursor=0;
const voice=story.map(c=>{const start=cursor;cursor+=c.duration;return `## ${stamp(start)}–${stamp(cursor)} · ${c.title}\n\n> ${c.narration}\n`;}).join('\n');
cursor=0;
const rows=live.map(c=>{const start=cursor;cursor+=c.live_duration;return `| ${stamp(start)}–${stamp(cursor)} | ${c.live_action} | ${c.live_narration} |`;}).join('\n');
const files={
 'CATERING_VOICEOVER.md':`# Video narration — ${stamp(videoSeconds)}\n\nGenerated from [story.json](../scripts/catering-showcase/story.json). Edit that\nsource, then run \`npm run docs:write\`. This is a human voiceover draft; the\nQAOA and VeloxQ paragraphs use integrated checked results; VQE separates\nreported campaign medians from checked exported schedules.\n\n${voice}\n## Recording notes\n\n${story.reduce((sum,c)=>sum+words(c.narration),0)} spoken words. Leave pauses for the code, equation and actual launch.\nThe current local MP4 is silent. Its pictures remain useful, but record the\nupdated narration for this result set. Earlier cuts have obsolete result slides.\n\nRecord one paragraph at a time in a quiet room. Align and retime the visuals,\nadd final subtitles, and check the export end to end. Keep the submitted video\nbelow five minutes. The screen recording and live slot are separate deliverables.\n`,
 'CATERING_LIVE.md':`# Live presentation — ${stamp(liveSeconds)} route\n\nGenerated from [story.json](../scripts/catering-showcase/story.json). Edit that\nsource, then run \`npm run docs:write\`. The slot is at most three minutes plus\nabout two minutes Q&A. This ${stamp(liveSeconds)} route leaves 15 seconds of margin; chapter\nholds do not pause the jury's clock.\n\n## Setup and controls\n\nRun \`.venv-stage2/bin/python scripts/serve-catering-showcase.py --port 4193\`.\nOpen [the live studio](http://127.0.0.1:4193/?mode=live). Use one speaker and\none operator. Share only the audience window; keep [Q&A notes](CATERING_QA.md)\noutside the share.\n\n- Right/Left Arrow: next/previous chapter.\n- Space: play/pause animation; live chapters hold at their end.\n- P: hide or restore operator controls and notes. F: full screen.\n- R: start/reset the rehearsal timer at the first spoken word. Animation holds do not\n  pause it. Target 2:45; stop before 3:00.\n\n## Read-aloud script and operator cues\n\n| Target time | Operator | Speaker |\n|---|---|---|\n${rows}\n\n${live.reduce((sum,c)=>sum+words(c.live_narration),0)} spoken words. The results use the integrated QAOA campaign and checked no-idle VeloxQ study. Rehearse three times\nunder 2:50 with the actual speaker, operator and final result set.\n\n## What the launch does\n\nThe button verifies frozen input hashes, reuses the frozen p=3/cell/budget256/seed-2026 angles and\nsamples 4096 shots with fixed sampling seed 17102026. It independently checks\nevery distinct returned bitstring. Local checks returned (U,W,B,R)=(0,0,2,2),\n20 complete meals, zero waste and 2173 valid shots. This is repeat execution\nof one fixed setup, not another independent training trial. It uses no paid\nservice, training or physical QPU. The kitchen replay retains its own label.\n\nTerminal fallback, with a fresh directory:\n\n\`\`\`sh\n.venv-stage2/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN\n\`\`\`\n\nIf the launch fails, say: “The fresh launch hasn't completed; we'll use the\nretained checked schedule.” Continue with the saved kitchen replay. If the\nstudio fails, open the [standalone viewer](http://127.0.0.1:4192/catering/)\nwith its separate static server running. Keep the local MP4 and screenshots\non the presenting laptop. Do not wait for a remote queue during the slot.\n`
};
let stale=false;
for(const [name,content]of Object.entries(files)){
 const url=new URL('../../docs/'+name,import.meta.url);
 if(process.argv.includes('--check')){
  const actual=await readFile(url,'utf8').catch(()=>null);
  if(actual!==content){console.error(`Outdated: ${fileURLToPath(url)}; run npm run docs:write`);stale=true;}
 }else await writeFile(url,content);
}
if(stale)process.exitCode=1;
else console.log(process.argv.includes('--check')?'Speaker scripts match story.json.':'Speaker scripts regenerated.');
