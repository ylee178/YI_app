# Pre-Flight Checklist: GitHub Actions Export

Before running `./setup_gha_export.sh`, ensure:

## Prerequisites

- [ ] HuggingFace token available at `~/.cache/huggingface/token`
  - Generate at: https://huggingface.co/settings/tokens
  - Requires: Read access to gated models (Llama 3.2)

- [ ] GitHub CLI installed: `gh --version`
  - Install: `brew install gh` (macOS) or https://cli.github.com/

- [ ] Git configured
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```

- [ ] GitHub account with access to create repos
  - If using existing repo, ensure push access

## Verify Environment

```bash
# Check HF token
[ -f ~/.cache/huggingface/token ] && echo "✅ HF token found" || echo "❌ HF token missing"

# Check GitHub CLI
gh --version && echo "✅ gh installed" || echo "❌ gh not installed"

# Check git
git --version && echo "✅ git installed" || echo "❌ git not installed"
```

## Ready to Run

```bash
cd /Users/uxersean/Desktop/YI_Clean
./setup_gha_export.sh
```

## Manual Setup (if script fails)

See: `docs/gha_export_guide.md` → "Manual Setup" section

## Expected Output

After workflow completes (~30 min):

```
Artifact: llama3.2-1b-pte-<SHA>
  - llama3.2-1b-int8-seq512.pte (≤1.5GB)
  - manifest.json
  - export_pte_log.txt
```

## Troubleshooting

**Issue**: HF token not found
- **Fix**: `huggingface-cli login`

**Issue**: gh not authenticated
- **Fix**: `gh auth login`

**Issue**: Workflow fails
- **Check logs**: `gh run view <RUN_ID> --log`

## Support

- Documentation: `docs/gha_export_guide.md`
- Quick start: `QUICKSTART_GHA_EXPORT.md`
