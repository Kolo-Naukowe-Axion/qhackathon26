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
