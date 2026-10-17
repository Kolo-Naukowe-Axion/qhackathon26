#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=24G
#SBATCH --time=01:20:00
#SBATCH --job-name=qh26-final-mpc-13
#SBATCH --output=qh26-final-mpc-13-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v20-final-current"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval freeze --selection "$TASK_ROOT/final-preparation-v20p2/mpc-13-selection.json" --protocol "$TASK_ROOT/final-preparation-v20p2/final-heldout-protocol.json" --output "$TASK_ROOT/results/final-mpc-13-$SLURM_JOB_ID-manifest.json"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval run --manifest "$TASK_ROOT/results/final-mpc-13-$SLURM_JOB_ID-manifest.json" --workers 32 --execute-final --output "$TASK_ROOT/results/final-mpc-13-$SLURM_JOB_ID"
