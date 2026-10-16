import test from 'node:test';
import assert from 'node:assert/strict';
import { parseReplay, validateSchedule, jobState, makespan, officialScheduleToReplay } from '../presentation/model.js';
import { slideReplay, alternativeReplay, smallReplay } from '../presentation/data.js';
import { readFile } from 'node:fs/promises';

test('published illustrations are feasible and retain their actual source', () => {
  for (const [fixture, expected] of [[slideReplay, 8], [alternativeReplay, 9], [smallReplay, 4]]) {
    const parsed = parseReplay(fixture);
    assert.equal(validateSchedule(parsed).feasible, true);
    assert.equal(makespan(parsed), expected);
    assert.equal(parsed.provenance.kind, 'illustration');
    assert.equal(parsed.provenance.jobId, null);
  }
});
test('job state follows half-open operation intervals and completion boundary', () => {
  assert.equal(jobState(slideReplay, 'Z2', .5).operation.machine, 'T');
  assert.equal(jobState(slideReplay, 'Z2', 1).operation.machine, 'F');
  assert.equal(jobState(slideReplay, 'Z3', 6.5).operation.machine, 'F');
  assert.equal(jobState(slideReplay, 'Z3', 8).kind, 'complete');
  assert.equal(jobState(slideReplay, 'Z1', .5).kind, 'waiting');
});
test('missing and duplicate operations fail coverage', () => {
  for (const mutate of [x => x.schedule.pop(), x => x.schedule.push({ ...x.schedule[0] })]) {
    const x = structuredClone(slideReplay); mutate(x);
    const result = validateSchedule(parseReplay(x));
    assert.equal(result.feasible, false);
    assert.ok(result.checks.find(c => c.id === 'coverage').issues.length);
  }
});
test('a machine overlap is detected even with correct processing durations', () => {
  const x = structuredClone(slideReplay);
  const op = x.schedule.find(o => o.job === 'Z1' && o.machine === 'T');
  op.start = 0; op.end = 2;
  assert.ok(validateSchedule(parseReplay(x)).checks.find(c => c.id === 'capacity').issues.length);
});
test('precedence and duration are checked independently', () => {
  const x = structuredClone(slideReplay);
  const op = x.schedule.find(o => o.job === 'Z3' && o.machine === 'S');
  op.start = 6; op.end = 6.5;
  const result = validateSchedule(parseReplay(x));
  assert.ok(result.checks.find(c => c.id === 'duration').issues.length);
  assert.ok(result.checks.find(c => c.id === 'precedence').issues.length);
});
test('import rejects unknown references, NaN times, bad colors and absent provenance', () => {
  for (const mutate of [x => x.schedule[0].job = 'unknown', x => x.schedule[0].start = NaN, x => x.jobs[0].color = 'url(javascript:bad)', x => delete x.provenance, x => x.schedule[0].end = -1]) {
    const x = structuredClone(slideReplay); mutate(x);
    assert.throws(() => parseReplay(x));
  }
});
test('viewer does not silently complete an incomplete job', () => {
  const x = structuredClone(slideReplay);
  x.schedule = x.schedule.filter(o => !(o.job === 'Z3' && o.machine === 'S'));
  assert.equal(jobState(x, 'Z3', 99).kind, 'unscheduled');
});
test('illustrative processing data exactly matches both official instance files', async () => {
  for (const [name, replay] of [['2x2', smallReplay], ['3x3', slideReplay]]) {
    const instance = JSON.parse(await readFile(new URL(`../instances/instance_${name}.json`, import.meta.url)));
    assert.deepEqual(replay.jobs.map(({ id, operations }) => ({ id, operations })), instance.jobs);
  }
});
test('official schedule import validates declared makespan without fabricating provenance', () => {
  const output = { instance: 'instance_2x2', method: 'File supplied method', makespan: 4, schedule: smallReplay.schedule };
  const replay = officialScheduleToReplay(output, smallReplay);
  assert.equal(validateSchedule(replay).feasible, true);
  assert.equal(replay.provenance.kind, 'imported');
  assert.equal(replay.provenance.jobId, null);
  output.makespan = 3;
  const wrong = validateSchedule(officialScheduleToReplay(output, smallReplay));
  assert.equal(wrong.feasible, false);
  assert.equal(wrong.checks.at(-1).id, 'makespan');
});
test('official baseline import rejects fractional times and wrong instance templates', () => {
  const output = { instance: 'instance_2x2', method: 'Example', makespan: 4, schedule: structuredClone(smallReplay.schedule) };
  assert.throws(() => officialScheduleToReplay(output, slideReplay));
  output.schedule[0].start = .5;
  assert.throws(() => officialScheduleToReplay(output, smallReplay));
});
