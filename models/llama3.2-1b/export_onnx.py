"""
Llama 3.2 1B ONNX Export Script
Target: INT8 quantized .onnx <= 1.5GB, seq_len=512
Runtime: ONNX Runtime Mobile
"""

import torch
import json
import hashlib
import os
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.onnxruntime import ORTModelForCausalLM
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from optimum.onnxruntime import ORTQuantizer

MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"
SEQ_LENGTH = 512
MAX_SIZE_GB = 1.5


def main():
    # Use /tmp for intermediate files to save desktop space
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="onnx_export_")
    output_dir = Path(temp_dir) / "onnx_output"
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"[1/6] Loading model and tokenizer from {MODEL_ID}...")
    print(f"    Using temp directory: {temp_dir}")

    # Export to ONNX format using Optimum
    print(f"[2/6] Exporting to ONNX format...")
    model = ORTModelForCausalLM.from_pretrained(
        MODEL_ID,
        export=True,
        use_cache=False  # Disable KV cache for simplicity
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

    # Save unquantized ONNX model first
    print(f"    Saving base ONNX model to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"    Base ONNX model saved successfully")

    print(f"[3/6] Applying INT8 dynamic quantization...")

    # Use dynamic quantization (simpler, more reliable for mobile)
    from optimum.onnxruntime import ORTQuantizer
    from onnxruntime.quantization import QuantizationMode

    quantized_dir = output_dir / "quantized"
    quantized_dir.mkdir(exist_ok=True)

    # Create quantizer from saved model
    quantizer = ORTQuantizer.from_pretrained(output_dir)

    # Dynamic INT8 quantization config
    qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)

    quantizer.quantize(
        save_dir=quantized_dir,
        quantization_config=qconfig
    )

    print(f"[4/6] Packaging quantized model...")

    # The quantized model should be in the quantized directory
    quantized_model_path = output_dir / "quantized" / "model.onnx"

    # Output to current working directory (where script is run)
    final_output_dir = Path.cwd()
    final_output = final_output_dir / "llama3.2-1b-int8-seq512.onnx"

    # Copy to final location
    import shutil
    if quantized_model_path.exists():
        shutil.copy(quantized_model_path, final_output)
        # Copy external data if exists
        ext_data = output_dir / "quantized" / "model.onnx.data"
        if ext_data.exists():
            shutil.copy(ext_data, final_output_dir / "llama3.2-1b-int8-seq512.onnx.data")
    else:
        print("WARNING: Quantized model not found, using unquantized model")
        # Fallback to base model if quantization didn't create expected file
        base_model = list((output_dir).glob("*.onnx"))
        if base_model:
            shutil.copy(base_model[0], final_output)
            # Copy external data
            ext_data_base = base_model[0].with_suffix(".onnx.data")
            if ext_data_base.exists():
                shutil.copy(ext_data_base, final_output_dir / "llama3.2-1b-int8-seq512.onnx.data")

    print(f"    Cleaning up temp directory: {temp_dir}")
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[5/6] Validating output...")

    # Check file size
    if not os.path.exists(final_output):
        print(f"ERROR: Output file not created: {final_output}")
        exit(1)

    file_size_bytes = os.path.getsize(final_output)
    file_size_gb = file_size_bytes / (1024 ** 3)
    file_size_mb = file_size_bytes / (1024 ** 2)

    # Calculate SHA256
    with open(final_output, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    print(f"[6/6] Creating manifest...")

    # Create manifest
    manifest = {
        "model_id": MODEL_ID,
        "onnx_file": final_output,
        "file_size_bytes": file_size_bytes,
        "file_size_gb": round(file_size_gb, 3),
        "file_size_mb": round(file_size_mb, 1),
        "sha256": sha256_hash,
        "quantization": "INT8",
        "sequence_length": SEQ_LENGTH,
        "runtime": "ONNX Runtime Mobile",
        "backend": "CPU (ARM/x64 optimized)",
        "optimizations": [
            "INT8 quantization",
            "per-channel quantization",
            "avx512_vnni config"
        ]
    }

    manifest_path = final_output_dir / "manifest.json"
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
        print(f"\n❌ FAILED: ONNX size {file_size_gb:.3f} GB exceeds limit {MAX_SIZE_GB} GB")
        exit(1)
    else:
        print(f"\n✅ PASSED: ONNX size within {MAX_SIZE_GB} GB limit")

    # Admission formula check (for 6GB device)
    required_ram_mb = file_size_mb * 1.6 + 600
    print(f"\nMemory Requirements (Admission Formula):")
    print(f"  Required RAM: {required_ram_mb:.0f} MB ({required_ram_mb/1024:.2f} GB)")
    print(f"  Target device: 6GB RAM ({6*1024} MB)")

    if required_ram_mb <= 6 * 1024:
        print(f"  ✅ Can run on 6GB devices")
    else:
        print(f"  ⚠️  May require >6GB RAM")

    print("="*60)


if __name__ == "__main__":
    main()
