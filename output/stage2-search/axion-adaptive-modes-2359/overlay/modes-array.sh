#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:20:00
#SBATCH --array=0-1%2
#SBATCH --job-name=qh26-stage2-adaptive-modes
#SBATCH --output=qh26-stage2-adaptive-modes-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
METHOD=ppo
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then METHOD=cem; fi
cd "$TASK_ROOT/snapshots/v13-adaptive-modes-2359"
"$TASK_ROOT/.venv/bin/python" -m stage2.adaptive_modes --contexts "$TASK_ROOT/adaptive-modes-contexts-2359.json" \
 --output "$TASK_ROOT/results/adaptive-modes-$SLURM_ARRAY_JOB_ID/$SLURM_ARRAY_TASK_ID-$METHOD-2026" \
 --seconds 600 --workers 32 --seed 2026 --method "$METHOD"
