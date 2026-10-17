#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --array=0-2%1
#SBATCH --job-name=qh26-stage2-adaptive-evidence
#SBATCH --output=qh26-stage2-adaptive-evidence-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
OVERLAY="$TASK_ROOT/overlays/adaptive-evidence-a1cc-identity-3faf-v1"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$TASK_ROOT/snapshots/v12-adaptive-recovery"
FIT=0-ppo-2026
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then FIT=1-ppo-2027; fi
if [ "$SLURM_ARRAY_TASK_ID" = 2 ]; then FIT=2-cem-2026; fi
cd "$TASK_ROOT/snapshots/v12-adaptive-recovery"
"$TASK_ROOT/.venv/bin/python" "$OVERLAY/postfit_diagnostic.py" \
 --fit "$TASK_ROOT/results/adaptive-recovery-6117339/$FIT" \
 --output "$TASK_ROOT/results/adaptive-evidence-$SLURM_ARRAY_JOB_ID/$FIT" \
 --training-job "6117339_$SLURM_ARRAY_TASK_ID" --workers 32
