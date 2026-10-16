// Small deterministic teaching models. These are illustrations, not solver runs.
export const jobs = [
  { id: 'Z1', color: '#3d667b', durations: [2, 1, 2] },
  { id: 'Z2', color: '#946b35', durations: [1, 2, 1] },
  { id: 'Z3', color: '#596d45', durations: [2, 2, 1] }
];
export const machines = ['T', 'F', 'S'];
export function scheduleForOrder(order, machineCount) {
  const ends = Array(machineCount).fill(0), schedule = [];
  for (const id of order) {
    const job = jobs.find(j => j.id === id);
    let previous = 0;
    for (let m = 0; m < machineCount; m++) {
      const start = Math.max(ends[m], previous), end = start + job.durations[m];
      schedule.push({ job: id, machine: machines[m], start, end });
      ends[m] = previous = end;
    }
  }
  return { schedule, makespan: ends.at(-1) };
}
export function permutations(items) {
  return items.length ? items.flatMap((v, i) => permutations(items.filter((_, k) => k !== i)).map(rest => [v, ...rest])) : [[]];
}
export const factorial = n => Array.from({ length: n }, (_, i) => BigInt(i + 1)).reduce((a, b) => a * b, 1n);
export function decodeBits([a, b, c, d]) {
  return [
    { job: 'Z1', machine: 'T', start: a, end: a + 2 },
    { job: 'Z1', machine: 'F', start: 2 + b, end: 3 + b },
    { job: 'Z2', machine: 'T', start: c, end: c + 1 },
    { job: 'Z2', machine: 'F', start: 1 + d, end: 3 + d }
  ];
}
export function conflicts(schedule) {
  const capacity = [], precedence = [];
  schedule.forEach((a, i) => schedule.slice(i + 1).forEach(b => {
    if (a.machine === b.machine && a.start < b.end && b.start < a.end) capacity.push(`${a.machine}: ${a.job} and ${b.job} overlap`);
  }));
  for (const id of ['Z1', 'Z2']) {
    const t = schedule.find(o => o.job === id && o.machine === 'T');
    const f = schedule.find(o => o.job === id && o.machine === 'F');
    if (t.end > f.start) precedence.push(`${id}: milling starts before turning finishes`);
  }
  return { capacity, precedence, energy: capacity.length + precedence.length };
}
export function compactEnergy([a, b, c, d]) { return 2 - b + c - a * b + a * c + b * d - c * d; }
