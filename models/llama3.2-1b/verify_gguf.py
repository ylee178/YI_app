"""
GGUF Model Verification Script
Validates model file and generates manifest
"""

import json
import hashlib
import os
from pathlib import Path

MODEL_FILE = "Llama-3.2-1B-Instruct-Q8_0.gguf"
MAX_SIZE_GB = 1.5


def main():
    model_path = Path(__file__).parent / MODEL_FILE

    if not model_path.exists():
        print(f"ERROR: Model file not found: {model_path}")
        exit(1)

    print(f"[1/3] Checking model size...")

    file_size_bytes = os.path.getsize(model_path)
    file_size_gb = file_size_bytes / (1024 ** 3)
    file_size_mb = file_size_bytes / (1024 ** 2)

    print(f"    Size: {file_size_gb:.3f} GB ({file_size_mb:.1f} MB)")

    print(f"[2/3] Calculating SHA256...")

    sha256_hash = hashlib.sha256()
    with open(model_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096*1024), b""):
            sha256_hash.update(chunk)

    sha256 = sha256_hash.hexdigest()
    print(f"    SHA256: {sha256[:16]}...")

    print(f"[3/3] Creating manifest...")

    # Create manifest
    manifest = {
        "model_id": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "model_file": str(model_path),
        "quantization": "Q8_0",
        "file_size_bytes": file_size_bytes,
        "file_size_gb": round(file_size_gb, 3),
        "file_size_mb": round(file_size_mb, 1),
        "sha256": sha256,
        "runtime": "llama.cpp",
        "backend": "CPU (ARM/x64 optimized)",
        "sequence_length": 512,
        "format": "GGUF",
        "optimizations": [
            "Q8_0 quantization (8-bit)",
            "Native GGUF format",
            "llama.cpp optimized"
        ]
    }

    manifest_path = model_path.parent / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Results
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print(f"Model file:   {model_path}")
    print(f"Size:         {file_size_gb:.3f} GB ({file_size_mb:.1f} MB)")
    print(f"SHA256:       {sha256[:16]}...")
    print(f"Manifest:     {manifest_path}")

    # Size gate check
    if file_size_gb > MAX_SIZE_GB:
        print(f"\n WARNING: Model size {file_size_gb:.3f} GB exceeds limit {MAX_SIZE_GB} GB")
        print(f"          This may still work on 8GB+ devices")
    else:
        print(f"\n PASSED: Model size within {MAX_SIZE_GB} GB limit")

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
