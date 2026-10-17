#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:10:00
#SBATCH --array=0-2%1
#SBATCH --job-name=qh26-stage2-guarded-v12
#SBATCH --output=qh26-stage2-guarded-v12-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$TASK_ROOT/snapshots/v13-adaptive-modes-2359"
FIT=0-ppo-2026
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then FIT=1-ppo-2027; fi
if [ "$SLURM_ARRAY_TASK_ID" = 2 ]; then FIT=2-cem-2026; fi
cd "$TASK_ROOT/snapshots/v13-adaptive-modes-2359"
"$TASK_ROOT/.venv/bin/python" "$TASK_ROOT/overlays/adaptive-modes-2359/guarded_selected_replay.py" \
 --seal "$TASK_ROOT/results/adaptive-evidence-6117453/$FIT/selected-seal" \
 --output "$TASK_ROOT/results/guarded-v12-$SLURM_ARRAY_JOB_ID/$FIT" --workers 32
