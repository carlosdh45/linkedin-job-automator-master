#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CorosDev Opportunity Copilot — First-time setup
#
# Supports: Ubuntu/WSL (primary), macOS (secondary)
# Run once: bash install.sh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "━━ CorosDev Opportunity Copilot — Setup ━━"
echo ""

# ── 1. Check Python 3.10+ ─────────────────────────────────────────────────────
echo "1. Checking Python version..."

PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON_BIN="$cmd"
            echo "   Found: $("$cmd" --version) at $(command -v "$cmd")"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo ""
    echo "ERROR: Python 3.10 or higher is required."
    echo ""
    echo "Ubuntu/WSL:"
    echo "  sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip"
    echo ""
    echo "macOS (with Homebrew):"
    echo "  brew install python@3.11"
    exit 1
fi

# ── 2. Create virtual environment ─────────────────────────────────────────────
echo ""
echo "2. Setting up virtual environment..."

if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
    echo "   Created .venv"
else
    echo "   .venv already exists — skipping creation"
fi

VENV_PYTHON=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: .venv/bin/python not found after venv creation."
    exit 1
fi

# ── 3. Install dependencies ───────────────────────────────────────────────────
echo ""
echo "3. Installing Python dependencies..."
"$VENV_PIP" install --upgrade pip --quiet
"$VENV_PIP" install -r requirements.txt --quiet
echo "   Dependencies installed."

# ── 4. Install Playwright Chromium ────────────────────────────────────────────
echo ""
echo "4. Installing Playwright Chromium browser..."
"$VENV_PYTHON" -m playwright install chromium --quiet
echo "   Playwright Chromium installed."

# ── 5. Create required directories ───────────────────────────────────────────
echo ""
echo "5. Creating runtime directories..."
mkdir -p data session logs exports
echo "   data/ session/ logs/ exports/ created."

# ── 6. Copy config files (never overwrite existing) ──────────────────────────
echo ""
echo "6. Setting up config files..."

if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "   config.yaml created from config.example.yaml"
    echo "   ▶ Edit config.yaml and fill in your settings."
else
    echo "   config.yaml already exists — not overwriting."
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "   .env created from .env.example"
    echo "   ▶ Edit .env and fill in your API keys and credentials."
else
    echo "   .env already exists — not overwriting."
fi

if [ ! -f profile.yaml ]; then
    cp profile.example.yaml profile.yaml
    echo "   profile.yaml created from profile.example.yaml"
    echo "   ▶ Edit profile.yaml with your skills, roles, and business context."
else
    echo "   profile.yaml already exists — not overwriting."
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━ Setup complete! ━━"
echo ""
echo "Next steps:"
echo ""
echo "  1. Fill in your credentials:"
echo "       nano .env"
echo ""
echo "  2. Update your config:"
echo "       nano config.yaml"
echo "       nano profile.yaml"
echo ""
echo "  3. Run the test suite (safe — no external calls):"
echo "       bash run.sh --test"
echo ""
echo "  4. Seed demo data for safe local testing:"
echo "       bash run.sh --seed-demo-data"
echo "       bash run.sh --daily-brief"
echo ""
echo "  5. Start the copilot workflow:"
echo "       bash run.sh --discover-jobs --dry-run"
echo "       bash run.sh --discover-jobs"
echo "       bash run.sh --score-jobs"
echo "       bash run.sh --draft-job-application"
echo "       bash run.sh --review-queue"
echo ""
echo "  Read the full guide: cat README.md"
echo "  Test workflow: cat TESTING.md"
