# INT8 Coverage Extraction - Research & Implementation Guide

## Overview
This document outlines methods to extract and validate INT8 quantization coverage from ExecuTorch PTE files.

---

## Method 1: ExecuTorch SDK Graph Inspection (PREFERRED)

### Approach
Use ExecuTorch's Python SDK to load the PTE file and inspect the computation graph for quantization operations.

### Implementation

```python
from executorch.exir import EdgeProgramManager
from executorch.sdk import Inspector

def extract_int8_coverage_sdk(pte_path: str) -> dict:
    """
    Extract INT8 coverage using ExecuTorch SDK

    Returns:
        {
            'total_ops': int,
            'quantized_ops': int,
            'int8_coverage': float,
            'quantized_layers': list,
            'fp32_layers': list
        }
    """
    # Load PTE
    inspector = Inspector(pte_path)

    # Get event blocks (operations)
    event_blocks = inspector.get_all_event_blocks()

    total_ops = 0
    quantized_ops = 0
    quantized_layers = []
    fp32_layers = []

    for block in event_blocks:
        for event in block.events:
            op_name = event.name
            total_ops += 1

            # Check if operation is quantized
            # Quantized ops typically have names like:
            # - quantized_conv2d
            # - quantized_linear
            # - quantize_per_tensor
            # - dequantize
            if 'quantized' in op_name.lower() or 'int8' in op_name.lower():
                quantized_ops += 1
                quantized_layers.append(op_name)
            else:
                fp32_layers.append(op_name)

    coverage = quantized_ops / total_ops if total_ops > 0 else 0.0

    return {
        'total_ops': total_ops,
        'quantized_ops': quantized_ops,
        'int8_coverage': coverage,
        'quantized_layers': quantized_layers[:10],  # First 10
        'fp32_layers': fp32_layers[:10]  # First 10
    }
```

### Dependencies
```bash
pip install executorch
# Or use ExecuTorch venv
source venv_et/bin/activate
```

### Expected Output
```json
{
  "total_ops": 256,
  "quantized_ops": 240,
  "int8_coverage": 0.9375,
  "quantized_layers": [
    "quantized_linear_0",
    "quantized_linear_1",
    ...
  ],
  "fp32_layers": [
    "embedding",
    "layernorm",
    ...
  ]
}
```

---

## Method 2: Graph Module Inspection (Alternative)

### Approach
Load the exported graph directly and count quantization nodes.

```python
import torch
from executorch.exir import to_edge

def extract_int8_coverage_graph(pte_path: str) -> dict:
    """
    Extract INT8 coverage by inspecting FX graph

    Note: Requires access to the original exported_program,
          not just the serialized .pte file
    """
    # This requires the EdgeProgram object, not just PTE binary
    # Typically done during export, not post-export validation

    # Load graph (placeholder - actual method TBD)
    # graph_module = load_graph_from_pte(pte_path)

    total_nodes = 0
    quantized_nodes = 0

    for node in graph_module.graph.nodes:
        total_nodes += 1

        # Check node target
        if node.op == 'call_function':
            target_name = str(node.target)
            if any(q in target_name for q in ['quantize', 'int8', 'quant']):
                quantized_nodes += 1

        # Check node metadata
        if hasattr(node, 'meta') and 'dtype' in node.meta:
            if node.meta['dtype'] == torch.qint8:
                quantized_nodes += 1

    coverage = quantized_nodes / total_nodes if total_nodes > 0 else 0.0

    return {
        'total_nodes': total_nodes,
        'quantized_nodes': quantized_nodes,
        'int8_coverage': coverage
    }
```

### Limitation
This requires access to the EdgeProgram/ExportedProgram object, not just the serialized .pte file. Best used during export, not post-export validation.

---

## Method 3: Binary Size Heuristic (CURRENT IMPLEMENTATION)

### Approach
Estimate INT8 coverage based on file size relative to expected sizes for FP32 vs INT8.

### Formula
```python
# Llama 3.2 1B parameters: ~1.23B
# FP32: 4 bytes/param → ~4.9 GB
# INT8: 1 byte/param + overhead → ~1.2-1.5 GB

PARAMS = 1.23e9
FP32_SIZE = PARAMS * 4  # ~4.9 GB
INT8_SIZE = PARAMS * 1.2  # ~1.5 GB (with overhead)

actual_size_gb = file_size_bytes / (1024**3)

if actual_size_gb < 2.0:
    estimated_coverage = 0.95  # High confidence INT8
elif actual_size_gb < 3.0:
    estimated_coverage = 0.70  # Mixed
else:
    estimated_coverage = 0.30  # Likely FP32
```

### Accuracy
- **Pros**: Fast, no SDK required, works on any .pte file
- **Cons**: Imprecise (±10-20% error), doesn't distinguish partial quantization
- **Use case**: Quick smoke test, fallback when SDK unavailable

---

## Method 4: Embedded Metadata Parsing (If Available)

### Approach
Some PTE files may embed quantization metadata in headers or auxiliary data.

```python
import struct

def extract_metadata(pte_path: str) -> dict:
    """
    Extract embedded metadata from PTE file

    ExecuTorch PTE format may include:
    - Magic bytes
    - Version info
    - Quantization config
    - Layer metadata
    """
    with open(pte_path, 'rb') as f:
        # Read header (first 256 bytes)
        header = f.read(256)

        # Parse header structure (format TBD based on ExecuTorch spec)
        # Example (placeholder):
        # - Bytes 0-4: Magic number
        # - Bytes 4-8: Version
        # - Bytes 8-12: Quantization mode (0=FP32, 1=INT8, 2=INT4)
        # - Bytes 12-16: Number of layers

        # This is highly dependent on ExecuTorch PTE format
        # Consult ExecuTorch documentation for exact spec

    return {
        'format_version': 'unknown',
        'quantization_mode': 'unknown',
        'metadata_available': False
    }
```

### Status
- **Current**: Not implemented (PTE format specification needed)
- **Next steps**: Review ExecuTorch PTE serialization format docs

---

## Recommended Approach for YI Clean Project

### Phase 1: Immediate (Artifact Validation)
Use **Method 3 (Size Heuristic)** for quick validation:
- Expected size: 1.2-1.5 GB for INT8
- If file is >2 GB, flag as potential quantization failure
- Low precision but fast (< 1 second)

```bash
python3 tools/validate_int8_coverage.py models/llama3.2-1b/*.pte
```

### Phase 2: Integration (Post-Download)
Implement **Method 1 (SDK Inspection)** when ExecuTorch runtime is available:
- Precise op-level coverage
- Identifies which layers are/aren't quantized
- Validates expected 90%+ INT8 coverage

```python
# In export_pte.py, add post-export validation:
from tools.validate_int8_coverage import extract_int8_coverage_sdk

manifest['int8_coverage'] = extract_int8_coverage_sdk(OUTPUT_FILE)
```

### Phase 3: CI/CD (Automated)
Add INT8 coverage gate to GitHub Actions:

```yaml
- name: Validate INT8 Coverage
  run: |
    python3 tools/validate_int8_coverage.py \
      models/llama3.2-1b/llama3.2-1b-int8-seq512.pte \
      --target-coverage 0.9 \
      --json-output int8_report.json

    # Fail if coverage < 90%
    coverage=$(jq -r '.int8_coverage' int8_report.json)
    if (( $(echo "$coverage < 0.9" | bc -l) )); then
      echo "FAIL: INT8 coverage $coverage < 0.9"
      exit 1
    fi
```

---

## Expected INT8 Coverage for Llama 3.2 1B

### Typical Coverage
- **Linear layers**: 100% quantized (most compute)
- **Embeddings**: 0% quantized (lookup tables, no benefit)
- **LayerNorm**: 0% quantized (small compute, precision-sensitive)
- **Attention**: 90%+ quantized (Q, K, V projections)

### Overall Target
- **Total ops**: 90-95% INT8 coverage
- **By compute**: 95-98% INT8 (weighted by FLOPs)
- **By memory**: 75-80% INT8 (embeddings are FP32)

### Validation Criteria
```python
# Strict gate (production)
assert int8_coverage >= 0.90, "INT8 coverage below 90%"

# Soft gate (smoke test)
if int8_coverage < 0.80:
    warnings.warn("INT8 coverage unexpectedly low")
```

---

## Common Issues & Fixes

### Issue: Coverage shows 0% INT8
**Cause**: Export script didn't apply quantization

**Fix**:
```python
# In export_pte.py, ensure quantization is applied
from torch.ao.quantization import quantize_dynamic

quantized_model = quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)
```

### Issue: Coverage is 50-60%
**Cause**: Partial quantization (only some layers)

**Fix**:
1. Review quantization config
2. Ensure all Linear layers are included
3. Check for quantization errors in export logs

### Issue: Coverage is 100%
**Unexpected**: Embeddings should typically be FP32

**Check**:
1. Verify embedding layers are excluded from quantization
2. Confirm coverage calculation is correct
3. May be acceptable if embeddings are small

---

## Integration with QA Pipeline

### Updated `validate_pte_guards.py`
```python
# Add INT8 coverage check to guard validation
def validate_pte(pte_path: str):
    # ... existing checks ...

    # INT8 Coverage Guard
    print("[GUARD 4] INT8 Coverage Validation")
    try:
        from validate_int8_coverage import analyze_pte_quantization
        result = analyze_pte_quantization(pte_path, target_coverage=0.9)

        if result['validation_status'] == 'PASS':
            print(f"  PASS: INT8 coverage {result['int8_coverage']:.1%}")
        else:
            print(f"  FAIL: INT8 coverage {result['int8_coverage']:.1%}")
    except Exception as e:
        print(f"  WARNING: INT8 validation failed: {e}")
```

### Updated Manifest Schema
```json
{
  "model_id": "meta-llama/Llama-3.2-1B-Instruct",
  "pte_file": "llama3.2-1b-int8-seq512.pte",
  "quantization": {
    "method": "INT8",
    "coverage": 0.92,
    "quantized_layers": ["linear", "attention.qkv"],
    "fp32_layers": ["embedding", "layernorm"]
  }
}
```

---

## References

- ExecuTorch SDK Docs: https://pytorch.org/executorch/
- PyTorch Quantization: https://pytorch.org/docs/stable/quantization.html
- INT8 Quantization Best Practices: https://arxiv.org/abs/2004.09602

---

## Action Items for Senior Engineer

1. **Immediate**: Use size-based heuristic in validation pipeline (already implemented)
2. **Next PR**: Add ExecuTorch SDK-based coverage extraction to export script
3. **CI Integration**: Add INT8 coverage gate to GitHub Actions (fail if <90%)
4. **Documentation**: Update manifest schema to include quantization metadata
