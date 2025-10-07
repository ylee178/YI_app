# PTE Validation Checklist

## Quick Reference for Artifact Download & Validation

### Prerequisites
- Python 3.12+ with executorch installed (optional for full tests)
- jq (for JSON parsing)
- Standard Unix tools (shasum, bc)

---

## Step-by-Step Validation Process

### 1. Download Artifact from GitHub Actions

```bash
# Find the latest run ID
cd /Users/uxersean/Desktop/YI_Clean
gh run list --limit 5

# Download artifact (replace <run-id> with actual ID)
gh run download <run-id> -n llama3.2-1b-pte

# Artifact should download to current directory or specified path
# Expected files:
#   - llama3.2-1b-int8-seq512.pte
#   - manifest.json
```

### 2. Quick Manual Checks (30 seconds)

```bash
# Check file exists and size
ls -lh models/llama3.2-1b/*.pte

# Expected: ~1.2-1.5 GB for INT8 quantized Llama 3.2 1B

# Quick SHA256
shasum -a 256 models/llama3.2-1b/*.pte

# Check manifest
cat models/llama3.2-1b/manifest.json | jq
```

### 3. Automated Full Validation (5 minutes)

```bash
# Run comprehensive validation pipeline
cd /Users/uxersean/Desktop/YI_Clean
./tools/run_full_pte_validation.sh models/llama3.2-1b/llama3.2-1b-int8-seq512.pte

# This runs all checks:
#   1. Basic file validation (size, SHA256)
#   2. Guard validation (empty file/partition checks)
#   3. INT8 coverage (heuristic)
#   4. Manifest verification
#   5. KPI smoke test (if ExecuTorch available)
#   6. Report generation
```

### 4. Individual Validation Tools

If full pipeline fails, run individual checks:

```bash
# Basic PTE verification
python3 tools/verify_pte.py models/llama3.2-1b/*.pte --max-size-gb 1.5

# Guard validation (empty file/partition)
python3 tools/validate_pte_guards.py models/llama3.2-1b/*.pte

# INT8 coverage check
python3 tools/validate_int8_coverage.py models/llama3.2-1b/*.pte --target-coverage 0.9

# KPI smoke test (requires ExecuTorch runtime)
python3 tools/kpi_smoke_test.py models/llama3.2-1b/*.pte
```

---

## Validation Criteria (Gates)

### Critical Gates (MUST PASS)
- [ ] File size ≤1.5 GB
- [ ] File is non-empty (size > 0)
- [ ] Buffer is readable and non-empty
- [ ] SHA256 matches manifest (if manifest exists)
- [ ] No crash on load

### Quality Gates (SHOULD PASS - Smoke Test)
- [ ] INT8 coverage ≥90% (heuristic - file size based)
- [ ] TTFT ≤350ms (initial smoke; target: ≤200ms after optimization)
- [ ] tok/s ≥10 (initial smoke; target: ≥18 after optimization)
- [ ] mem_peak ≤3500MB (initial smoke; target: ≤3000MB on 6GB devices)

### Expected Values
```json
{
  "pte_size_gb": "1.2-1.5",
  "partitions": ">0",
  "int8_coverage": "≥90%",
  "ttft_ms": "≤350 (smoke) / ≤200 (optimized)",
  "tok_s": "≥10 (smoke) / ≥18 (optimized)",
  "mem_peak_mb": "≤3500 (smoke) / ≤3000 (optimized)"
}
```

---

## Troubleshooting

### Issue: "Empty PTE file" or size is 0 bytes
**Cause**: Export failed or incomplete download

**Fix**:
```bash
# Re-download artifact
gh run download <run-id> -n llama3.2-1b-pte --clobber

# If still empty, check GitHub Actions logs
gh run view <run-id> --log
```

### Issue: "Empty buffer" or "0 partitions"
**Cause**: Export process generated invalid PTE (IR lowering failed)

**Fix**:
1. Check export logs in GitHub Actions
2. Look for errors in `to_edge()` or `write_to_file()` steps
3. Verify export script has guard checks enabled
4. Re-run export with increased memory limits

### Issue: "SHA256 mismatch"
**Cause**: File corruption during download or manifest out of sync

**Fix**:
```bash
# Re-download artifact
gh run download <run-id> -n llama3.2-1b-pte --clobber

# Regenerate manifest
python3 models/llama3.2-1b/export_pte.py  # Re-run export
```

### Issue: "INT8 coverage < 90%"
**Cause**: Model not properly quantized or export skipped quantization

**Fix**:
1. Check file size: Should be ~1.2-1.5GB for INT8, ~4.8GB for FP32
2. If >2GB, likely FP32 or mixed precision
3. Verify export script applies quantization
4. Re-export with explicit INT8 quantization config

### Issue: "KPI smoke test failed" or "ExecuTorch runtime not available"
**Cause**: ExecuTorch Python bindings not installed

**Fix**:
```bash
# Install ExecuTorch (if available)
pip install executorch

# Or activate ExecuTorch environment
source venv_et/bin/activate
python3 tools/kpi_smoke_test.py models/llama3.2-1b/*.pte
```

---

## Success Criteria Summary

### Minimum Viable PTE (Ready for Runtime Testing)
- [x] File exists and is non-empty
- [x] Size ≤1.5GB
- [x] Buffer readable
- [x] SHA256 verified
- [x] Basic structural validation passes

### Production-Ready PTE (Ready for Deployment)
- [x] All minimum criteria
- [x] INT8 coverage ≥90%
- [x] TTFT ≤200ms
- [x] tok/s ≥18
- [x] mem_peak ≤3.0GB on 6GB device
- [x] Zero crashes in 10-minute stress test
- [x] Quality score (EQ) ≥85/100

---

## Next Steps After Validation

### If All Gates Pass (PASS)
1. Copy PTE to React Native app assets
2. Run on iOS/Android device (not simulator)
3. Measure actual TTFT/tok/s/mem_peak on target hardware
4. Run full benchmark suite (20-turn conversation)
5. Validate quality (EQ score ≥85)

### If Any Gate Fails (FAIL)
1. Review specific failure in validation report
2. Check export logs for errors
3. Investigate root cause (memory, quantization, IR lowering)
4. Apply fix and re-export
5. Re-run validation pipeline

### If Incomplete (INCOMPLETE)
1. Install missing dependencies (ExecuTorch, tokenizer)
2. Re-run validation with full runtime
3. If runtime not available, proceed to device testing
4. Validate KPIs on actual device instead of smoke test

---

## Automated Validation Output

The full validation script generates:
- `results/pte_validation_YYYYMMDD_HHMMSS.json` - Comprehensive report
- `results/int8_coverage_YYYYMMDD_HHMMSS.json` - INT8 analysis
- `results/kpi_smoke_YYYYMMDD_HHMMSS.json` - KPI smoke test results

Review these files for detailed diagnostics.

---

## Quick Commands Reference

```bash
# Full validation (recommended)
./tools/run_full_pte_validation.sh models/llama3.2-1b/*.pte

# Individual checks
python3 tools/verify_pte.py <pte_file> --max-size-gb 1.5
python3 tools/validate_pte_guards.py <pte_file>
python3 tools/validate_int8_coverage.py <pte_file>
python3 tools/kpi_smoke_test.py <pte_file>

# Manual verification
ls -lh <pte_file>                    # Size check
shasum -a 256 <pte_file>             # SHA256
cat manifest.json | jq               # Manifest inspection
```

---

**Estimated Time**:
- Download: 2-5 minutes (depending on network)
- Validation: 5 minutes (full automated pipeline)
- Total: ~10 minutes from artifact ready to validation complete

**Critical Path**:
1. Download artifact (when ready)
2. Run `./tools/run_full_pte_validation.sh`
3. Review report
4. Proceed to runtime testing OR fix issues and re-export
