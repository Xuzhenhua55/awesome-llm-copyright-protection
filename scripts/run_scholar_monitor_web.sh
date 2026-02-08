#!/bin/bash
#
# 启动文献查询与分析后端 API（FastAPI）
# 用法: ./run_scholar_monitor_web.sh [端口]
# 默认端口 8765；页面中 API 地址填 http://127.0.0.1:8765
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
PORT="${1:-8765}"

echo "Starting Scholar Monitor API on http://0.0.0.0:${PORT}"
echo "API 地址: http://127.0.0.1:${PORT}"
echo ""

exec python scholar_monitor_app.py "${PORT}"
