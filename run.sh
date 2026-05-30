#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CorosDev Opportunity Copilot — run script (WSL / Ubuntu)
#
# COPILOT WORKFLOW (human-in-the-loop — nothing sent without approval):
#   bash run.sh --discover-jobs            # load jobs from CSV, no applying
#   bash run.sh --score-jobs               # score 0-100 by skill/location fit
#   bash run.sh --draft-job-application    # generate drafts (Claude, no send)
#   bash run.sh --review-queue             # review + approve interactively
#   bash run.sh --approve 42               # approve draft #42 after reading it
#   bash run.sh --send-approved            # send ONLY approved items (+ confirmation)
#   bash run.sh --daily-brief              # summary of top jobs, leads, actions
#
# LEADS / CLIENTS:
#   bash run.sh --discover-leads
#   bash run.sh --score-leads
#   bash run.sh --draft-client-outreach
#   bash run.sh --review-queue --type client
#
# SAFE PREVIEW (writes nothing, makes no external calls):
#   bash run.sh --discover-jobs --dry-run
#   bash run.sh --score-jobs --dry-run
#   bash run.sh --draft-job-application --dry-run
#
# TESTS (run before using real data):
#   bash run.sh --test
#   bash run.sh --test -v
#
# UTILITIES:
#   bash run.sh --stats
#   bash run.sh --export-contacts
#   bash run.sh --export-outreach
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e
export PATH="$PATH:/home/$(whoami)/.local/bin"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$PROJECT_DIR"
export PYTHONUTF8=1
cd "$PROJECT_DIR"

# Auto-load .env if present (never required — use ${ENV_VAR} in config.yaml)
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

if [ "$1" = "--test" ]; then
    shift
    echo "Running CorosDev Opportunity Copilot test suite..."
    python3 -m pytest tests/ -v "$@"
    exit $?
fi

python3 main.py "$@"
