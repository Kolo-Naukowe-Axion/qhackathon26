import test from 'node:test';
import assert from 'node:assert/strict';
import {advancePlayback,rehearsalStatus} from '../scripts/catering-showcase/playback.js';

const chapters = [{start:0,end:8},{start:8,end:30},{start:30,end:42}];
test('live playback holds the current chapter before advancing', () => {
  const step = advancePlayback({time:29.95,delta:0.2,chapters,mode:'live'});
  assert.equal(step.pause,true);
  assert.ok(step.time < 30 && step.time > 29.9);
  assert.equal(chapters.find(c=>step.time<c.end),chapters[1]);
});
test('video playback crosses chapter boundaries continuously', () => {
  assert.deepEqual(advancePlayback({time:29.95,delta:0.2,chapters,mode:'video'}),
    {time:30.15,pause:false});
});
test('both routes stop exactly at the end', () => {
  for (const mode of ['live','video']) {
    assert.deepEqual(advancePlayback({time:41.9,delta:0.2,chapters,mode}),
      {time:42,pause:true});
  }
});

test('rehearsal clock flags wrap-up and the actual three-minute limit', () => {
  assert.deepEqual(rehearsalStatus(164.9),{elapsed:164,label:'2:44',level:'normal'});
  assert.equal(rehearsalStatus(165).level,'wrap');
  assert.equal(rehearsalStatus(179.9).level,'wrap');
  assert.deepEqual(rehearsalStatus(180),{elapsed:180,label:'3:00',level:'over'});
});

import {readFile} from 'node:fs/promises';
import {comparisonRows,serviceRows,formatTuple,identityDetails} from '../presentation/catering/benchmarks/benchmarks.js';
const bench=JSON.parse(await readFile(new URL('../presentation/catering/benchmarks/data.json',import.meta.url)));
test('benchmark filters keep evaluation budgets and method scopes explicit',()=>{
 const rows=comparisonRows(bench,'S2',256);
 assert.ok(rows.length>=5);
 assert.ok(rows.every(r=>r.case==='S2'&&(r.budget===256||r.budget===0)));
 assert.equal(rows.find(r=>r.config==='frozen').success_rate,1);
 assert.equal(bench.qaoa_runs.length,400);
 assert.equal(bench.veloxq.length,61);
 const scaled=serviceRows(bench,'noidle','completed');
 assert.equal(scaled.length,4);
 assert.ok(scaled.every(r=>r.valid===512&&r.shots===512));
 assert.equal(serviceRows(bench,'original','all').length,54);
 assert.equal(formatTuple({U:1,W:2,B:3,R:4}),'(1,2,3,4)');
});
test('presentation routes fit the slots and include full problem and scaling',async()=>{
 const story=JSON.parse(await readFile(new URL('../scripts/catering-showcase/story.json',import.meta.url)));
 assert.equal(story[0].id,'hook');
 assert.match(story[0].narration,/qualified workers/);
 assert.equal(story.reduce((a,c)=>a+c.duration,0),260);
 assert.equal(story.reduce((a,c)=>a+c.live_duration,0),165);
 for(const id of ['results','vqe','velox','scaling'])assert.ok(story.find(c=>c.id===id));
 assert.equal(bench.vqe.verification.checked_results.length,5);
 assert.deepEqual(bench.vqe.verification.checked_results.map(r=>r.case).sort(),['S0','S1','S2','S3','cell']);
 assert.ok(bench.vqe.verification.checked_results.every(r=>r.shots===1024));
});


test('quantum comparison separates held-out medians and unequal final shots',()=>{
 assert.deepEqual(bench.vqe.primary_heldout.map(r=>[r.case,r.seeds,r.hits,r.shots]),
   [['S2',10,10,[1024]],['S3',10,9,[1024]]]);
 assert.ok(bench.vqe.primary_heldout.every(r=>r.probability>0.12&&r.probability<0.13));
 assert.ok(bench.vqe.primary_heldout.every(r=>r.median_shift_equivalents>r.median_evaluations));
});


import {captureOptions,chapterShots} from '../scripts/catering-showcase/capture-plan.mjs';
test('capture defaults to no video and no sampler; explicit dry run cannot execute either',()=>{
 assert.deepEqual(captureOptions([]),{record:false,sample:false,dryRun:true});
 assert.deepEqual(captureOptions(['--dry-run']),{record:false,sample:false,dryRun:true});
 assert.deepEqual(captureOptions(['--sample']),{record:false,sample:true,dryRun:false});
 assert.deepEqual(captureOptions(['--record']),{record:true,sample:true,dryRun:false});
 assert.throws(()=>captureOptions(['--dry-run','--record']),/cannot sample or record/);
 assert.throws(()=>captureOptions(['--sample','--dry-run']),/cannot sample or record/);
});
test('recording shots derive durations and include operational outcomes and real code',async()=>{
 const story=JSON.parse(await readFile(new URL('../scripts/catering-showcase/story.json',import.meta.url)));
 const shots=chapterShots(story);
 assert.equal(shots.length,12);assert.equal(shots.at(-1).end,260);
 assert.ok(shots.every(c=>c.shot&&c.editor_cue&&c.time>c.start&&c.time<c.end));
 assert.ok(shots.find(c=>c.id==='service').still_progress>.8);
 assert.ok(shots.find(c=>c.id==='encoding').still_progress>.55);
});


test('follow-up service rows expose distinct source sampling and packet identities',()=>{
 const rows=bench.veloxq.filter(r=>r.source_bundle_sha256);
 assert.equal(rows.length,7);
 assert.ok(rows.every(r=>r.source_bundle_sha256.length===64&&r.sampling_bundle_sha256.length===64));
 const detail=identityDetails(rows[0]);
 assert.match(detail,/Source bundle SHA-256/);assert.match(detail,/Sampling bundle SHA-256/);
 if(rows[0].packet_sha256)assert.match(detail,/Packet SHA-256/);
 assert.deepEqual(bench.velox_payoff.rows.map(r=>[r.complete_meals,r.discarded_portions,r.valid_shots]),
  [[10,30,17],[50,60,512]]);
});


test('speaker scripts fit each chapter and separate result cues from spoken text',async()=>{
 const story=JSON.parse(await readFile(new URL('../scripts/catering-showcase/story.json',import.meta.url)));
 const words=s=>s.trim().split(/\s+/).length;
 for(const chapter of story){
  assert.ok(words(chapter.narration)*60/chapter.duration<=170,chapter.id+' video is rushed');
  if(chapter.live_duration)assert.ok(words(chapter.live_narration)*60/chapter.live_duration<=170,chapter.id+' live is rushed');
 }
 const run=story.find(c=>c.id==='run');
 assert.doesNotMatch(run.live_narration,/Read the actual|Click|expected20/);
 assert.match(run.live_result_cue,/only if/);
 assert.match(run.live_action,/Only after completion/);
 const close=story.find(c=>c.id==='close');
 assert.equal(close.log_summary.length,3);assert.match(close.narration,/Our log records/);
 assert.match(story.find(c=>c.id==='encoding').narration,/product expands.*coefficient span plus one/is);
});
