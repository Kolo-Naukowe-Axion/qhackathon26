#!/bin/bash
#SBATCH --account=hpc-iwowoj-1781179048
#SBATCH --qos=hpc-iwowoj-1781179048
#SBATCH --partition=bem2-cpu-short
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=00:10:00
#SBATCH --array=0-1%2
#SBATCH --dependency=aftercorr:6117473
#SBATCH --job-name=qh26-static-val
#SBATCH --chdir=/home/iwosmu/qh26-stage2-20261016
#SBATCH --output=/home/iwosmu/qh26-stage2-20261016/qh26-static-val-%A-%a.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_ROOT=/home/iwosmu/qh26-stage2-20261016
cd "$TASK_ROOT/snapshots/v16p2-static-control-validation"
"$TASK_ROOT/.venv/bin/python" -m stage2.static_control_validation --training-report "$TASK_ROOT/results/static-control-v16-6117473-${SLURM_ARRAY_TASK_ID}/report.json" --tasks-out "$TASK_ROOT/submissions/v16p2-static-control-validation/tasks-part${SLURM_ARRAY_TASK_ID}.json"
"$TASK_ROOT/.venv/bin/python" -m stage2.static_control_validation --tasks "$TASK_ROOT/submissions/v16p2-static-control-validation/tasks-part${SLURM_ARRAY_TASK_ID}.json" --output "$TASK_ROOT/results/static-control-validation-v16p2-${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}" --workers 32
