#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=24G
#SBATCH --time=00:10:00
#SBATCH --job-name=qh26-stage2-legacy-preflight
#SBATCH --output=qh26-stage2-legacy-preflight-v18p1-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v18p1-legacy-evaluation-preflight"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval freeze --selection "$TASK_ROOT/final-preparation/legacy-selection-draft.json" --protocol "$TASK_ROOT/final-preparation/development-protocol.json" --development --output "$TASK_ROOT/results/legacy-preflight-v18p1-$SLURM_JOB_ID-manifest.json"
"$TASK_ROOT/.venv/bin/python" -m stage2.final_eval run --manifest "$TASK_ROOT/results/legacy-preflight-v18p1-$SLURM_JOB_ID-manifest.json" --workers 32 --output "$TASK_ROOT/results/legacy-preflight-v18p1-$SLURM_JOB_ID"
