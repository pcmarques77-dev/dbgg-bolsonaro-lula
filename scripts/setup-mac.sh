#!/usr/bin/env bash
# Configura o projeto no Mac Mini (clone já feito ou pasta existente).
# Uso:
#   cd ~/app-mba-economia-fipe && bash scripts/setup-mac.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Python"
PY="${PY:-python3}"
ver="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
major="${ver%%.*}"
minor="${ver#*.}"
if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 11 ]]; then
  echo "Python >= 3.11 necessário (atual: $ver). Ex.: brew install python@3.12"
  exit 1
fi

echo "==> venv"
"$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

echo "==> smoke test"
python -m mba_economia --start 2019-01-01 --end 2019-06-30 --out-dir output_smoke

echo ""
echo "OK. Próximos passos:"
echo "  1. Abra esta pasta no Cursor (Apple Silicon)."
echo "  2. Python: Select Interpreter -> .venv/bin/python"
echo "  3. Saídas em: output_smoke/"
