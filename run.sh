#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CorosDev Opportunity Copilot — runner
#
# Usage:
#   bash run.sh --help
#   bash run.sh --test
#   bash run.sh --seed-demo-data
#   bash run.sh --daily-brief
#   bash run.sh --discover-jobs --dry-run
#   bash run.sh --review-queue
#
# SAFETY RULES:
#   Nothing is sent or applied without explicit --approve + --send-approved.
#   --apply is removed. --send-outreach does not send.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$PROJECT_DIR"
export PYTHONUTF8=1
cd "$PROJECT_DIR"

# ── Python resolution: prefer .venv, then system python3 ──────────────────────
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    # Warn if using system python (not venv)
    if [ "$1" != "--test" ] && [ "$1" != "--help" ] && [ -z "$COPILOT_SKIP_VENV_WARN" ]; then
        echo "⚠  Warning: .venv not found. Using system python3." >&2
        echo "   Run 'bash install.sh' to set up a proper virtual environment." >&2
        echo "   (Set COPILOT_SKIP_VENV_WARN=1 to suppress this message)" >&2
        echo "" >&2
    fi
else
    echo "ERROR: Python not found." >&2
    echo "  Run 'bash install.sh' to set up the project first." >&2
    exit 1
fi

# ── Sanity check: verify key dependencies are importable ─────────────────────
if [ "$1" != "--test" ]; then
    if ! "$PYTHON" -c "import yaml, anthropic" 2>/dev/null; then
        echo "ERROR: Required dependencies not installed." >&2
        echo "  Run 'bash install.sh' to install them." >&2
        exit 1
    fi
fi

# ── Auto-load .env (never commits secrets) ───────────────────────────────────
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

# ── Test shortcut ─────────────────────────────────────────────────────────────
if [ "$1" = "--test" ]; then
    shift
    echo "Running CorosDev Opportunity Copilot test suite..."
    "$PYTHON" -m pytest tests/ -v "$@"
    exit $?
fi

# ── Run main application ──────────────────────────────────────────────────────
exec "$PYTHON" main.py "$@"
