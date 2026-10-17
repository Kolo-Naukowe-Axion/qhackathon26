#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --job-name=qh26-stage2-mpc
#SBATCH --output=qh26-stage2-mpc-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v2-mpc"
"$TASK_ROOT/.venv/bin/python" -m stage2.tournament \
 --tasks "$TASK_ROOT/mpc-training-tasks.json" --workers 32 --max-seconds 2400 \
 --output "$TASK_ROOT/results/mpc-v2-$SLURM_JOB_ID"
