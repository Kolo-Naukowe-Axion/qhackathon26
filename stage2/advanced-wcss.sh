#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:45:00
#SBATCH --job-name=qh26-stage2-advanced
#SBATCH --output=qh26-stage2-advanced-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v3-advanced"
"$TASK_ROOT/.venv/bin/python" -m stage2.tournament \
 --tasks "$TASK_ROOT/advanced-training-tasks.json" --workers 32 --max-seconds 2400 \
 --output "$TASK_ROOT/results/advanced-v3-$SLURM_JOB_ID"
