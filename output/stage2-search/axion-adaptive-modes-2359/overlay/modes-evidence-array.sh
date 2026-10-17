#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:10:00
#SBATCH --array=0-1%1
#SBATCH --job-name=qh26-stage2-modes-evidence
#SBATCH --output=qh26-stage2-modes-evidence-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$TASK_ROOT/snapshots/v13-adaptive-modes-2359"
FIT=0-ppo-2026
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then FIT=1-cem-2026; fi
cd "$TASK_ROOT/snapshots/v13-adaptive-modes-2359"
"$TASK_ROOT/.venv/bin/python" "$TASK_ROOT/overlays/adaptive-modes-2359/modes_postfit.py" \
 --fit "$TASK_ROOT/results/adaptive-modes-6117468/$FIT" \
 --output "$TASK_ROOT/results/adaptive-modes-evidence-$SLURM_ARRAY_JOB_ID/$FIT" \
 --training-job "6117468_$SLURM_ARRAY_TASK_ID" --workers 32
