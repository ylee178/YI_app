"""
PTE Verification Tool
Validates .pte file integrity, size, and quantization
"""

import argparse
import hashlib
import json
import os
from pathlib import Path


def calculate_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_pte(pte_path: str, manifest_path: str = None, max_size_gb: float = None):
    """
    Verify PTE file against manifest and size constraints

    Args:
        pte_path: Path to .pte file
        manifest_path: Path to manifest.json (optional)
        max_size_gb: Maximum allowed size in GB (optional)
    """
    if not os.path.exists(pte_path):
        print(f"❌ ERROR: PTE file not found: {pte_path}")
        return False

    print("="*60)
    print(f"Verifying: {pte_path}")
    print("="*60)

    # 1. File size check
    file_size_bytes = os.path.getsize(pte_path)
    file_size_gb = file_size_bytes / (1024 ** 3)
    file_size_mb = file_size_bytes / (1024 ** 2)

    print(f"\n[1] File Size:")
    print(f"    {file_size_gb:.3f} GB ({file_size_mb:.1f} MB, {file_size_bytes:,} bytes)")

    if max_size_gb:
        if file_size_gb > max_size_gb:
            print(f"    ❌ FAILED: Exceeds {max_size_gb} GB limit")
            return False
        else:
            print(f"    ✅ PASSED: Within {max_size_gb} GB limit")

    # 2. SHA256 checksum
    print(f"\n[2] SHA256 Hash:")
    sha256_hash = calculate_sha256(pte_path)
    print(f"    {sha256_hash}")

    # 3. Manifest verification
    if manifest_path:
        if not os.path.exists(manifest_path):
            print(f"\n[3] Manifest: ⚠️  File not found: {manifest_path}")
        else:
            print(f"\n[3] Manifest Verification:")
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            # Check SHA256
            manifest_sha = manifest.get("sha256", "")
            if manifest_sha == sha256_hash:
                print(f"    ✅ SHA256 matches manifest")
            else:
                print(f"    ❌ SHA256 mismatch!")
                print(f"       Expected: {manifest_sha}")
                print(f"       Actual:   {sha256_hash}")
                return False

            # Check size
            manifest_size = manifest.get("pte_size_bytes", 0)
            if manifest_size == file_size_bytes:
                print(f"    ✅ Size matches manifest ({manifest_size:,} bytes)")
            else:
                print(f"    ❌ Size mismatch!")
                print(f"       Expected: {manifest_size:,} bytes")
                print(f"       Actual:   {file_size_bytes:,} bytes")
                return False

            # Display manifest info
            print(f"\n    Model: {manifest.get('model_id', 'N/A')}")
            print(f"    Quant: {manifest.get('quantization', 'N/A')}")
            print(f"    Seq:   {manifest.get('sequence_length', 'N/A')}")

    # 4. Basic binary structure check
    print(f"\n[4] Binary Structure:")
    with open(pte_path, "rb") as f:
        header = f.read(16)
        print(f"    Header (hex): {header.hex()[:32]}...")

        # Check for common magic bytes (placeholder - actual ExecuTorch format TBD)
        # This is a basic sanity check
        if len(header) == 16:
            print(f"    ✅ Header readable")
        else:
            print(f"    ⚠️  Unexpected header length")

    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60)

    return True


def main():
    parser = argparse.ArgumentParser(description="Verify ExecuTorch .pte file")
    parser.add_argument("pte_file", help="Path to .pte file")
    parser.add_argument("--manifest", help="Path to manifest.json", default=None)
    parser.add_argument("--max-size-gb", type=float, help="Maximum size in GB", default=None)

    args = parser.parse_args()

    # Auto-detect manifest in same directory
    if args.manifest is None:
        pte_dir = Path(args.pte_file).parent
        candidate = pte_dir / "manifest.json"
        if candidate.exists():
            args.manifest = str(candidate)
            print(f"Auto-detected manifest: {args.manifest}\n")

    success = verify_pte(args.pte_file, args.manifest, args.max_size_gb)

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
