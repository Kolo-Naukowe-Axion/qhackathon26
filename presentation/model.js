const EPS = 1e-8;
const fail = message => { throw new Error(message); };
const isText = x => typeof x === 'string' && x.length > 0 && x.length <= 4000;

// This viewer deliberately accepts a narrow, versioned display contract.
// Official submission JSON enters through the adapter below.
export function parseReplay(value) {
  if (!value || value.schema !== 'axion-replay.v1') fail('Expected an axion-replay.v1 file.');
  if (value.unit !== 'hours') fail('This viewer currently displays time in hours.');
  if (!Array.isArray(value.machines) || ![2, 3].includes(value.machines.length)) fail('This first factory scene supports two or three machines.');
  if (!Array.isArray(value.jobs) || !value.jobs.length || value.jobs.length > 12) fail('Supply between 1 and 12 jobs.');
  if (!Array.isArray(value.schedule) || value.schedule.length > 200) fail('Supply a schedule array with at most 200 operations.');
  for (const m of value.machines) if (!m || !isText(m.id) || !isText(m.name)) fail('Each machine needs an id and name.');
  const machines = new Set(value.machines.map(m => m.id));
  if (machines.size !== value.machines.length) fail('Machine ids must be unique.');
  const jobs = new Set();
  for (const j of value.jobs) {
    if (!j || !isText(j.id) || jobs.has(j.id)) fail('Job ids must be unique, nonempty strings.');
    jobs.add(j.id);
    if (!/^#[0-9a-f]{6}$/i.test(j.color)) fail('Job colors must use six-digit hex notation.');
    if (!Array.isArray(j.operations) || j.operations.length !== value.machines.length) fail('Each job must visit every displayed machine once.');
    if (j.operations.some((o, i) => !o || o.machine !== value.machines[i].id || !Number.isFinite(o.duration) || o.duration <= 0)) fail('Operations must follow the displayed machine route with positive durations.');
  }
  for (const op of value.schedule) {
    if (!op || !jobs.has(op.job) || !machines.has(op.machine)) fail('An operation refers to an unknown job or machine.');
    if (![op.start, op.end].every(Number.isFinite) || op.start < 0 || op.end <= op.start || op.end > 1e6) fail('Operation times must be finite, nonnegative, and end after start (maximum 1,000,000).');
  }
  if (!value.provenance || !['illustration', 'solver', 'imported'].includes(value.provenance.kind) || !isText(value.provenance.method) || !isText(value.provenance.label)) fail('Supply illustration/solver/imported provenance, a method, and a label.');
  if (value.declaredMakespan != null && (!Number.isFinite(value.declaredMakespan) || value.declaredMakespan < 0)) fail('Declared makespan must be a nonnegative number.');
  for (const field of ['description', 'source', 'jobId', 'backend', 'timestamp']) if (value.provenance[field] != null && !isText(value.provenance[field])) fail(`Provenance ${field} must be text.`);
  return structuredClone(value);
}

export function makespan(replay) { return Math.max(0, ...replay.schedule.map(o => o.end)); }

export function officialScheduleToReplay(output, template) {
  if (!output || !['instance_2x2', 'instance_3x3'].includes(output.instance)) fail('Unknown official baseline instance.');
  if (!isText(output.method) || !Number.isInteger(output.makespan)) fail('Official schedules require a method and integer makespan.');
  if (!Array.isArray(output.schedule) || output.schedule.some(o => !o || !Number.isInteger(o.start) || !Number.isInteger(o.end))) fail('Official baseline times must be integers in hours.');
  const expectedMachines = output.instance === 'instance_2x2' ? 2 : 3;
  if (template.machines.length !== expectedMachines) fail('Instance and display template do not match.');
  return parseReplay({
    ...structuredClone(template),
    declaredMakespan: output.makespan,
    schedule: output.schedule,
    provenance: { kind: 'imported', method: output.method, label: `Imported ${output.instance}`, source: 'Official-format schedule JSON', description: 'Schedule loaded in the organizer’s submission format. The method is declared by the file; execution evidence has not been authenticated.', jobId: null }
  });
}
export function operationsFor(replay, job) { return replay.schedule.filter(o => o.job === job).sort((a, b) => a.start - b.start); }
export function jobState(replay, job, time) {
  const ops = operationsFor(replay, job);
  const active = ops.find(o => o.start <= time && time < o.end);
  if (active) return { kind: 'processing', operation: active, progress: (time - active.start) / (active.end - active.start) };
  const expected = replay.jobs.find(j => j.id === job).operations.length;
  if (ops.length === expected && ops.every(o => o.end <= time)) return { kind: 'complete' };
  const next = ops.find(o => o.start > time);
  if (next) return { kind: 'waiting', next, after: ops.filter(o => o.end <= time).at(-1) };
  return { kind: 'unscheduled' };
}

export function validateSchedule(replay) {
  const checks = [
    { id: 'coverage', label: 'Every operation appears exactly once', detail: 'All required job–machine operations are present.', issues: [] },
    { id: 'duration', label: 'Processing durations match', detail: 'Each operation receives its specified processing time.', issues: [] },
    { id: 'capacity', label: 'One operation per machine', detail: 'No two operations overlap on the same machine.', issues: [] },
    { id: 'precedence', label: 'The machine route is respected', detail: 'Each operation finishes before its successor begins.', issues: [] }
  ];
  for (const j of replay.jobs) {
    for (const requirement of j.operations) {
      const ops = replay.schedule.filter(o => o.job === j.id && o.machine === requirement.machine);
      if (ops.length !== 1) checks[0].issues.push(`${j.id}/${requirement.machine}: expected once, found ${ops.length}.`);
      for (const op of ops) if (Math.abs(op.end - op.start - requirement.duration) > EPS) checks[1].issues.push(`${j.id}/${requirement.machine}: duration differs from ${requirement.duration}.`);
    }
    for (let i = 1; i < j.operations.length; i++) {
      const prev = replay.schedule.filter(o => o.job === j.id && o.machine === j.operations[i - 1].machine);
      const next = replay.schedule.filter(o => o.job === j.id && o.machine === j.operations[i].machine);
      for (const a of prev) for (const b of next) if (a.end > b.start + EPS) checks[3].issues.push(`${j.id}: ${b.machine} starts before ${a.machine} finishes.`);
    }
  }
  for (const m of replay.machines) {
    const ops = replay.schedule.filter(o => o.machine === m.id).sort((a, b) => a.start - b.start);
    for (let i = 0; i < ops.length; i++) for (let k = i + 1; k < ops.length; k++) {
      if (ops[k].start < ops[i].end - EPS) checks[2].issues.push(`${m.id}: ${ops[i].job} overlaps ${ops[k].job}.`);
    }
  }
  if (replay.declaredMakespan != null) checks.push({ id: 'makespan', label: 'Declared makespan matches completion', detail: 'The submitted makespan equals the final operation end.', issues: Math.abs(replay.declaredMakespan - makespan(replay)) > EPS ? [`Declared ${replay.declaredMakespan} h; actual ${makespan(replay)} h.`] : [] });
  return { feasible: checks.every(c => !c.issues.length), checks, makespan: makespan(replay), operationCount: replay.schedule.length };
}
