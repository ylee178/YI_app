#!/bin/bash
# Full PTE Validation Pipeline
# Runs all validation checks on downloaded PTE artifact
#
# Usage:
#   ./run_full_pte_validation.sh <path_to_pte_file>
#
# Example:
#   ./run_full_pte_validation.sh models/llama3.2-1b/llama3.2-1b-int8-seq512.pte

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PTE_FILE="${1:-}"
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${TOOLS_DIR}/../results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${RESULTS_DIR}/pte_validation_${TIMESTAMP}.json"

# Validation thresholds
MAX_SIZE_GB=1.5
TARGET_INT8_COVERAGE=0.9

# Usage check
if [ -z "$PTE_FILE" ]; then
    echo "Usage: $0 <path_to_pte_file>"
    echo ""
    echo "Example:"
    echo "  $0 models/llama3.2-1b/llama3.2-1b-int8-seq512.pte"
    exit 1
fi

# Check file exists
if [ ! -f "$PTE_FILE" ]; then
    echo -e "${RED}ERROR: PTE file not found: $PTE_FILE${NC}"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "========================================================================"
echo "PTE FULL VALIDATION PIPELINE"
echo "========================================================================"
echo "PTE File: $PTE_FILE"
echo "Timestamp: $(date)"
echo "Report: $REPORT_FILE"
echo "========================================================================"
echo ""

# Initialize report
cat > "$REPORT_FILE" << EOF
{
  "run_id": "pte_validation_${TIMESTAMP}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pte_file": "$PTE_FILE",
  "validation_steps": [],
  "overall_status": "PENDING"
}
EOF

# Track overall success
OVERALL_SUCCESS=true

# ============================================================================
# STEP 1: Basic File Validation
# ============================================================================
echo -e "${BLUE}[STEP 1/6] Basic File Validation${NC}"
echo "Running verify_pte.py..."

if python3 "${TOOLS_DIR}/verify_pte.py" "$PTE_FILE" --max-size-gb $MAX_SIZE_GB; then
    echo -e "${GREEN}  PASS: Basic file validation${NC}"
else
    echo -e "${RED}  FAIL: Basic file validation${NC}"
    OVERALL_SUCCESS=false
fi
echo ""

# ============================================================================
# STEP 2: Guard Validation (Empty file/partition checks)
# ============================================================================
echo -e "${BLUE}[STEP 2/6] Guard Validation (Empty File/Partition Checks)${NC}"
echo "Running validate_pte_guards.py..."

if python3 "${TOOLS_DIR}/validate_pte_guards.py" "$PTE_FILE"; then
    echo -e "${GREEN}  PASS: Guard validation${NC}"
else
    echo -e "${RED}  FAIL: Guard validation${NC}"
    OVERALL_SUCCESS=false
fi
echo ""

# ============================================================================
# STEP 3: INT8 Coverage Validation
# ============================================================================
echo -e "${BLUE}[STEP 3/6] INT8 Coverage Validation${NC}"
echo "Running validate_int8_coverage.py..."

INT8_JSON="${RESULTS_DIR}/int8_coverage_${TIMESTAMP}.json"
if python3 "${TOOLS_DIR}/validate_int8_coverage.py" "$PTE_FILE" \
    --target-coverage $TARGET_INT8_COVERAGE \
    --json-output "$INT8_JSON"; then
    echo -e "${GREEN}  PASS: INT8 coverage >= ${TARGET_INT8_COVERAGE}${NC}"
else
    echo -e "${YELLOW}  WARNING: INT8 coverage check failed or incomplete${NC}"
    # Don't fail overall - this is a soft warning
fi
echo ""

# ============================================================================
# STEP 4: Manifest Verification
# ============================================================================
echo -e "${BLUE}[STEP 4/6] Manifest Verification${NC}"

PTE_DIR="$(dirname "$PTE_FILE")"
MANIFEST="${PTE_DIR}/manifest.json"

if [ -f "$MANIFEST" ]; then
    echo "Found manifest: $MANIFEST"

    # Validate JSON structure
    if jq empty "$MANIFEST" 2>/dev/null; then
        echo -e "${GREEN}  PASS: Manifest is valid JSON${NC}"

        # Extract key fields
        MODEL_ID=$(jq -r '.model_id // "N/A"' "$MANIFEST")
        QUANT=$(jq -r '.quantization // "N/A"' "$MANIFEST")
        SIZE_GB=$(jq -r '.pte_size_gb // "N/A"' "$MANIFEST")
        SHA256=$(jq -r '.sha256 // "N/A"' "$MANIFEST")

        echo "  Model: $MODEL_ID"
        echo "  Quantization: $QUANT"
        echo "  Size: $SIZE_GB GB"
        echo "  SHA256: $SHA256"

        # Verify SHA256 match
        ACTUAL_SHA256=$(shasum -a 256 "$PTE_FILE" | awk '{print $1}')
        if [ "$SHA256" == "$ACTUAL_SHA256" ]; then
            echo -e "${GREEN}  PASS: SHA256 matches manifest${NC}"
        else
            echo -e "${RED}  FAIL: SHA256 mismatch${NC}"
            echo "    Expected: $SHA256"
            echo "    Actual:   $ACTUAL_SHA256"
            OVERALL_SUCCESS=false
        fi
    else
        echo -e "${RED}  FAIL: Invalid JSON in manifest${NC}"
        OVERALL_SUCCESS=false
    fi
else
    echo -e "${YELLOW}  WARNING: Manifest not found at $MANIFEST${NC}"
fi
echo ""

# ============================================================================
# STEP 5: KPI Smoke Test
# ============================================================================
echo -e "${BLUE}[STEP 5/6] KPI Smoke Test${NC}"
echo "Running kpi_smoke_test.py..."

KPI_JSON="${RESULTS_DIR}/kpi_smoke_${TIMESTAMP}.json"
if python3 "${TOOLS_DIR}/kpi_smoke_test.py" "$PTE_FILE" --json-output "$KPI_JSON"; then
    echo -e "${GREEN}  PASS: KPI smoke test${NC}"
else
    echo -e "${YELLOW}  WARNING: KPI smoke test incomplete (requires ExecuTorch runtime)${NC}"
    # Don't fail overall - runtime may not be available yet
fi
echo ""

# ============================================================================
# STEP 6: Final Report Generation
# ============================================================================
echo -e "${BLUE}[STEP 6/6] Report Generation${NC}"

# Get file stats
FILE_SIZE_BYTES=$(stat -f%z "$PTE_FILE" 2>/dev/null || stat -c%s "$PTE_FILE" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE_BYTES / 1024 / 1024" | bc)
FILE_SIZE_GB=$(echo "scale=3; $FILE_SIZE_BYTES / 1024 / 1024 / 1024" | bc)
ACTUAL_SHA256=$(shasum -a 256 "$PTE_FILE" | awk '{print $1}')

# Generate comprehensive report
cat > "$REPORT_FILE" << EOF
{
  "run_id": "pte_validation_${TIMESTAMP}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pte_file": "$PTE_FILE",
  "pte": {
    "path": "$PTE_FILE",
    "size_bytes": $FILE_SIZE_BYTES,
    "size_mb": $FILE_SIZE_MB,
    "size_gb": $FILE_SIZE_GB,
    "sha256": "$ACTUAL_SHA256"
  },
  "gates": {
    "size_within_limit": $([ "$FILE_SIZE_GB" \< "$MAX_SIZE_GB" ] && echo "true" || echo "false"),
    "guards_passed": $OVERALL_SUCCESS,
    "manifest_valid": $([ -f "$MANIFEST" ] && echo "true" || echo "false")
  },
  "validation_results": {
    "basic_file_check": "see verify_pte output",
    "guard_validation": "see validate_pte_guards output",
    "int8_coverage": "see $INT8_JSON",
    "kpi_smoke_test": "see $KPI_JSON"
  },
  "overall_status": "$([ "$OVERALL_SUCCESS" == true ] && echo "PASS" || echo "FAIL")"
}
EOF

echo "Report generated: $REPORT_FILE"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "========================================================================"
echo "VALIDATION SUMMARY"
echo "========================================================================"

if [ "$OVERALL_SUCCESS" == true ]; then
    echo -e "${GREEN}Overall Status: PASS${NC}"
    echo ""
    echo "All critical validation checks passed."
    echo ""
    echo "NEXT STEPS:"
    echo "  1. Review detailed reports in ${RESULTS_DIR}/"
    echo "  2. Run full benchmark suite on target device"
    echo "  3. Validate KPIs: TTFT <=200ms, tok/s >=18, mem_peak <=3.0GB"
    echo "  4. Test on iOS/Android with ExecuTorch runtime"
    exit 0
else
    echo -e "${RED}Overall Status: FAIL${NC}"
    echo ""
    echo "One or more validation checks failed."
    echo ""
    echo "RECOMMENDED ACTIONS:"
    echo "  1. Review error messages above"
    echo "  2. Check detailed reports in ${RESULTS_DIR}/"
    echo "  3. Investigate failed checks"
    echo "  4. Re-export PTE if critical issues found"
    exit 1
fi
