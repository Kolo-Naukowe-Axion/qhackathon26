import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseReplay, officialScheduleToReplay, validateSchedule } from '../presentation/model.js';
import { smallReplay, slideReplay } from '../presentation/data.js';

const selection = JSON.parse(await readFile(new URL('../output/stage1-selected.json', import.meta.url), 'utf8'));

for (const [size, template, optimum] of [
  ['2x2', smallReplay, 4],
  ['3x3', slideReplay, 8]
]) {
  test(`actual ${size} solver artifacts pass the independent browser checker`, async () => {
    const directory = selection.selected_runs[`instance_${size}`];
    const official = JSON.parse(await readFile(new URL(`../schedule_${size}.json`, import.meta.url), 'utf8'));
    const replay = JSON.parse(await readFile(new URL(`../${directory}/replay.json`, import.meta.url), 'utf8'));
    const report = JSON.parse(await readFile(new URL(`../${directory}/run.json`, import.meta.url), 'utf8'));
    assert.equal(validateSchedule(officialScheduleToReplay(official, template)).feasible, true);
    const checked = validateSchedule(parseReplay(replay));
    assert.equal(checked.feasible, true);
    assert.equal(checked.makespan, optimum);
    assert.deepEqual(replay.schedule, official.schedule);
    assert.equal(replay.provenance.kind, 'solver');
    assert.equal(report.accepted, true);
    assert.equal(report.method, official.method);
    if (size === '2x2') assert.match(official.method, /QAOA/);
  });
}
