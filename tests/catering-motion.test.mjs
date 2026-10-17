import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { buildWorkerTrack, workerPoseAt, corridorRoute } from '../presentation/catering/worker-motion.js';
import {activateRun} from '../presentation/catering/model.js';
const data=JSON.parse(await readFile(new URL('../presentation/catering/replay-data.json',import.meta.url)));
const cases=data.cases.flatMap(c=>c.runs.map(r=>activateRun(c,r.key)));
const close=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y)<1e-6;
test('all sixteen method views have continuous worker paths, including back-to-back handovers',()=>{
  for(const c of cases)for(const worker of ['W1','W2','W3']){
    const track=buildWorkerTrack(c,worker);
    assert.equal(track[0].start,0);assert.equal(track.at(-1).end,c.instance.horizon_minutes);
    for(let i=1;i<track.length;i++){
      assert.equal(track[i].start,track[i-1].end);
      assert.ok(close(workerPoseAt(track,track[i].start-1e-9),workerPoseAt(track,track[i].start)),`${c.id}/${worker} jumps at ${track[i].start}`);
    }
    const end=workerPoseAt(track,c.instance.horizon_minutes);
    assert.deepEqual([end.x,end.y],track.at(-1).to); // A pack operation can end exactly at the horizon.
  }
});
test('visual walking keeps feet outside the two kitchen islands and uses cardinal directions',()=>{
  const islands=[[292,472,648,662],[932,472,1248,662]];
  for(const c of cases)for(const worker of ['W1','W2','W3']){
    const track=buildWorkerTrack(c,worker);
    for(let t=0;t<c.instance.horizon_minutes;t+=.05){
      const pose=workerPoseAt(track,t);
      for(const [x1,y1,x2,y2] of islands)assert.ok(!(pose.x>x1&&pose.x<x2&&pose.y>y1&&pose.y<y2),`${c.id}/${worker} enters a counter at ${t}`);
      assert.ok(['up','down','left','right'].includes(pose.direction));
    }
  }
  assert.deepEqual(corridorRoute([662,458],[1042,458]),[[662,458],[1042,458]]);
});
test('seeking reconstructs the same mid-walk pose and step frame without wall-clock state',()=>{
  const track=buildWorkerTrack(cases[1],'W1'),walk=track.find(s=>s.mode==='walk');
  const t=(walk.start+walk.end)/2,mid=workerPoseAt(track,t);
  assert.equal(mid.mode,'walk');assert.notDeepEqual([mid.x,mid.y],walk.to);
  workerPoseAt(track,90);workerPoseAt(track,0);
  assert.deepEqual(workerPoseAt(track,t),mid);
  assert.deepEqual(workerPoseAt(track,t),mid); // Pausing cannot teleport the cook.
  const frames=new Set(Array.from({length:32},(_,i)=>(i+.5)/32).map(f=>workerPoseAt(track,walk.start+(walk.end-walk.start)*f).frame));
  assert.ok(frames.size>1);
});
test('separate aisle lanes keep the three cooks from sharing foot space',()=>{
  for(const c of cases){
    const tracks=['W1','W2','W3'].map(w=>buildWorkerTrack(c,w));
    for(let t=0;t<c.instance.horizon_minutes;t+=.05){
      const p=tracks.map(tr=>workerPoseAt(tr,t));
      for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)assert.ok(Math.abs(p[i].x-p[j].x)>=38||Math.abs(p[i].y-p[j].y)>=30,`${c.id}: cooks ${i+1}/${j+1} collide at ${t}`);
    }
  }
});
test('mandatory recovery clean gives the cleaning worker a visible work segment',()=>{
  const c=cases.find(c=>c.id==='S2'),track=buildWorkerTrack(c,'W2');
  assert.equal(workerPoseAt(track,75).mode,'work');
  assert.equal(workerPoseAt(track,75).task,'clean');
});
