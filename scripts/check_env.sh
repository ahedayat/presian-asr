#!/usr/bin/env bash
# Verify Python, ffmpeg, and core dependencies for Persian ASR.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

failures=0

pass() {
  printf 'OK   %s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  failures=$((failures + 1))
}

warn() {
  printf 'WARN %s\n' "$1"
}

echo "Persian ASR environment check"
echo "Project root: $PROJECT_ROOT"
echo

if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  fail "Python interpreter not found (need python3)"
  exit 1
fi

py_version="$("$python_bin" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY
)"

if "$python_bin" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
then
  pass "Python $py_version (>= 3.10)"
else
  fail "Python $py_version (need >= 3.10)"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg_version="$(ffmpeg -version 2>/dev/null | head -n 1 || true)"
  pass "ffmpeg available (${ffmpeg_version:-unknown version})"
else
  fail "ffmpeg not found on PATH (install: sudo apt install -y ffmpeg)"
fi

if "$python_bin" -c "import torch" >/dev/null 2>&1; then
  torch_version="$("$python_bin" -c "import torch; print(torch.__version__)")"
  pass "import torch ($torch_version)"
else
  fail "import torch failed (pip install -e . in project venv)"
fi

if "$python_bin" -c "import transformers" >/dev/null 2>&1; then
  transformers_version="$("$python_bin" -c "import transformers; print(transformers.__version__)")"
  pass "import transformers ($transformers_version)"
else
  fail "import transformers failed (pip install -e . in project venv)"
fi

if "$python_bin" -c "import PyQt6" >/dev/null 2>&1; then
  qt_version="$("$python_bin" -c "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)")"
  pass "import PyQt6 ($qt_version)"
else
  fail "import PyQt6 failed (pip install -e . in project venv)"
fi

device="$("$python_bin" - <<'PY' 2>/dev/null || echo "unknown"
import torch
print(torch.device("cpu"))
PY
)"
if [[ "$device" == *cpu* ]]; then
  pass "CPU device available ($device)"
else
  warn "Unexpected default device: $device (app is CPU-first only)"
fi

if [[ -f "$PROJECT_ROOT/.env" ]]; then
  pass ".env present"
else
  warn ".env not found (optional; copy from .env.example)"
fi

echo
if [[ "$failures" -eq 0 ]]; then
  echo "All required checks passed."
  exit 0
fi

echo "$failures check(s) failed."
exit 1
