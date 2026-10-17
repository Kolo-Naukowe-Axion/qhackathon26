#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:30:00
#SBATCH --job-name=qh26-stage2-selector-reward
#SBATCH --output=qh26-stage2-selector-reward-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v13-selector-reward"
"$TASK_ROOT/.venv/bin/python" -m stage2.selector_reward \
 --tasks "$TASK_ROOT/selector-reward-full-controls-training-tasks.json" --workers 32 \
 --output "$TASK_ROOT/results/selector-reward-$SLURM_JOB_ID"
