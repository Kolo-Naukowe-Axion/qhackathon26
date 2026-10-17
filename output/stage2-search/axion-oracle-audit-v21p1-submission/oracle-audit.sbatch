#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --job-name=qh26-oracle-audit
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-oracle-audit-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_ROOT=/home/iwosmu/qh26-stage2-20261016
cd "$TASK_ROOT/snapshots/v21p1-oracle-audit"
"$TASK_ROOT/.venv/bin/python" -m stage2.schedule_neighborhood_audit --checkpoint "$TASK_ROOT/submissions/v21p1-oracle-audit/strong-cem6-2026.json" --output "$TASK_ROOT/results/oracle-audit-v21p1-${SLURM_JOB_ID}" --workers 32 --seconds 1680
