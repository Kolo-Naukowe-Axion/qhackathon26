#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --job-name=qh26-hybrid-cem
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-hybrid-cem-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_ROOT=/home/iwosmu/qh26-stage2-20261016
cd "$TASK_ROOT/snapshots/v19p1-hybrid-schedule"
"$TASK_ROOT/.venv/bin/python" -m stage2.hybrid_schedule --checkpoint "$TASK_ROOT/submissions/v19p1-hybrid-schedule/strong-cem6-2026.json" --output "$TASK_ROOT/results/hybrid-schedule-v19p1-${SLURM_JOB_ID}" --workers 32
