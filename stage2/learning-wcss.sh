#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --array=0-4%3
#SBATCH --job-name=qh26-stage2-learn-v1
#SBATCH --output=qh26-stage2-learn-v1-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
METHODS=(ppo static cem bandit random)
METHOD="${METHODS[$SLURM_ARRAY_TASK_ID]}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v1-rl"
"$TASK_ROOT/.venv/bin/python" -m stage2.sequential --method "$METHOD" \
 --orders 8,12,16,24 --seconds 600 --workers 32 --batch-episodes 64 \
 --selector priority --seed 2026 \
 --output "$TASK_ROOT/results/learning-v1-$SLURM_ARRAY_JOB_ID/$METHOD"
