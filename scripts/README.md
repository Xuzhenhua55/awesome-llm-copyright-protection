# Scripts Usage

## Installation

```bash
cd scripts
pip install -r requirements.txt
```

## Usage

### Semantic Scholar Citation Monitor (`run_scholar_monitor.sh`)

```bash
# Default settings
./run_scholar_monitor.sh

# Options
./run_scholar_monitor.sh --api-base URL
./run_scholar_monitor.sh --host HOST
./run_scholar_monitor.sh --port PORT
./run_scholar_monitor.sh --max-papers N
./run_scholar_monitor.sh --max-citations N
./run_scholar_monitor.sh --skip-search
./run_scholar_monitor.sh --skip-analysis
```

### Scholar Citation Monitor Web UI

Web 页面：在站点中打开 `docs/html/scholar-monitor.html`。可先启动后端 API，再在页面中按流程操作（种子论文 → 查找引用 → 分析），或直接「加载已有结果」JSON 分页查看与导出。

```bash
# 启动后端 API（默认端口 8765）
./run_scholar_monitor_web.sh
# 或指定端口
./run_scholar_monitor_web.sh 8766
```

在页面中设置「API 地址」为 `http://127.0.0.1:8765`，然后：从项目页面抽取或手动添加种子论文 → 点击「查找引用」→ 设置并发数后点击「开始分析」。分析结果在下方分页展示，可导出 JSON。也可直接选择本地的 `scholar_relevant_*.json` / `all_citations_*.json` 加载后分页展示与导出。

### Using Python Directly

```bash
python scholar_citation_monitor.py --max-papers 10 --max-citations 50
```
