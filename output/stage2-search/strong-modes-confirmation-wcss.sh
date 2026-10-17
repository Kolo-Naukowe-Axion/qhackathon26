#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:30:00
#SBATCH --job-name=qh26-stage2-modes-confirm
#SBATCH --output=qh26-stage2-modes-confirm-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v11-strong-mpc"
"$TASK_ROOT/.venv/bin/python" -m stage2.tournament \
 --tasks "$TASK_ROOT/strong-modes-confirmation-tasks.json" --workers 32 --max-seconds 1500 \
 --output "$TASK_ROOT/results/modes-confirm-$SLURM_JOB_ID"
