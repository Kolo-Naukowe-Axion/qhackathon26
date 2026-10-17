#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=6
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --job-name=qh26-stage2-guarded-mpc
#SBATCH --output=qh26-stage2-guarded-mpc-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v17-guarded-evaluation-smoke"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval freeze --selection "$TASK_ROOT/guarded-mpc-development-selection.json" --protocol "$TASK_ROOT/guarded-mpc-development-protocol.json" --development --output "$TASK_ROOT/results/guarded-mpc-$SLURM_JOB_ID-manifest.json"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval run --manifest "$TASK_ROOT/results/guarded-mpc-$SLURM_JOB_ID-manifest.json" --workers 6 --output "$TASK_ROOT/results/guarded-mpc-$SLURM_JOB_ID"
