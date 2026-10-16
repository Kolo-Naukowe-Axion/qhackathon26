import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { jobs, scheduleForOrder, permutations, decodeBits, compactEnergy } from '../presentation/problem-explanation/model.js';
import { validateSchedule } from '../presentation/model.js';
import { smallReplay, slideReplay } from '../presentation/data.js';
import { selectedEvidence } from '../presentation/problem-explanation/evidence.js';

test('guide solver summaries match the currently selected verified evidence', async () => {
  const selection = JSON.parse(await readFile(new URL('../output/stage1-selected.json', import.meta.url)));
  for (const [instance, summary] of Object.entries(selectedEvidence)) {
    const source = selection.selected_runs[instance];
    assert.equal(summary.source, source);
    const run = JSON.parse(await readFile(new URL(`../${source}/run.json`, import.meta.url)));
    for (const [key, value] of Object.entries(summary)) {
      if (key === 'source') continue;
      if (key === 'metadata') {
        for (const [setting, expected] of Object.entries(value)) assert.deepEqual(run.metadata[setting], expected);
      } else assert.deepEqual(run[key], value);
    }
  }
});

test('manual inputs match the official datasets', async () => {
  const official = JSON.parse(await readFile(new URL('../instances/instance_3x3.json', import.meta.url)));
  assert.deepEqual(jobs.map(j => ({ id: j.id, durations: j.durations })), official.jobs.map(j => ({ id: j.id, durations: j.operations.map(o => o.duration) })));
});
test('every manual job order produces a feasible schedule with the expected makespan', () => {
  for (const [template, m, expected] of [[smallReplay, 2, [5, 4]], [slideReplay, 3, [8, 9, 8, 8, 8, 9]]]) {
    permutations(template.jobs.map(j => j.id)).forEach((order, i) => {
      const result = scheduleForOrder(order, m);
      assert.equal(result.makespan, expected[i]);
      assert.equal(validateSchedule({ ...template, schedule: result.schedule }).feasible, true);
    });
  }
});
test('interactive four-bit energy has zero energy exactly for independently valid schedules', () => {
  let feasibleCount = 0;
  for (let n = 0; n < 16; n++) {
    const bits = Array.from({ length: 4 }, (_, i) => (n >> i) & 1);
    const schedule = decodeBits(bits);
    const feasible = validateSchedule({ ...smallReplay, schedule }).feasible;
    assert.equal(compactEnergy(bits) === 0, feasible, `bit assignment ${bits}`);
    if (feasible) feasibleCount++;
  }
  assert.equal(feasibleCount, 1);
});
