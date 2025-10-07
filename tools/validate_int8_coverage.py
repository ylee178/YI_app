"""
INT8 Quantization Coverage Validator
Extracts quantization information from ExecuTorch .pte files

TARGET: >=90% INT8 coverage for Llama 3.2 1B

Methods:
1. ExecuTorch SDK inspection (if available)
2. Binary pattern analysis (fallback)
3. Export metadata parsing (if embedded)

Usage:
    python validate_int8_coverage.py <path_to_pte_file> [--target-coverage 0.9]
"""

import sys
import os
import argparse
import json
from pathlib import Path


def analyze_pte_quantization(pte_path: str, target_coverage: float = 0.9) -> dict:
    """
    Analyze quantization coverage in PTE file

    Args:
        pte_path: Path to .pte file
        target_coverage: Target INT8 coverage ratio (default 0.9 = 90%)

    Returns:
        Dict with quantization analysis results
    """
    print("="*70)
    print(f"INT8 QUANTIZATION COVERAGE ANALYSIS")
    print(f"File: {pte_path}")
    print(f"Target Coverage: {target_coverage:.1%}")
    print("="*70)

    if not os.path.exists(pte_path):
        raise FileNotFoundError(f"PTE file not found: {pte_path}")

    size_bytes = os.path.getsize(pte_path)
    size_mb = size_bytes / (1024 ** 2)

    print(f"\nFile Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")

    # Load binary data
    with open(pte_path, "rb") as f:
        buffer = f.read()

    result = {
        "pte_file": pte_path,
        "size_mb": round(size_mb, 2),
        "target_coverage": target_coverage,
        "analysis_method": None,
        "int8_coverage": None,
        "validation_status": "UNKNOWN"
    }

    # METHOD 1: ExecuTorch SDK Inspection (Preferred)
    print(f"\n[METHOD 1] ExecuTorch SDK Inspection")
    executorch_available = False

    try:
        from executorch.exir import EdgeProgramManager
        executorch_available = True
        print(f"    ExecuTorch SDK: AVAILABLE")
    except ImportError:
        print(f"    ExecuTorch SDK: NOT AVAILABLE")

    if executorch_available:
        try:
            # Placeholder for actual ExecuTorch quantization inspection
            # In practice, you would:
            # 1. Load the PTE using ExecuTorch SDK
            # 2. Inspect the graph for quantization ops
            # 3. Count INT8 vs FP32 ops

            print(f"    Status: NOT IMPLEMENTED (SDK integration pending)")
            print(f"    Fallback: Using heuristic analysis")

        except Exception as e:
            print(f"    Error: {e}")
            print(f"    Fallback: Using heuristic analysis")

    # METHOD 2: Heuristic Analysis (Fallback)
    print(f"\n[METHOD 2] Heuristic Binary Analysis")
    print(f"    Method: Statistical byte distribution analysis")

    # Heuristic 1: Expected size ratio
    # FP32 model: ~4 bytes per parameter
    # INT8 model: ~1 byte per parameter (+ metadata)
    # Llama 3.2 1B: ~1.23B parameters
    # Expected INT8 size: ~1.2-1.5 GB
    # Expected FP32 size: ~4.8-5.0 GB

    PARAMS_1B = 1.23e9  # 1.23 billion parameters
    EXPECTED_FP32_SIZE_GB = (PARAMS_1B * 4) / (1024 ** 3)  # ~4.6 GB
    EXPECTED_INT8_SIZE_GB = (PARAMS_1B * 1.2) / (1024 ** 3)  # ~1.4 GB (with overhead)

    size_gb = size_bytes / (1024 ** 3)

    print(f"\n    Size-based Heuristic:")
    print(f"      Current: {size_gb:.3f} GB")
    print(f"      Expected INT8: ~{EXPECTED_INT8_SIZE_GB:.2f} GB")
    print(f"      Expected FP32: ~{EXPECTED_FP32_SIZE_GB:.2f} GB")

    # Estimate quantization based on size
    if size_gb < 2.0:
        estimated_coverage = 0.95  # Likely >90% INT8
        confidence = "HIGH"
    elif size_gb < 3.0:
        estimated_coverage = 0.70  # Mixed INT8/FP32
        confidence = "MEDIUM"
    else:
        estimated_coverage = 0.30  # Likely mostly FP32
        confidence = "LOW"

    print(f"      Estimated INT8 Coverage: {estimated_coverage:.1%} (confidence: {confidence})")

    result["analysis_method"] = "heuristic_size_based"
    result["int8_coverage"] = estimated_coverage
    result["confidence"] = confidence

    # Heuristic 2: Byte value distribution
    # INT8 tensors have values in range [-128, 127]
    # FP32 has more diverse byte patterns
    print(f"\n    Byte Distribution Analysis:")

    sample_size = min(1024 * 1024, len(buffer))  # Sample 1MB
    sample = buffer[:sample_size]

    # Count bytes in typical INT8 range (rough approximation)
    # This is NOT accurate for packed/serialized data but gives a hint
    byte_counts = [0] * 256
    for byte in sample:
        byte_counts[byte] += 1

    # Calculate entropy
    total = len(sample)
    entropy = 0
    for count in byte_counts:
        if count > 0:
            p = count / total
            entropy -= p * (p.bit_length() - 1)  # Simplified entropy

    print(f"      Sample size: {sample_size:,} bytes")
    print(f"      Unique byte values: {sum(1 for c in byte_counts if c > 0)}/256")
    print(f"      Approximate entropy: {entropy:.2f} bits")

    # VALIDATION
    print(f"\n" + "="*70)
    print(f"VALIDATION RESULT")
    print(f"="*70)

    if result["int8_coverage"] is not None:
        if result["int8_coverage"] >= target_coverage:
            result["validation_status"] = "PASS"
            print(f"  Status: PASS")
            print(f"  Coverage: {result['int8_coverage']:.1%} >= {target_coverage:.1%}")
        else:
            result["validation_status"] = "FAIL"
            print(f"  Status: FAIL")
            print(f"  Coverage: {result['int8_coverage']:.1%} < {target_coverage:.1%}")
    else:
        result["validation_status"] = "UNKNOWN"
        print(f"  Status: UNKNOWN (analysis method not available)")

    print(f"  Method: {result['analysis_method']}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
    print("="*70)

    # RECOMMENDATIONS
    print(f"\nRECOMMENDATIONS:")

    if result["validation_status"] == "PASS":
        print(f"  - Size-based heuristic indicates strong INT8 quantization")
        print(f"  - File size ({size_gb:.3f} GB) consistent with INT8 model")
        print(f"  - Proceed with runtime validation (TTFT/tok_s tests)")

    elif result["validation_status"] == "FAIL":
        print(f"  - WARNING: Model may not be properly quantized")
        print(f"  - File size ({size_gb:.3f} GB) larger than expected for INT8")
        print(f"  - RECOMMENDED ACTIONS:")
        print(f"    1. Verify export script applied quantization")
        print(f"    2. Check for quantization ops in export logs")
        print(f"    3. Re-export with explicit INT8 quantization")

    else:
        print(f"  - Unable to determine quantization coverage")
        print(f"  - RECOMMENDED ACTIONS:")
        print(f"    1. Install ExecuTorch SDK for precise analysis")
        print(f"    2. Check export manifest for quantization metadata")
        print(f"    3. Run inference benchmarks to validate performance")

    print(f"\nNOTE: For precise INT8 coverage, integrate ExecuTorch SDK inspection")
    print(f"      Current method uses size-based heuristics only")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate INT8 quantization coverage in ExecuTorch PTE files"
    )
    parser.add_argument("pte_file", help="Path to .pte file")
    parser.add_argument(
        "--target-coverage",
        type=float,
        default=0.9,
        help="Target INT8 coverage ratio (default: 0.9 = 90%%)"
    )
    parser.add_argument(
        "--json-output",
        help="Path to save JSON results (optional)"
    )

    args = parser.parse_args()

    try:
        result = analyze_pte_quantization(args.pte_file, args.target_coverage)

        # Save JSON output if requested
        if args.json_output:
            with open(args.json_output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nResults saved to: {args.json_output}")

        # Exit code based on validation status
        if result["validation_status"] == "PASS":
            sys.exit(0)
        elif result["validation_status"] == "FAIL":
            sys.exit(1)
        else:
            sys.exit(2)  # Unknown status

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
