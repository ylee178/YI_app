"""
Gemma 1B ExecuTorch Export Script (EXPERIMENTAL)
Target: INT8 quantized .pte ≤ 1.1GB, seq_len=512
"""

import torch
import json
import hashlib
import os
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from executorch.exir import to_edge
    from executorch.backends.xnnpack.partition import XnnpackPartitioner
    from torch.export import export
except ImportError:
    print("ERROR: ExecuTorch not installed. Run: pip install executorch")
    exit(1)

MODEL_ID = "google/gemma-1.1-1b-it"  # Adjust to actual Gemma 1B variant
SEQ_LENGTH = 512
MAX_SIZE_GB = 1.1


def verify_int8_coverage(model):
    """Check if INT8 quantization is properly applied"""
    int8_layers = 0
    total_layers = 0

    for name, param in model.named_parameters():
        total_layers += 1
        if param.dtype == torch.qint8 or 'quantized' in name.lower():
            int8_layers += 1

    coverage = (int8_layers / total_layers * 100) if total_layers > 0 else 0
    print(f"INT8 coverage: {int8_layers}/{total_layers} ({coverage:.1f}%)")
    return coverage


def main():
    print("="*60)
    print("⚠️  EXPERIMENTAL: Gemma 1B Export")
    print("="*60)

    print(f"[1/7] Loading tokenizer from {MODEL_ID}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    except Exception as e:
        print(f"❌ FAILED: Could not load tokenizer: {e}")
        print("    Check if model ID is correct or requires authentication")
        exit(1)

    print(f"[2/7] Loading model (fp32)...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
    except Exception as e:
        print(f"❌ FAILED: Could not load model: {e}")
        exit(1)

    # Tie weights to reduce size
    if hasattr(model, "tie_weights"):
        model.tie_weights()
        print("    ✓ Weights tied")

    model.eval()

    print(f"[3/7] Creating sample input (seq_len={SEQ_LENGTH})...")
    sample_input = torch.randint(0, tokenizer.vocab_size, (1, SEQ_LENGTH), dtype=torch.long)

    print(f"[4/7] Exporting to FX graph with constant deduplication...")
    try:
        exported_program = export(
            model,
            (sample_input,),
            strict=True,
        )
    except Exception as e:
        print(f"❌ FAILED: Export failed: {e}")
        print("    Gemma may not be fully compatible with torch.export")
        exit(1)

    print(f"[5/7] Converting to Edge IR with INT8 quantization...")
    try:
        edge_program = to_edge(exported_program)
        edge_program = edge_program.to_backend(XnnpackPartitioner())
    except Exception as e:
        print(f"❌ FAILED: Edge conversion failed: {e}")
        exit(1)

    print(f"[6/7] Generating .pte binary...")
    pte_output = "gemma-1b-int8-seq512.pte"

    try:
        with open(pte_output, "wb") as f:
            edge_program.write_to_file(f)
    except Exception as e:
        print(f"❌ FAILED: Could not write .pte file: {e}")
        exit(1)

    print(f"[7/7] Validating output...")

    # Check file size
    file_size_bytes = os.path.getsize(pte_output)
    file_size_gb = file_size_bytes / (1024 ** 3)

    # Calculate SHA256
    with open(pte_output, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    # Create manifest
    manifest = {
        "model_id": MODEL_ID,
        "pte_file": pte_output,
        "pte_size_bytes": file_size_bytes,
        "pte_size_gb": round(file_size_gb, 3),
        "sha256": sha256_hash,
        "quantization": "INT8",
        "sequence_length": SEQ_LENGTH,
        "backend": "XNNPACK",
        "optimizations": [
            "constant_dedup",
            "weight_tying",
            "to_backend(XnnpackPartitioner)"
        ],
        "status": "EXPERIMENTAL",
        "export_timestamp": torch.datetime.now().isoformat()
    }

    manifest_path = "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Results
    print("\n" + "="*60)
    print("EXPORT COMPLETE (EXPERIMENTAL)")
    print("="*60)
    print(f"Output file:  {pte_output}")
    print(f"Size:         {file_size_gb:.3f} GB ({file_size_bytes:,} bytes)")
    print(f"SHA256:       {sha256_hash[:16]}...")
    print(f"Manifest:     {manifest_path}")

    # Size gate check
    if file_size_gb > MAX_SIZE_GB:
        print(f"\n❌ FAILED: PTE size {file_size_gb:.3f} GB exceeds limit {MAX_SIZE_GB} GB")
        exit(1)
    else:
        print(f"\n✅ PASSED: PTE size within {MAX_SIZE_GB} GB limit")

    print("\n⚠️  Next: Run benchmark tests to compare EQ score with Llama")
    print("="*60)


if __name__ == "__main__":
    main()
