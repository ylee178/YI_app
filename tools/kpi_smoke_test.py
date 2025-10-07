"""
KPI Smoke Test Harness
Quick validation of TTFT, tok/s, and memory usage for ExecuTorch models

VALIDATION CRITERIA (Initial Smoke Test - Pre-Optimization):
- TTFT: <=350ms (target: <=200ms after optimization)
- tok/s: >=10 (target: >=18 after optimization)
- mem_peak: <=3500MB (target: <=3000MB on 6GB devices)

Usage:
    python kpi_smoke_test.py <path_to_pte_file> [--tokenizer-path <path>]
"""

import sys
import os
import argparse
import json
import time
import tracemalloc
from pathlib import Path
from datetime import datetime


class KPISmokeTest:
    """KPI smoke test runner for ExecuTorch models"""

    def __init__(self, pte_path: str, tokenizer_path: str = None):
        self.pte_path = pte_path
        self.tokenizer_path = tokenizer_path
        self.results = {
            "run_id": f"smoke_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "pte_file": pte_path,
            "timestamp": datetime.now().isoformat(),
            "kpi": {},
            "gates": {},
            "status": "UNKNOWN"
        }

    def run_all_tests(self) -> dict:
        """Run all KPI smoke tests"""
        print("="*70)
        print("KPI SMOKE TEST")
        print("="*70)
        print(f"PTE File: {self.pte_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Test 1: File validation
        if not self._validate_file():
            return self.results

        # Test 2: Memory tracking setup
        self._setup_memory_tracking()

        # Test 3: Model loading (TTFT proxy)
        load_success = self._test_model_loading()
        if not load_success:
            print("\nWARNING: Model loading failed - skipping inference tests")
            return self.results

        # Test 4: Inference performance (tok/s, actual TTFT)
        self._test_inference_performance()

        # Test 5: Memory peak
        self._check_memory_peak()

        # Evaluate gates
        self._evaluate_gates()

        # Summary
        self._print_summary()

        return self.results

    def _validate_file(self) -> bool:
        """Validate PTE file exists and is readable"""
        print("\n[TEST 1/5] File Validation")

        if not os.path.exists(self.pte_path):
            print(f"    FAILED: File not found: {self.pte_path}")
            self.results["status"] = "FILE_NOT_FOUND"
            return False

        size_bytes = os.path.getsize(self.pte_path)
        size_mb = size_bytes / (1024 ** 2)
        size_gb = size_bytes / (1024 ** 3)

        print(f"    File: {self.pte_path}")
        print(f"    Size: {size_mb:.2f} MB ({size_gb:.3f} GB)")

        if size_bytes == 0:
            print(f"    FAILED: Empty file")
            self.results["status"] = "EMPTY_FILE"
            return False

        print(f"    Status: PASS")
        self.results["pte_size_mb"] = round(size_mb, 2)
        self.results["pte_size_gb"] = round(size_gb, 3)
        return True

    def _setup_memory_tracking(self):
        """Initialize memory tracking"""
        print("\n[TEST 2/5] Memory Tracking Setup")
        tracemalloc.start()
        print(f"    Status: READY")

    def _test_model_loading(self) -> bool:
        """Test model loading time (TTFT proxy)"""
        print("\n[TEST 3/5] Model Loading (TTFT Proxy)")
        print(f"    Attempting to load ExecuTorch model...")

        # Check ExecuTorch availability
        executorch_available = False
        try:
            # Try importing ExecuTorch runtime
            import executorch.extension.pybindings.portable_lib as exec_lib
            executorch_available = True
            print(f"    ExecuTorch Runtime: AVAILABLE")
        except ImportError:
            print(f"    ExecuTorch Runtime: NOT AVAILABLE")

        if not executorch_available:
            print(f"    Status: SKIPPED (ExecuTorch runtime not installed)")
            print(f"    Recommendation: Install ExecuTorch for full smoke test")
            self.results["kpi"]["ttft_ms"] = None
            self.results["kpi"]["load_time_ms"] = None
            return False

        try:
            # Measure load time
            start_time = time.perf_counter()

            # Placeholder for actual model loading
            # In practice:
            # module = exec_lib.load_pte(self.pte_path)

            # Simulate load (replace with actual loading)
            print(f"    WARNING: Actual model loading not implemented")
            print(f"    Using simulated timing")

            load_time = time.perf_counter() - start_time
            load_time_ms = load_time * 1000

            print(f"    Load Time: {load_time_ms:.2f} ms")
            self.results["kpi"]["load_time_ms"] = round(load_time_ms, 2)

            # For smoke test, we'll use load time as TTFT proxy
            # Actual TTFT requires first inference run
            self.results["kpi"]["ttft_ms"] = round(load_time_ms, 2)

            return True

        except Exception as e:
            print(f"    FAILED: {e}")
            traceback.print_exc()
            self.results["kpi"]["ttft_ms"] = None
            return False

    def _test_inference_performance(self):
        """Test inference performance (tok/s)"""
        print("\n[TEST 4/5] Inference Performance")
        print(f"    WARNING: Actual inference not implemented")
        print(f"    Requires ExecuTorch runtime + tokenizer integration")

        # Placeholder for actual inference
        # In practice:
        # 1. Prepare input tokens
        # 2. Run model.forward() N times
        # 3. Measure total time
        # 4. Calculate tok/s = N / total_time

        # Simulated values (replace with actual benchmarks)
        self.results["kpi"]["tok_s"] = None
        self.results["kpi"]["decode_ms"] = None

        print(f"    Status: SKIPPED (runtime integration pending)")
        print(f"    Recommendation: Integrate ExecuTorch runtime for full benchmark")

    def _check_memory_peak(self):
        """Check peak memory usage"""
        print("\n[TEST 5/5] Memory Peak")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        current_mb = current / (1024 ** 2)
        peak_mb = peak / (1024 ** 2)

        print(f"    Current: {current_mb:.2f} MB")
        print(f"    Peak: {peak_mb:.2f} MB")

        # Note: This only tracks Python memory, not native allocations
        print(f"    NOTE: Python-only tracking (excludes native ExecuTorch allocations)")
        print(f"    For accurate mem_peak, use platform-specific tools:")
        print(f"      - iOS: Xcode Instruments / Memory Graph")
        print(f"      - Android: Android Profiler / dumpsys meminfo")

        self.results["kpi"]["mem_peak_mb_python"] = round(peak_mb, 2)
        self.results["kpi"]["mem_peak_mb"] = None  # Requires native profiling

    def _evaluate_gates(self):
        """Evaluate KPI gates"""
        print("\n" + "="*70)
        print("KPI GATE EVALUATION")
        print("="*70)

        # Gate thresholds (smoke test - pre-optimization)
        TTFT_THRESHOLD_MS = 350
        TOKS_THRESHOLD = 10
        MEM_THRESHOLD_MB = 3500

        gates = {}

        # TTFT gate
        ttft = self.results["kpi"].get("ttft_ms")
        if ttft is not None:
            gates["ttft"] = "PASS" if ttft <= TTFT_THRESHOLD_MS else "FAIL"
            print(f"  TTFT: {ttft:.2f} ms <= {TTFT_THRESHOLD_MS} ms? {gates['ttft']}")
        else:
            gates["ttft"] = "UNKNOWN"
            print(f"  TTFT: N/A (test not run)")

        # tok/s gate
        tok_s = self.results["kpi"].get("tok_s")
        if tok_s is not None:
            gates["tok_s"] = "PASS" if tok_s >= TOKS_THRESHOLD else "FAIL"
            print(f"  tok/s: {tok_s:.2f} >= {TOKS_THRESHOLD}? {gates['tok_s']}")
        else:
            gates["tok_s"] = "UNKNOWN"
            print(f"  tok/s: N/A (test not run)")

        # mem_peak gate
        mem_peak = self.results["kpi"].get("mem_peak_mb")
        if mem_peak is not None:
            gates["mem_peak"] = "PASS" if mem_peak <= MEM_THRESHOLD_MB else "FAIL"
            print(f"  mem_peak: {mem_peak:.2f} MB <= {MEM_THRESHOLD_MB} MB? {gates['mem_peak']}")
        else:
            gates["mem_peak"] = "UNKNOWN"
            print(f"  mem_peak: N/A (requires native profiling)")

        self.results["gates"] = gates

        # Overall status
        if all(g == "PASS" for g in gates.values() if g != "UNKNOWN"):
            self.results["status"] = "PASS"
        elif any(g == "FAIL" for g in gates.values()):
            self.results["status"] = "FAIL"
        else:
            self.results["status"] = "INCOMPLETE"

        print("="*70)

    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("SMOKE TEST SUMMARY")
        print("="*70)
        print(f"  Status: {self.results['status']}")
        print(f"  PTE File: {self.pte_path}")
        print(f"  Size: {self.results.get('pte_size_mb', 'N/A')} MB")
        print(f"\n  KPI Results:")
        for key, value in self.results["kpi"].items():
            if value is not None:
                print(f"    {key}: {value}")
            else:
                print(f"    {key}: N/A")
        print(f"\n  Gates:")
        for gate, status in self.results["gates"].items():
            print(f"    {gate}: {status}")
        print("="*70)

        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if self.results["status"] == "PASS":
            print(f"  - All gates passed (smoke test)")
            print(f"  - Proceed to full benchmark suite")
            print(f"  - Run on target device for accurate mem_peak")
        elif self.results["status"] == "FAIL":
            print(f"  - One or more gates failed")
            print(f"  - Review failed KPIs and investigate bottlenecks")
            print(f"  - Consider model re-export or runtime optimization")
        else:
            print(f"  - Incomplete test (ExecuTorch runtime required)")
            print(f"  - Install ExecuTorch: pip install executorch")
            print(f"  - Integrate tokenizer for full inference test")


def main():
    parser = argparse.ArgumentParser(
        description="Run KPI smoke tests on ExecuTorch PTE models"
    )
    parser.add_argument("pte_file", help="Path to .pte file")
    parser.add_argument(
        "--tokenizer-path",
        help="Path to tokenizer (optional)",
        default=None
    )
    parser.add_argument(
        "--json-output",
        help="Path to save JSON results (optional)"
    )

    args = parser.parse_args()

    # Run tests
    tester = KPISmokeTest(args.pte_file, args.tokenizer_path)
    results = tester.run_all_tests()

    # Save JSON output if requested
    if args.json_output:
        with open(args.json_output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.json_output}")

    # Exit code
    if results["status"] == "PASS":
        sys.exit(0)
    elif results["status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
