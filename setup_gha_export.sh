#!/bin/bash
set -e

echo "=========================================="
echo "GitHub Actions Export Setup"
echo "=========================================="

# Step 1: Initialize git repository if needed
if [ ! -d .git ]; then
    echo "[1/6] Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: YI emotional AI companion project"
else
    echo "[1/6] Git repository already initialized"
fi

# Step 2: Check for GitHub remote
if ! git remote | grep -q origin; then
    echo ""
    echo "[2/6] No GitHub remote configured."
    echo "Please create a GitHub repository and add remote:"
    echo ""
    echo "  gh repo create YI --private --source=. --push"
    echo ""
    echo "OR manually:"
    echo ""
    echo "  git remote add origin https://github.com/YOUR_USERNAME/YI.git"
    echo "  git branch -M main"
    echo "  git push -u origin main"
    echo ""
    read -p "Press Enter after configuring remote to continue..."
else
    echo "[2/6] GitHub remote configured: $(git remote get-url origin)"
fi

# Step 3: Check for HF_TOKEN secret
echo ""
echo "[3/6] Checking HuggingFace token..."

if [ -f ~/.cache/huggingface/token ]; then
    echo "Found local HF token at ~/.cache/huggingface/token"
    echo ""
    echo "Setting GitHub secret HF_TOKEN..."

    if command -v gh &> /dev/null; then
        gh secret set HF_TOKEN < ~/.cache/huggingface/token
        echo "✅ HF_TOKEN secret configured"
    else
        echo "⚠️  GitHub CLI (gh) not found."
        echo "Please install gh or manually set secret:"
        echo ""
        echo "  GitHub repo → Settings → Secrets → Actions → New secret"
        echo "  Name: HF_TOKEN"
        echo "  Value: <your HuggingFace token>"
        echo ""
        read -p "Press Enter after configuring secret to continue..."
    fi
else
    echo "⚠️  No HuggingFace token found at ~/.cache/huggingface/token"
    echo ""
    echo "Please configure HF_TOKEN secret manually:"
    echo "  GitHub repo → Settings → Secrets → Actions → New secret"
    echo "  Name: HF_TOKEN"
    echo "  Value: <your HuggingFace token>"
    echo ""
    read -p "Press Enter after configuring secret to continue..."
fi

# Step 4: Commit workflow file
echo ""
echo "[4/6] Committing GitHub Actions workflow..."
git add .github/workflows/export-llama-pte.yml
git add models/llama3.2-1b/export_pte.py
git commit -m "Add GitHub Actions workflow for PTE export with memory guards" || echo "Already committed"

# Step 5: Push to remote
echo ""
echo "[5/6] Pushing to GitHub..."
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$BRANCH" || echo "Push failed - check remote configuration"

# Step 6: Trigger workflow
echo ""
echo "[6/6] Triggering export workflow..."

if command -v gh &> /dev/null; then
    echo "Triggering workflow via GitHub CLI..."
    gh workflow run export-llama-pte.yml

    echo ""
    echo "✅ Workflow triggered!"
    echo ""
    echo "Monitor progress:"
    echo "  gh run watch"
    echo ""
    echo "Or view in browser:"
    echo "  gh run list --workflow=export-llama-pte.yml"
    echo ""
    echo "Expected timeline:"
    echo "  - Workflow setup: ~5-10 min"
    echo "  - Export execution: ~15-20 min"
    echo "  - Total: ~25-30 min"
    echo ""
    echo "Download artifact when complete:"
    echo "  gh run download --name llama3.2-1b-pte-<SHA>"
else
    echo "⚠️  GitHub CLI (gh) not found."
    echo "Please trigger workflow manually:"
    echo "  GitHub repo → Actions → Export Llama 3.2 1B PTE → Run workflow"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
