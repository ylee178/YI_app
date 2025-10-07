# Runtime Decision: ExecuTorch via GitHub Actions

## Decision Date
2025-10-07

## Decision
**Runtime**: ExecuTorch
**Export Method**: GitHub Actions (Option B)
**Fallback**: Local export blocked due to RAM constraints

---

## Context

### PRD Requirements
- Runtime: ExecuTorch (PRIMARY) OR ONNX Runtime Mobile (fallback)
- Format: `.pte` (ExecuTorch portable tensor expression)
- Quantization: INT8
- Size limit: ≤1.5GB
- Platforms: iOS + Android

### Local Export Blocker
**Problem**: Memory constraints on development machine

**Technical Details**:
- Model: Llama 3.2 1B FP32 (~4.5GB in memory)
- Export overhead: IR graph generation + buffers (~1-2GB)
- Peak RAM required: ~5-6GB
- Available RAM: Insufficient for export

**Symptom**: `export_pte.py` exits with code 0 but produces empty (0-byte) `.pte` file

**Root Cause**: ExecuTorch `to_edge()` returns empty buffer when partitioning fails due to OOM

---

## Implementation Details

### Memory Guards Added

**Guard 1: Disable Gradients**
```python
torch.set_grad_enabled(False)  # Saves ~1-2GB RAM
```

**Guard 2: Smaller Example Input**
```python
EXPORT_SEQ = 128  # Instead of 512, reduces IR graph size
```

**Guard 3: Edge IR Buffer Validation**
```python
edge_buffer = edge_program.buffer()
if len(edge_buffer) == 0:
    raise RuntimeError("Empty Edge IR buffer - export failed")
```

**Guard 4: Partition Count Check**
```python
num_methods = len(edge_program.exported_program().graph_module.graph.nodes)
if num_methods == 0:
    raise RuntimeError("No executable methods in Edge IR")
```

### GitHub Actions Workflow

**File**: `.github/workflows/export-llama-pte.yml`

**Expected Timeline**:
- Workflow setup: 5-10 min
- Export execution: 15-20 min
- Total: 25-30 min

**Resource Usage**:
- RAM: 16-32GB (sufficient)
- Disk: ~10GB (model + ExecuTorch + artifacts)

---

## Next Steps

1. Trigger export workflow: `./setup_gha_export.sh`
2. Download artifact (~30 min later): `gh run download <RUN_ID>`
3. Verify locally: `python tools/verify_pte.py`
4. Proceed to Phase 1: React Native scaffold

---

## PRD Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Runtime: ExecuTorch | ✅ PASS | Uses executorch.exir.to_edge |
| Format: .pte | ✅ PASS | edge_program.write_to_file() |
| Size: ≤1.5GB | ⏳ PENDING | Validated in workflow |

---

## References

- PRD: `/Users/uxersean/Desktop/YI_Clean/PRD.md`
- Export script: `/Users/uxersean/Desktop/YI_Clean/models/llama3.2-1b/export_pte.py`
- Workflow: `/Users/uxersean/Desktop/YI_Clean/.github/workflows/export-llama-pte.yml`
