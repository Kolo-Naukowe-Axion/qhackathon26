import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fetchLinkedTrace} from '../presentation/stage2/trace-loader.js';
import {normalizeTrace} from '../presentation/stage2/model.js';
import {FINAL_REPLAYS,DEFAULT_REPLAY,replayPreset} from '../presentation/stage2/replay-presets.js';

test('default and stress presets load the frozen selected final methods and retain their scope',async()=>{
 const records=JSON.parse(readFileSync(new URL('../presentation/stage2/traces/final-first-replay-index.json',import.meta.url)));
 assert.equal(DEFAULT_REPLAY,records.find(row=>row.method_id==='static-grid-12').viewer_path);
 for(const preset of FINAL_REPLAYS){
  const fetcher=async url=>new Response(readFileSync(new URL('../presentation'+new URL(url).pathname,import.meta.url)));
  const run=normalizeTrace(await fetchLinkedTrace(preset.path,'https://factory.test/stage2/',fetcher));
  assert.equal(replayPreset(run)?.id,preset.id);
  assert.equal(run.metrics.shipped,preset.orders);
  assert.equal(run.horizon_ticks,preset.hours*60);
  assert.equal(run.provenance.viewer_replay.selection.seed,10004);
  assert.equal(run.provenance.viewer_replay.selection.method_id,preset.method);
  assert.equal(run.provenance.viewer_replay.predeclared_first_tape,true);
  assert.equal(run.provenance.viewer_replay.posthoc_audit_only,false);
  assert.equal(run.validation.valid,true);
 }
 assert.equal(replayPreset({provenance:{kind:'measured'}}),null);
});
