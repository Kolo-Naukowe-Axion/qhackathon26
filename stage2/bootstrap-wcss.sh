#!/bin/bash
# Run only inside a Slurm allocation on the user's verified Axion grant.
set -euo pipefail
test -n "${SLURM_JOB_ID:-}"
TASK_ROOT="$HOME/qh26-stage2-20261016"
mkdir -p "$TASK_ROOT"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
"$HOME/.local/bin/uv" venv --python "$HOME/qhackathon26-stage1/.venv/bin/python" "$TASK_ROOT/.venv"
"$HOME/.local/bin/uv" pip install --python "$TASK_ROOT/.venv/bin/python" torch --index-url https://download.pytorch.org/whl/cpu
"$HOME/.local/bin/uv" pip install --python "$TASK_ROOT/.venv/bin/python" numpy scipy ortools
"$TASK_ROOT/.venv/bin/python" - <<'PY'
import platform, torch, numpy, scipy, ortools
print(dict(python=platform.python_version(),torch=torch.__version__,numpy=numpy.__version__,
           scipy=scipy.__version__,ortools=ortools.__version__,cuda=torch.cuda.is_available()))
PY
