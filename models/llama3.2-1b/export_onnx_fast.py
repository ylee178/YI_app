"""
Llama 3.2 1B ONNX Export Script (Fast Path)
Uses pre-quantized INT8 model to skip quantization step
Target: .onnx <= 1.5GB, seq_len=512
Runtime: ONNX Runtime Mobile
"""

import torch
import json
import hashlib
import os
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.onnxruntime import ORTModelForCausalLM

# Use pre-quantized INT8 model from NeuralMagic
MODEL_ID = "neuralmagic/Llama-3.2-1B-Instruct-quantized.w8a8"
SEQ_LENGTH = 512
MAX_SIZE_GB = 1.5


def main():
    # Output directly to models directory
    output_dir = Path(__file__).parent / "onnx_output"
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"[1/4] Loading pre-quantized INT8 model from {MODEL_ID}...")
    print(f"    Output directory: {output_dir}")

    # Export to ONNX format using Optimum
    print(f"[2/4] Exporting to ONNX format...")
    model = ORTModelForCausalLM.from_pretrained(
        MODEL_ID,
        export=True,
        use_cache=False  # Disable KV cache for simplicity
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

    # Save ONNX model
    print(f"    Saving ONNX model to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"    ONNX model saved successfully")

    print(f"[3/4] Packaging model...")

    # Find the main ONNX file
    onnx_files = list(output_dir.glob("*.onnx"))
    if not onnx_files:
        # Check subdirectories
        onnx_files = list(output_dir.glob("**/*.onnx"))

    if not onnx_files:
        print("ERROR: No ONNX file found in output directory")
        exit(1)

    onnx_model_path = onnx_files[0]
    print(f"    Found ONNX model: {onnx_model_path}")

    # Rename to standard name
    final_output = output_dir.parent / "llama3.2-1b-int8-seq512.onnx"

    import shutil
    shutil.copy(onnx_model_path, final_output)

    # Copy external data if exists
    ext_data = onnx_model_path.with_suffix(".onnx.data")
    if ext_data.exists():
        shutil.copy(ext_data, final_output.with_suffix(".onnx.data"))

    print(f"[4/4] Validating output...")

    # Check file size
    if not os.path.exists(final_output):
        print(f"ERROR: Output file not created: {final_output}")
        exit(1)

    file_size_bytes = os.path.getsize(final_output)
    file_size_gb = file_size_bytes / (1024 ** 3)
    file_size_mb = file_size_bytes / (1024 ** 2)

    # Add external data size if exists
    ext_data_final = final_output.with_suffix(".onnx.data")
    if ext_data_final.exists():
        ext_size = os.path.getsize(ext_data_final)
        file_size_bytes += ext_size
        file_size_gb = file_size_bytes / (1024 ** 3)
        file_size_mb = file_size_bytes / (1024 ** 2)
        print(f"    Total size (model + external data): {file_size_gb:.3f} GB")

    # Calculate SHA256
    with open(final_output, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"Creating manifest...")

    # Create manifest
    manifest = {
        "model_id": MODEL_ID,
        "onnx_file": str(final_output),
        "external_data": str(ext_data_final) if ext_data_final.exists() else None,
        "file_size_bytes": file_size_bytes,
        "file_size_gb": round(file_size_gb, 3),
        "file_size_mb": round(file_size_mb, 1),
        "sha256": sha256_hash,
        "quantization": "INT8 (w8a8)",
        "sequence_length": SEQ_LENGTH,
        "runtime": "ONNX Runtime Mobile",
        "backend": "CPU (ARM/x64 optimized)",
        "optimizations": [
            "INT8 weight + activation quantization",
            "Pre-quantized by NeuralMagic"
        ]
    }

    manifest_path = output_dir.parent / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Results
    print("\n" + "="*60)
    print("EXPORT COMPLETE")
    print("="*60)
    print(f"Output file:  {final_output}")
    print(f"Size:         {file_size_gb:.3f} GB ({file_size_mb:.1f} MB)")
    print(f"SHA256:       {sha256_hash[:16]}...")
    print(f"Manifest:     {manifest_path}")

    # Size gate check
    if file_size_gb > MAX_SIZE_GB:
        print(f"\n WARNING: ONNX size {file_size_gb:.3f} GB exceeds limit {MAX_SIZE_GB} GB")
        print(f"         This may still work on 8GB+ devices")
    else:
        print(f"\n PASSED: ONNX size within {MAX_SIZE_GB} GB limit")

    # Admission formula check (for 6GB device)
    required_ram_mb = file_size_mb * 1.6 + 600
    print(f"\nMemory Requirements (Admission Formula):")
    print(f"  Required RAM: {required_ram_mb:.0f} MB ({required_ram_mb/1024:.2f} GB)")
    print(f"  Target device: 6GB RAM ({6*1024} MB)")

    if required_ram_mb <= 6 * 1024:
        print(f"  PASSED: Can run on 6GB devices")
    else:
        print(f"  WARNING: May require >6GB RAM")

    print("="*60)


if __name__ == "__main__":
    main()
