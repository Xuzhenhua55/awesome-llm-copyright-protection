#!/bin/bash
#
# Run the Semantic Scholar Citation Monitor
# Usage: ./run_scholar_monitor.sh [OPTIONS]
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/scholar_citation_monitor.py"
LOG_DIR="${SCRIPT_DIR}/logs"

# Default settings
API_HOST="127.0.0.1"
API_PORT="8000"
API_KEY="EMPTY"
API_BASE=""
MODEL=""
MAX_PAPERS=10
MAX_CITATIONS=50
SKIP_SEARCH=""
SKIP_ANALYSIS=""

# Create log directory
mkdir -p "${LOG_DIR}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-base)
            API_BASE="$2"
            shift 2
            ;;
        --host)
            API_HOST="$2"
            shift 2
            ;;
        --port)
            API_PORT="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --max-papers)
            MAX_PAPERS="$2"
            shift 2
            ;;
        --max-citations)
            MAX_CITATIONS="$2"
            shift 2
            ;;
        --skip-search)
            SKIP_SEARCH="--skip-search"
            shift
            ;;
        --skip-analysis)
            SKIP_ANALYSIS="--skip-analysis"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --api-base URL      Full LLM API base URL"
            echo "  --api-key KEY       LLM API key"
            echo "  --model NAME        Model name (e.g., gpt-4, gpt-5.2)"
            echo "  --host HOST         LLM API host (default: 127.0.0.1)"
            echo "  --port PORT         LLM API port (default: 8000)"
            echo "  --max-papers N      Max existing papers to check (default: 10)"
            echo "  --max-citations N   Max citations per paper (default: 50)"
            echo "  --skip-search       Skip Semantic Scholar search, use cached data"
            echo "  --skip-analysis     Skip LLM analysis"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build API base URL
if [[ -z "${API_BASE}" ]]; then
    API_BASE="http://${API_HOST}:${API_PORT}/v1"
fi

# Check script exists
if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
    echo "Error: Script not found at ${PYTHON_SCRIPT}"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_LOG="${LOG_DIR}/scholar_run_${TIMESTAMP}.log"

echo "=============================================="
echo "Semantic Scholar Citation Monitor"
echo "=============================================="
echo "Time: $(date)"
echo "LLM API: ${API_BASE}"
echo "Max papers to check: ${MAX_PAPERS}"
echo "Max citations per paper: ${MAX_CITATIONS}"
echo "Log file: ${RUN_LOG}"
echo "=============================================="

python "${PYTHON_SCRIPT}" \
    --api-base "${API_BASE}" \
    --api-key "${API_KEY}" \
    ${MODEL:+--model "${MODEL}"} \
    --max-papers "${MAX_PAPERS}" \
    --max-citations "${MAX_CITATIONS}" \
    ${SKIP_SEARCH} \
    ${SKIP_ANALYSIS} \
    2>&1 | tee "${RUN_LOG}"

echo ""
echo "Done. Check logs at: ${LOG_DIR}"
