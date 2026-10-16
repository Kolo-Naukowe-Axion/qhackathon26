// Hand-transcribed illustration; no solver has produced these schedules.
export const slideReplay = {
  schema: 'axion-replay.v1',
  title: 'Three parts through three machines',
  unit: 'hours',
  provenance: { kind: 'illustration', method: 'Manual transcription', label: 'Organizer slide', description: 'Opening presentation, 3×3 example. Reported makespan: 8 h.', source: 'Quantum_Hackathon_2026_Opening.pdf, p.5', jobId: null },
  machines: [{ id: 'T', name: 'Turning' }, { id: 'F', name: 'Milling' }, { id: 'S', name: 'Welding' }],
  jobs: [
    { id: 'Z1', color: '#3d667b', operations: [{ machine: 'T', duration: 2 }, { machine: 'F', duration: 1 }, { machine: 'S', duration: 2 }] },
    { id: 'Z2', color: '#946b35', operations: [{ machine: 'T', duration: 1 }, { machine: 'F', duration: 2 }, { machine: 'S', duration: 1 }] },
    { id: 'Z3', color: '#596d45', operations: [{ machine: 'T', duration: 2 }, { machine: 'F', duration: 2 }, { machine: 'S', duration: 1 }] }
  ],
  schedule: [
    { job: 'Z2', machine: 'T', start: 0, end: 1 }, { job: 'Z1', machine: 'T', start: 1, end: 3 }, { job: 'Z3', machine: 'T', start: 3, end: 5 },
    { job: 'Z2', machine: 'F', start: 1, end: 3 }, { job: 'Z1', machine: 'F', start: 3, end: 4 }, { job: 'Z3', machine: 'F', start: 5, end: 7 },
    { job: 'Z2', machine: 'S', start: 3, end: 4 }, { job: 'Z1', machine: 'S', start: 4, end: 6 }, { job: 'Z3', machine: 'S', start: 7, end: 8 }
  ]
};

export const smallReplay = {
  schema: 'axion-replay.v1',
  title: 'Instance A — document illustration',
  unit: 'hours',
  provenance: { kind: 'illustration', method: 'Manual transcription', label: 'Challenge document', description: 'Challenge §14, 2×2 example. Reported makespan: 4 h.', source: 'Quantum_Hackathon_2026_ERP_Challenge.pdf §14', jobId: null },
  machines: slideReplay.machines.slice(0, 2),
  jobs: slideReplay.jobs.slice(0, 2).map(j => ({ ...j, operations: j.operations.slice(0, 2) })),
  schedule: [{ job: 'Z2', machine: 'T', start: 0, end: 1 }, { job: 'Z2', machine: 'F', start: 1, end: 3 }, { job: 'Z1', machine: 'T', start: 1, end: 3 }, { job: 'Z1', machine: 'F', start: 3, end: 4 }]
};

export const alternativeReplay = {
  ...structuredClone(slideReplay),
  provenance: { kind: 'illustration', method: 'Manual schedule', label: 'Alternative', description: 'Sequence Z1 → Z3 → Z2 on every machine.', source: 'Local demonstration fixture', jobId: null },
  schedule: [
    { job: 'Z1', machine: 'T', start: 0, end: 2 }, { job: 'Z3', machine: 'T', start: 2, end: 4 }, { job: 'Z2', machine: 'T', start: 4, end: 5 },
    { job: 'Z1', machine: 'F', start: 2, end: 3 }, { job: 'Z3', machine: 'F', start: 4, end: 6 }, { job: 'Z2', machine: 'F', start: 6, end: 8 },
    { job: 'Z1', machine: 'S', start: 3, end: 5 }, { job: 'Z3', machine: 'S', start: 6, end: 7 }, { job: 'Z2', machine: 'S', start: 8, end: 9 }
  ]
};
