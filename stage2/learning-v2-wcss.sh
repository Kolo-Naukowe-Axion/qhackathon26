#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-3%2
#SBATCH --job-name=qh26-stage2-learn-v2
#SBATCH --output=qh26-stage2-learn-v2-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v2p1-rl"
METHODS=(ppo ppo bandit cem)
SEEDS=(2026 2027 2026 2026)
METHOD="${METHODS[$SLURM_ARRAY_TASK_ID]}"
RUN_SEED="${SEEDS[$SLURM_ARRAY_TASK_ID]}"
EXTRA=()
if test "$METHOD" != cem; then
 EXTRA+=(--warm-start-static "$TASK_ROOT/results/learning-v1-6116807/static/checkpoint.json" --warm-start-episodes 8)
fi
"$TASK_ROOT/.venv/bin/python" -m stage2.sequential --method "$METHOD" \
 --orders 8,12,16,24 --seconds 1800 --workers 32 --batch-episodes 64 \
 --selector priority --seed "$RUN_SEED" --validation-every 5 "${EXTRA[@]}" \
 --output "$TASK_ROOT/results/learning-v2-$SLURM_ARRAY_JOB_ID/$METHOD-$RUN_SEED"
