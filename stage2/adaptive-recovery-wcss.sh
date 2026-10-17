#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=00:35:00
#SBATCH --array=0-2%2
#SBATCH --job-name=qh26-stage2-adaptive-recovery
#SBATCH --output=qh26-stage2-adaptive-recovery-%A-%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
METHOD=ppo
FIT_SEED=2026
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then FIT_SEED=2027; fi
if [ "$SLURM_ARRAY_TASK_ID" = 2 ]; then METHOD=cem; fi
cd "$TASK_ROOT/snapshots/v12-adaptive-recovery"
"$TASK_ROOT/.venv/bin/python" -m stage2.adaptive_recovery \
 --contexts "$TASK_ROOT/adaptive-recovery-contexts.json" --workers 32 --seconds 1200 \
 --seed "$FIT_SEED" --method "$METHOD" \
 --output "$TASK_ROOT/results/adaptive-recovery-$SLURM_ARRAY_JOB_ID/$SLURM_ARRAY_TASK_ID-$METHOD-$FIT_SEED"
