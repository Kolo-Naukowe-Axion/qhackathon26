// Public summary of the selected, verified local runs. Refresh when selection changes.
export const selectedEvidence = {
  "instance_2x2": {
    "method": "QAOA p=3, local-x mixer (Qiskit Aer statevector simulator)",
    "timestamp": "2026-10-16T18:17:23.495231+00:00",
    "encoding": "domain-wall",
    "variables": 4,
    "total_samples": 4096,
    "feasible_samples": 4096,
    "feasible_rate": 1.0,
    "source": "output/stage1-local-ready/qaoa-2x2",
    "metadata": {
      "mixer": "local-x",
      "trainable_parameters": 15,
      "layers": 3,
      "shots": 4096,
      "seed": 2026,
      "restarts": 16,
      "maxiter": 500,
      "elapsed_wall_seconds": 6.578799542039633
    }
  },
  "instance_3x3": {
    "method": "Classical QUBO simulated annealing (dwave-samplers)",
    "timestamp": "2026-10-16T18:17:25.863137+00:00",
    "encoding": "onehot",
    "variables": 39,
    "total_samples": 512,
    "feasible_samples": 511,
    "feasible_rate": 0.998046875,
    "source": "output/stage1-local-ready/anneal-3x3",
    "metadata": {
      "reads": 512,
      "sweeps": 32000,
      "seed": 2026,
      "elapsed_wall_seconds": 2.121553333941847,
      "beta_schedule_type": "linear"
    }
  }
};
