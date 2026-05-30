#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CorosDev Opportunity Copilot — first-time setup (WSL / Ubuntu)
# Run once:  bash install.sh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e
export PATH="$PATH:/home/$(whoami)/.local/bin"

echo "━━ CorosDev Opportunity Copilot — Install ━━"
echo ""

echo "1. Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

echo ""
echo "2. Installing Playwright Chromium (used for LinkedIn session management)..."
python3 -m playwright install chromium

echo ""
echo "3. Creating required directories..."
mkdir -p data session logs exports

echo ""
echo "━━ Setup complete! ━━"
echo ""
echo "Next steps:"
echo "  1. Copy and configure:"
echo "       cp config.example.yaml config.yaml"
echo "       cp .env.example .env"
echo "       nano .env          # add your API keys and credentials"
echo ""
echo "  2. Run the test suite (safe — no external calls):"
echo "       bash run.sh --test"
echo ""
echo "  3. Start the copilot workflow:"
echo "       bash run.sh --discover-jobs --dry-run    # preview"
echo "       bash run.sh --discover-jobs              # save to DB"
echo "       bash run.sh --score-jobs                 # score by fit"
echo "       bash run.sh --draft-job-application      # generate drafts"
echo "       bash run.sh --review-queue               # review & approve"
echo "       bash run.sh --send-approved              # send approved only"
echo ""
echo "  4. Read the docs: cat README.md"
