#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --job-name=qh26-stage2-grid-v1
#SBATCH --output=qh26-stage2-grid-v1-%j.log
set -euo pipefail
TASK_ROOT="$HOME/qh26-stage2-20261016"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
cd "$TASK_ROOT/snapshots/v1-core"
"$TASK_ROOT/.venv/bin/python" -m stage2.tournament --orders 3,6,8,12,16,24,32 \
 --seeds 0,1,2,3,4,5,6,7 --wips 1,2,3,4,6,8,12,24 \
 --modes eco,standard,turbo --leases 0,1 --selectors priority \
 --workers 32 --max-seconds 5400 --output "$TASK_ROOT/results/grid-v1-$SLURM_JOB_ID"
