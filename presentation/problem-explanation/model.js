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

// Rebuild A's actual one-hot coefficients from durations and interval conflicts.
// stage 1 = exactly once, 2 = add capacity, 3 = add precedence.
export function teachingMatrix(stage = 3, symmetric = false) {
  const starts = jobs.slice(0, 2).flatMap(job => job.durations.slice(0, 2).flatMap((duration, order) => {
    const earliest = order ? job.durations[0] : 0;
    const latest = 4 - job.durations.slice(order, 2).reduce((a, b) => a + b, 0);
    return Array.from({ length: latest - earliest + 1 }, (_, t) => ({ job: job.id, machine: machines[order], order, start: earliest + t, duration }));
  }));
  const matrix = starts.map(() => starts.map(() => 0));
  const reasons = starts.map(() => starts.map(() => []));
  function add(i, j, value, kind, text) {
    matrix[i][j] += value;
    reasons[i][j].push({ value, kind, text });
  }
  if (stage >= 1) starts.forEach((a, i) => {
    add(i, i, -1, 'once', `The exactly-one square for ${a.job}/${a.machine} contributes −x${i}. Since x${i}² = x${i}, its linear coefficient goes on the diagonal.`);
    starts.slice(i + 1).forEach((b, relative) => {
      const j = i + relative + 1;
      if (a.job === b.job && a.machine === b.machine) add(i, j, 2, 'once', `x${i} and x${j} are two starts of ${a.job}/${a.machine}. Expanding (x${i} + x${j} − 1)² contributes +2x${i}x${j}.`);
      else {
        if (stage >= 2 && a.machine === b.machine && a.start < b.start + b.duration && b.start < a.start + a.duration) add(i, j, 1, 'machine', `${a.job}/${a.machine} [${a.start}, ${a.start + a.duration}) overlaps ${b.job}/${b.machine} [${b.start}, ${b.start + b.duration}). Selecting both contributes +x${i}x${j}.`);
        if (stage >= 3 && a.job === b.job && a.order + 1 === b.order && a.start + a.duration > b.start) add(i, j, 1, 'precedence', `${a.job}'s turning ends at ${a.start + a.duration}, after its milling would start at ${b.start}. Selecting both contributes +x${i}x${j}.`);
      }
    });
  });
  if (symmetric) {
    for (let i = 0; i < starts.length; i++) for (let j = i + 1; j < starts.length; j++) {
      matrix[i][j] /= 2; matrix[j][i] = matrix[i][j];
      reasons[j][i] = reasons[i][j];
    }
  }
  return { starts, matrix, reasons, offset: stage >= 1 ? 4 : 0 };
}

export function matrixEnergy(matrix, bits, offset = 0) {
  return offset + matrix.reduce((total, row, i) => total + row.reduce((sum, q, j) => sum + q * bits[i] * bits[j], 0), 0);
}
