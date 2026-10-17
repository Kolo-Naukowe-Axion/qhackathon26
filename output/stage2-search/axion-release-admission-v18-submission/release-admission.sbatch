#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:10:00
#SBATCH --job-name=qh26-release-adm
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-release-adm-%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_ROOT=/home/iwosmu/qh26-stage2-20261016
cd "$TASK_ROOT/snapshots/v18-release-admission"
"$TASK_ROOT/.venv/bin/python" -m stage2.release_admission --output "$TASK_ROOT/results/release-admission-v18-${SLURM_JOB_ID}" --workers 32
