# GitHub Actions Export Guide

## Problem Statement

**Local Export Failure**: Memory constraints on development machine (RAM insufficient for FP32 model + IR buffers + export overhead).

**Symptom**: `export_pte.py` exits with code 0 but produces empty (0-byte) `.pte` file.

**Root Cause**:
1. FP32 Llama 3.2 1B (~4.5GB) + IR graph generation requires ~5-6GB peak RAM
2. Local machine has insufficient free RAM
3. Silent failure: ExecuTorch `to_edge()` returns empty buffer when partitioning fails

## Solution: GitHub Actions Export

**Environment**: Ubuntu runner with 16-32GB RAM (sufficient for export)

**Timeline**: ~25-30 minutes total
- ExecuTorch install: 5-10 min
- Model download: 2-3 min
- Export execution: 15-20 min

**Artifacts**: `.pte` file + `manifest.json` + export logs

---

## Implementation

### Files Added

1. **`.github/workflows/export-llama-pte.yml`**
   - GitHub Actions workflow definition
   - Installs ExecuTorch, runs export, validates output
   - Uploads artifact on success

2. **`models/llama3.2-1b/export_pte.py`** (updated)
   - Added memory guards:
     - `torch.set_grad_enabled(False)` - disable gradients globally
     - Smaller example input (128 tokens) for export
     - Edge IR buffer validation (catches empty .pte)
     - Partition count verification

3. **`setup_gha_export.sh`**
   - Interactive setup script
   - Initializes git, configures secrets, triggers workflow

4. **`docs/gha_export_guide.md`**
   - This documentation file

---

## Usage

### First-Time Setup

```bash
cd /Users/uxersean/Desktop/YI_Clean

# Run interactive setup
./setup_gha_export.sh
```

**Setup script will:**
1. Initialize git repository (if needed)
2. Prompt for GitHub remote configuration
3. Configure `HF_TOKEN` secret (from `~/.cache/huggingface/token`)
4. Commit workflow files
5. Push to GitHub
6. Trigger export workflow

### Manual Setup (if script fails)

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit: YI project"

# 2. Create GitHub repo
gh repo create YI --private --source=. --push

# 3. Configure HF_TOKEN secret
gh secret set HF_TOKEN < ~/.cache/huggingface/token

# 4. Commit workflow
git add .github/workflows/export-llama-pte.yml
git add models/llama3.2-1b/export_pte.py
git commit -m "Add GHA export workflow"
git push

# 5. Trigger workflow
gh workflow run export-llama-pte.yml
```

---

## Monitoring

### Watch live progress

```bash
gh run watch
```

### View workflow logs

```bash
gh run list --workflow=export-llama-pte.yml
gh run view <RUN_ID> --log
```

### Check status

```bash
gh run list --limit 5
```

---

## Download Artifact

### After workflow completes

```bash
# List recent runs
gh run list --workflow=export-llama-pte.yml

# Download artifact
gh run download <RUN_ID> --name llama3.2-1b-pte-<SHA>
```

**Artifact contains:**
- `llama3.2-1b-int8-seq512.pte` - Model file (target: ≤1.5GB)
- `manifest.json` - Metadata (size, SHA256, timestamps)
- `export_pte_log.txt` - Full export logs

### Move to project directory

```bash
cd /Users/uxersean/Desktop/YI_Clean

# Create models directory if needed
mkdir -p models/llama3.2-1b

# Move downloaded files
mv ~/Downloads/llama3.2-1b-pte-*/*.pte models/llama3.2-1b/
mv ~/Downloads/llama3.2-1b-pte-*/manifest.json models/llama3.2-1b/
```

---

## Validation Checklist

After download, verify:

```bash
cd models/llama3.2-1b

# 1. File exists
ls -lh *.pte

# 2. Size check (must be ≤1.5GB)
SIZE_GB=$(stat -f%z *.pte | awk '{print $1/1024/1024/1024}')
echo "Size: ${SIZE_GB} GB"

# 3. SHA256 integrity
shasum -a 256 *.pte

# 4. Manifest validation
cat manifest.json | jq '.prd_compliant, .runtime, .pte_size_gb'

# Expected output:
# true
# "ExecuTorch"
# <value ≤ 1.5>
```

---

## Memory Guards Explained

### Guard 1: Disable Gradients Globally

```python
torch.set_grad_enabled(False)
```

**Why**: Prevents PyTorch from allocating gradient buffers during export. Saves ~1-2GB RAM.

### Guard 2: Smaller Example Input

```python
EXPORT_SEQ = 128  # Instead of 512
sample_input = torch.randint(0, vocab_size, (1, 128))
```

**Why**: Reduces IR graph size during export. Final `.pte` is sequence-agnostic, so this doesn't affect runtime capabilities.

### Guard 3: Edge IR Buffer Validation

```python
edge_buffer = edge_program.buffer()
if len(edge_buffer) == 0:
    raise RuntimeError("Empty Edge IR buffer - export failed")
```

**Why**: Catches silent failures. ExecuTorch may return exit code 0 even when partitioning fails (e.g., unsupported ops, OOM during lowering).

### Guard 4: Partition Count Check

```python
num_methods = len(edge_program.exported_program().graph_module.graph.nodes)
if num_methods == 0:
    raise RuntimeError("No executable methods in Edge IR")
```

**Why**: Verifies at least one executable partition was generated. Zero partitions = unusable `.pte`.

---

## Troubleshooting

### Issue: Workflow fails during ExecuTorch install

**Solution**: Check PyTorch compatibility. ExecuTorch requires PyTorch 2.1-2.4.

```yaml
# In workflow, pin PyTorch version:
pip install torch==2.4.0 torchvision==0.19.0
```

### Issue: HF_TOKEN authentication fails

**Symptoms**: 401 Unauthorized when downloading model

**Solution**:
1. Generate new HF token: https://huggingface.co/settings/tokens
2. Update secret: `gh secret set HF_TOKEN`

### Issue: Empty .pte file on GitHub Actions

**Diagnosis**: Check workflow logs for guard failures

```bash
gh run view <RUN_ID> --log | grep "GUARD\|ERROR\|Empty"
```

**Likely causes**:
- Unsupported ops in model graph
- ExecuTorch version mismatch
- Insufficient runner memory (should not happen on ubuntu-latest)

**Solution**: Check export logs, open issue on ExecuTorch repo if needed.

### Issue: File size exceeds 1.5GB

**Solution**: Apply additional quantization

```python
# In export_pte.py, add:
from torch.ao.quantization import quantize_dynamic

model = quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)
```

---

## Next Steps After Export

Once `.pte` file is validated:

1. **Copy to React Native app**:
   ```bash
   mkdir -p /path/to/YI_App/assets/models
   cp models/llama3.2-1b/*.pte /path/to/YI_App/assets/models/
   ```

2. **Implement native iOS module**:
   - Load `.pte` using ExecuTorch C++ runtime
   - Implement admission logic (`free_ram >= pte_size * 1.6 + 600`)
   - Bridge inference to React Native

3. **Run local benchmark**:
   ```bash
   python tools/benchmark_pte.py models/llama3.2-1b/*.pte
   ```

4. **Verify KPI gates**:
   - TTFT: ≤200ms (flagship), ≤350ms (mid-range)
   - Decode: ≥18 tok/s (flagship), ≥12 tok/s (mid-range)
   - Memory: ≤3.0GB peak (Safe preset)

---

## KPI Gate Reference

| Metric | Target | Measurement |
|--------|--------|-------------|
| **EQ Score** | ≥85/100 | Blind 20-turn eval with rubric |
| **TTFT** | ≤200ms (flagship), ≤350ms (mid-range) | First token latency |
| **Decode Speed** | ≥18 tok/s (flagship), ≥12 tok/s (mid-range) | Tokens per second |
| **Memory Peak** | ≤3.0GB | Safe preset, 10-min session |
| **Crash Rate** | 0 | 10-min continuous session |
| **Memory Leak** | None | 20+ turn session |

---

## References

- **ExecuTorch docs**: https://pytorch.org/executorch/
- **Llama 3.2 model card**: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
- **PRD**: `/Users/uxersean/Desktop/YI_Clean/PRD.md`
- **Admission logic**: `/Users/uxersean/Desktop/YI_Clean/docs/admission_formula.md`
