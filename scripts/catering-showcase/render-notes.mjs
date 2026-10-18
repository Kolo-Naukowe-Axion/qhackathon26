import {noteSlidesForChapter} from './speaker-notes.js';
// Generate speaker and recording sheets from one chapter source; --check detects drift.
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const story=JSON.parse(await readFile(new URL('./story.json',import.meta.url),'utf8'));
const stamp=seconds=>`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
const words=text=>text.trim().split(/\s+/).length;
const maxPace=(field,duration)=>Math.max(...story.filter(c=>c[duration]).map(c=>words(c[field])*60/c[duration]));
const videoSeconds=story.reduce((sum,c)=>sum+c.duration,0);
const live=story.filter(c=>c.live_duration);
const liveSeconds=live.reduce((sum,c)=>sum+c.live_duration,0);
let cursor=0;
const voice=story.map(c=>{const start=cursor;cursor+=c.duration;return `## ${stamp(start)}–${stamp(cursor)} · ${c.title}\n\n> ${c.narration}\n`;}).join('\n');
cursor=0;
const rows=live.map(c=>{const start=cursor;cursor+=c.live_duration;return `| ${stamp(start)}–${stamp(cursor)} | ${c.live_action} | ${c.live_narration} |`;}).join('\n');
cursor=0;
const shotRows=story.map(c=>{const start=cursor;cursor+=c.duration;return `| ${stamp(start)}–${stamp(cursor)} | ${c.shot} | ${c.editor_cue} |`;}).join('\n');
const slideNotes=live.flatMap(chapter=>noteSlidesForChapter(chapter,'live')).map(note=>`## ${note.label}\n\n> ${note.speech}\n`).join('\n');
const files={
 'CATERING_SLIDE_NOTES.md':`# Live speaker notes — by visible slide\n\nThese notes match the current visual slide, including the separate opening, Stage 1, code and proof views. They do not change on a clock within the same view. Keep this file on a phone or second device when sharing the demo; P hides the studio notes as well as its controls. Use the rehearsal timer to stay under three minutes.\n\n${slideNotes}\n`,
 'CATERING_RECORDING.md':`# Final video and recording notes — ${stamp(videoSeconds)}

[Watch the final video](https://qfactoria.com/video/) · [Narration](CATERING_VOICEOVER.md) · [Live route](CATERING_LIVE.md)

The completed local export is [axion-kitchen.mp4](../output/submission-male-v3/axion-kitchen.mp4):
3840×2160, ${stamp(videoSeconds)}, H.264 video with AAC narration, English selectable subtitles
and ${story.length} chapter markers. [manifest.json](../output/submission-male-v3/manifest.json)
records media hashes, source hashes and the export checks. Publication and organizer
submission are separate states; this document does not assert submission.

## What was captured

The video edits actual browser UI captures. The animated service section was
captured at five frames per second and encoded into a 30-fps output; model,
code and result frames are held for reading. It is not a continuous screen recording.
The QAOA chapter includes a real button launch, its RUNNING state and its CHECKED
receipt: 20 complete meals, zero waste and 2,173 valid shots from 4,096 samples
at 2026-10-18 12:15:30 UTC. Editorial holds do not measure process runtime.
The retained kitchen replay has a separate label. This capture made no training
runs, VeloxQ submissions or physical-QPU jobs.

Narration uses Kokoro's stock \`am_fenrir\` synthetic voice, with no voice cloning.
[voice-manifest.json](../output/submission-male-v3/voice-manifest.json) records
model/engine attribution, pronunciation text and chapter alignment;
[captions.srt](../output/submission-male-v3/captions.srt) retains the subtitles.

## Picture and edit plan

Generated from [story.json](../scripts/catering-showcase/story.json).

| Video time | Picture | Hold / edit cue |
|---|---|---|
${shotRows}

## Optional replacement capture

Start the [local studio](../scripts/catering-showcase/README.md) and run
\`.venv-catering/bin/python scripts/check-catering-demo.py\` before capturing.
Use \`http://127.0.0.1:4193/?export=2\` for the fixed 3840×2160 stage; operator
controls sit below it and must stay outside the final crop. Retain source hashes
and actual launch receipts with any replacement export.

The separate \`scripts/capture-catering-showcase.mjs --dry-run\` helper captures
stills without sampling or video; \`--record\` instead creates a silent continuous
route and performs two frozen-angle local samples (preview and recording).
That optional helper requires Chromium, Playwright and ffmpeg. It was not the
capture method used for this final edited video.

If narration or evidence changes, regenerate the affected audio and picture
from the same story, update subtitles and hashes, and review the resulting file
with sound. Keep the export below five minutes and verify the public watch link
after deployment.
`,
 'CATERING_VOICEOVER.md':`# Video narration — ${stamp(videoSeconds)}

[Watch the final video](https://qfactoria.com/video/) · [Local MP4](../output/submission-male-v3/axion-kitchen.mp4)

The completed narration uses Kokoro's stock \`am_fenrir\` synthetic voice;
no voice was cloned. [Voice manifest](../output/submission-male-v3/voice-manifest.json)
records the engine/model attribution, pronunciation adjustments and chapter timing.
English selectable subtitles are included in the MP4 and available as
[captions.srt](../output/submission-male-v3/captions.srt).

This text is generated from [story.json](../scripts/catering-showcase/story.json).
Edit that source, then run \`npm run docs:write\`. QAOA and VeloxQ use integrated
checked results; VQE separates reported campaign medians from checked exported schedules.

${voice}
## Editing notes

${story.reduce((sum,c)=>sum+words(c.narration),0)} source words; the fastest chapter is ${Math.ceil(maxPace('narration','duration'))} words/minute.
Narration is generated sentence by sentence and aligned to the chapter route.
The voice manifest records actual pronunciation text and time stretch. Preserve
pauses for the model, source code and real launch; do not claim a result absent
from the receipt. The final video uses edited actual UI captures, not an unedited
continuous recording.

The separate live presentation uses [its shorter script](CATERING_LIVE.md).
Organizer submission is not implied by this completed local video.
`,
 'CATERING_LIVE.md':`# Live presentation — ${stamp(liveSeconds)} route\n\nGenerated from [story.json](../scripts/catering-showcase/story.json). Edit that\nsource, then run \`npm run docs:write\`. The slot is at most three minutes plus\nabout two minutes Q&A. This ${stamp(liveSeconds)} route leaves 15 seconds of margin; chapter\nholds do not pause the jury's clock.\n\n## Setup and controls\n\n[Final narrated video](https://qfactoria.com/video/) · [Local MP4](../output/submission-male-v3/axion-kitchen.mp4). The video is a fallback and a separate deliverable.\n\nRun \`.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193\`.\nOpen [the live studio](http://127.0.0.1:4193/?mode=live). Use one speaker and\none operator. Share only the audience window; keep [Q&A notes](CATERING_QA.md)\noutside the share.\n\n- Right/Left Arrow: next/previous chapter.\n- Space: play/pause animation; at a live chapter hold, replay that chapter.\n- P: hide or restore operator controls and notes. F: full screen.\n- R: start/reset the rehearsal timer at the first spoken word. Animation holds do not\n  pause it. Target 2:45; stop before 3:00.\n\n## Read-aloud script and operator cues\n\n| Target time | Operator | Speaker |\n|---|---|---|\n${rows}\n\n${live.reduce((sum,c)=>sum+words(c.live_narration),0)} scripted words; the fastest chapter is ${Math.ceil(maxPace('live_narration','live_duration'))} words/minute. The results use the integrated QAOA campaign and checked VeloxQ replanning loop. Rehearse three times\nunder 2:50 with the actual speaker, operator and final result set.\n\n## Reading the live result\n\n${story.find(c=>c.id==='run').live_result_cue}\nRead the short success sentence within the launch chapter; it is conditional on the actual displayed receipt.\n\n## What the launch does\n\nThe button verifies frozen input hashes, reuses the frozen p=3/cell/budget256/seed-2026 angles and\nsamples 4096 shots with fixed sampling seed 17102026. It independently checks\nevery distinct returned bitstring. Local checks returned (U,W,B,R)=(0,0,2,2),\n20 complete meals, zero waste and 2173 valid shots. This is repeat execution\nof one fixed setup, not another independent training trial. It uses no paid\nservice, training or physical QPU. The kitchen replay retains its own label.\n\nTerminal fallback, with a fresh directory:\n\n\`\`\`sh\n.venv-catering/bin/python scripts/catering_live.py --output output/NEW-LIVE-RUN\n\`\`\`\n\nIf the launch fails, say: “The fresh launch hasn't completed; we'll use the\nretained checked schedule.” Continue with the saved kitchen replay. If the\nstudio fails, open the [standalone viewer](http://127.0.0.1:4192/catering/?case=CELL)\nwith its separate static server running. Keep the local MP4 and screenshots\non the presenting laptop. Do not wait for a remote queue during the slot.\n`
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
else console.log(process.argv.includes('--check')?'Speaker and recording sheets match story.json.':'Speaker and recording sheets regenerated.');
