// Selected verified local runs; generated from output/stage1-selected.json and retained samples.
export const selectedEvidence = {
  "instance_2x2": {
    "method": "QAOA p=1, x mixer, pairwise-order QUBO (Qiskit Aer statevector simulator)",
    "timestamp": "2026-10-16T23:17:45.153699+00:00",
    "encoding": "pairwise-order",
    "variables": 1,
    "total_samples": 4096,
    "feasible_samples": 4096,
    "feasible_rate": 1.0,
    "source": "output/stage1-compact-ready/quantum-2x2",
    "metadata": {
      "mixer": "x",
      "trainable_parameters": 2,
      "layers": 1,
      "shots": 4096,
      "seed": 2026,
      "restarts": 1,
      "maxiter": 500,
      "elapsed_wall_seconds": 0.03224712493829429,
      "ideal_ground_probability": 0.9999999999999984,
      "circuit_operations": {
        "h": 1,
        "rz": 1,
        "rx": 1
      }
    },
    "optimal_samples": 4096
  },
  "instance_3x3": {
    "method": "QAOA p=2, local-x mixer, pairwise-order QUBO (Qiskit Aer statevector simulator)",
    "timestamp": "2026-10-16T23:17:46.536544+00:00",
    "encoding": "pairwise-order",
    "variables": 3,
    "total_samples": 4096,
    "feasible_samples": 4096,
    "feasible_rate": 1.0,
    "source": "output/stage1-compact-ready/quantum-3x3",
    "metadata": {
      "mixer": "local-x",
      "trainable_parameters": 8,
      "layers": 2,
      "shots": 4096,
      "seed": 2026,
      "restarts": 8,
      "maxiter": 500,
      "elapsed_wall_seconds": 1.3105563749559224,
      "ideal_ground_probability": 0.9999999999999547,
      "circuit_operations": {
        "rz": 6,
        "rzz": 6,
        "rx": 6,
        "h": 3
      }
    },
    "optimal_samples": 4096
  }
};
