# Quick Start: GitHub Actions Export

## Problem
Local PTE export fails due to insufficient RAM (needs ~5-6GB peak).

## Solution
Export on GitHub Actions runners (16-32GB RAM available).

---

## Setup (5 minutes)

```bash
cd /Users/uxersean/Desktop/YI_Clean

# Run interactive setup
./setup_gha_export.sh
```

**What it does:**
1. Initialize git repo
2. Configure GitHub remote
3. Set HF_TOKEN secret
4. Commit + push workflow
5. Trigger export

---

## Manual Trigger

```bash
# Trigger workflow
gh workflow run export-llama-pte.yml

# Watch progress
gh run watch

# View logs
gh run view --log
```

---

## Download Result (~25-30 min later)

```bash
# List recent runs
gh run list --workflow=export-llama-pte.yml

# Download artifact
gh run download <RUN_ID>

# Move to project
mv ~/Downloads/llama3.2-1b-pte-*/*.pte models/llama3.2-1b/
mv ~/Downloads/llama3.2-1b-pte-*/manifest.json models/llama3.2-1b/
```

---

## Validate

```bash
cd models/llama3.2-1b

# Check size (must be ≤1.5GB)
ls -lh *.pte

# Verify manifest
cat manifest.json | jq '.prd_compliant, .pte_size_gb'
# Expected: true, <value ≤ 1.5>

# SHA256 integrity
shasum -a 256 *.pte
# Compare with manifest.json sha256 field
```

---

## Success Criteria

- File: `llama3.2-1b-int8-seq512.pte`
- Size: ≤1.5GB
- Format: ExecuTorch .pte
- PRD compliant: true
- SHA256: matches manifest

---

## Next Steps

1. Copy .pte to React Native app assets
2. Implement iOS native module (ExecuTorch runtime)
3. Run local benchmark
4. Verify KPI gates (TTFT, tok/s, memory)

---

## Help

- Full docs: `docs/gha_export_guide.md`
- Troubleshooting: Check workflow logs with `gh run view <ID> --log`
- Support: File issue on ExecuTorch repo if export guards fail
