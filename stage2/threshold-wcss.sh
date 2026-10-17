#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --array=0-2%2
#SBATCH --job-name=qh26-stage2-threshold
#SBATCH --output=qh26-stage2-threshold-%A_%a.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
METHODS=(cem cem random)
SEEDS=(2026 2027 2026)
METHOD="${METHODS[$SLURM_ARRAY_TASK_ID]}"
RUN_SEED="${SEEDS[$SLURM_ARRAY_TASK_ID]}"
cd "$TASK_ROOT/snapshots/v2-threshold"
"$TASK_ROOT/.venv/bin/python" -m stage2.threshold --method "$METHOD" \
 --orders 8,12,16,24 --seconds 1800 --workers 32 --candidates 24 --generations 120 \
 --paired-tapes 8 --validation-every 5 --rerank-pool 8 --seed "$RUN_SEED" \
 --teacher "$TASK_ROOT/results/learning-v1-6116807/static/checkpoint.json" \
 --output "$TASK_ROOT/results/threshold-v2-$SLURM_ARRAY_JOB_ID/$METHOD-$RUN_SEED"
