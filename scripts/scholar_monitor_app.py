#!/usr/bin/env python3
"""
FastAPI backend for Scholar Citation Monitor Web UI.

Endpoints:
- GET/POST seed papers (extract from project, add manual, list)
- POST find-citations (run Semantic Scholar citation search)
- POST analyze (run LLM analysis with configurable concurrency)
- GET paper-logs list (optional: list available JSON files)
"""

import os
import re
import json
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional


def _normalize_title(title: str) -> str:
    """Normalize title for seed-match (trim, lower, collapse spaces)."""
    return re.sub(r"\s+", " ", (title or "").strip().lower())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Import from existing monitor (run from scripts/ so parent is project root)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in __import__("sys").path:
    import sys
    sys.path.insert(0, str(SCRIPT_DIR))

from scholar_citation_monitor import (
    extract_all_existing_papers,
    collect_all_citations,
    analyze_paper,
)
from paper_analysis import OpenAIClientWrapper

# Paths
PAPER_LOG_DIR = SCRIPT_DIR / "paper_logs"

app = FastAPI(title="Scholar Citation Monitor API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state (per process)
state: Dict[str, Any] = {
    "seed_papers": [],
    "citations": [],
    "analyzed_papers": [],
}


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class SeedPaperAdd(BaseModel):
    title: str
    url: str = ""


class SeedPapersSet(BaseModel):
    papers: List[Dict[str, Any]] = Field(default_factory=list)


class FindCitationsRequest(BaseModel):
    seed_papers: Optional[List[Dict[str, Any]]] = None  # use state if None
    max_papers_to_check: Optional[int] = None
    max_citations_per_paper: int = 50


class AnalyzeRequest(BaseModel):
    citations: Optional[List[Dict[str, Any]]] = None  # use state citations if None
    concurrency: int = 4
    api_base: str = "http://127.0.0.1:8000/v1"
    api_key: str = "EMPTY"
    model: Optional[str] = None


# ---------------------------------------------------------------------------
# Seed papers
# ---------------------------------------------------------------------------

@app.get("/api/seed-papers")
def get_seed_papers():
    return {"papers": state["seed_papers"]}


@app.post("/api/seed-papers/extract")
def extract_seed_papers():
    """Extract papers from project HTML files and set as seed papers."""
    try:
        papers = extract_all_existing_papers()
        state["seed_papers"] = papers
        return {"papers": papers, "count": len(papers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seed-papers/add")
def add_seed_paper(body: SeedPaperAdd):
    paper = {"title": body.title.strip(), "url": body.url.strip()}
    if paper["title"]:
        state["seed_papers"].append(paper)
    return {"papers": state["seed_papers"], "count": len(state["seed_papers"])}


@app.post("/api/seed-papers/set")
def set_seed_papers(body: SeedPapersSet):
    state["seed_papers"] = list(body.papers) if body.papers else []
    return {"papers": state["seed_papers"], "count": len(state["seed_papers"])}


@app.post("/api/seed-papers/remove")
def remove_seed_paper(index: int):
    if 0 <= index < len(state["seed_papers"]):
        state["seed_papers"].pop(index)
    return {"papers": state["seed_papers"], "count": len(state["seed_papers"])}


# ---------------------------------------------------------------------------
# Find citations
# ---------------------------------------------------------------------------

@app.post("/api/citations/find")
def find_citations(req: FindCitationsRequest):
    seed = req.seed_papers if req.seed_papers is not None else state["seed_papers"]
    if not seed:
        raise HTTPException(status_code=400, detail="No seed papers. Extract or add seeds first.")
    try:
        citations = collect_all_citations(
            seed,
            max_citations_per_paper=req.max_citations_per_paper,
            max_papers_to_check=req.max_papers_to_check,
        )
        state["citations"] = citations
        return {"citations": citations, "count": len(citations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/citations/find/stream")
def find_citations_stream(req: FindCitationsRequest):
    """Stream progress via Server-Sent Events, then return final citations."""
    seed = req.seed_papers if req.seed_papers is not None else state["seed_papers"]
    if not seed:
        raise HTTPException(status_code=400, detail="No seed papers. Extract or add seeds first.")

    progress_queue: queue.Queue = queue.Queue()
    total_to_check = min(len(seed), req.max_papers_to_check) if req.max_papers_to_check else len(seed)

    def run_find():
        try:
            result = collect_all_citations(
                seed,
                max_citations_per_paper=req.max_citations_per_paper,
                max_papers_to_check=req.max_papers_to_check,
                progress_callback=lambda event: progress_queue.put(event),
            )
            progress_queue.put({"type": "done", "citations": result})
        except Exception as e:
            progress_queue.put({"type": "error", "detail": str(e)})

    def event_stream():
        # 立即发送 started，让前端马上收到数据，避免“正在连接”后无数据导致界面消失或卡住
        yield f"data: {json.dumps({'type': 'started', 'total': total_to_check}, ensure_ascii=False)}\n\n"
        thread = threading.Thread(target=run_find)
        thread.start()
        while True:
            try:
                msg = progress_queue.get(timeout=300)
            except queue.Empty:
                continue
            if msg["type"] == "done":
                state["citations"] = msg["citations"]
                yield f"data: {json.dumps({'type': 'done', 'count': len(msg['citations']), 'citations': msg['citations']}, ensure_ascii=False)}\n\n"
                break
            if msg["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'detail': msg['detail']}, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Analyze (with concurrency)
# ---------------------------------------------------------------------------

# 已在种子中的论文不调用 LLM，直接标记「已在种子中，跳过分析」
SKIP_ANALYSIS_SEED = {
    "is_model_copyright_protection": False,
    "reasoning": "已在种子中，跳过分析",
    "category": None,
    "subcategory": None,
    "classification_confidence": None,
    "brief_summary": "已在种子中，跳过分析",
}


@app.post("/api/analyze")
def run_analyze(req: AnalyzeRequest):
    papers = req.citations if req.citations is not None else state["citations"]
    if not papers:
        raise HTTPException(status_code=400, detail="No citations to analyze. Run find-citations first.")
    seed_titles = {_normalize_title(p.get("title", "")) for p in state["seed_papers"]}
    # 已在种子中的论文不提交给模型，直接标记跳过
    results_by_index: Dict[int, Dict[str, Any]] = {}
    for i, p in enumerate(papers):
        if _normalize_title(p.get("title", "")) in seed_titles:
            paper = dict(p)
            paper["analysis"] = dict(SKIP_ANALYSIS_SEED)
            results_by_index[i] = paper
    to_analyze = [(i, p) for i, p in enumerate(papers) if i not in results_by_index]
    concurrency = max(1, min(req.concurrency, 16))
    client = OpenAIClientWrapper(
        api_base=req.api_base,
        api_key=req.api_key,
        model_name=req.model,
    )
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_i = {executor.submit(analyze_paper, client, p): i for i, p in to_analyze}
        for future in as_completed(future_to_i):
            i = future_to_i[future]
            try:
                analysis = future.result()
                paper = dict(papers[i])
                paper["analysis"] = analysis
                results_by_index[i] = paper
            except Exception as e:
                paper = dict(papers[i])
                paper["analysis"] = {
                    "is_model_copyright_protection": False,
                    "reasoning": str(e),
                    "category": None,
                    "subcategory": None,
                    "classification_confidence": "low",
                    "brief_summary": "Analysis failed",
                }
                results_by_index[i] = paper
    # Restore order
    analyzed = [results_by_index[i] for i in range(len(papers))]
    state["analyzed_papers"] = analyzed
    return {"papers": analyzed, "count": len(analyzed)}


# ---------------------------------------------------------------------------
# Paper logs (list available JSON files)
# ---------------------------------------------------------------------------

@app.get("/api/paper-logs/list")
def list_paper_logs():
    """List scholar_relevant_*.json and all_citations_*.json in paper_logs."""
    if not PAPER_LOG_DIR.exists():
        return {"files": []}
    files = []
    for f in PAPER_LOG_DIR.iterdir():
        if f.suffix == ".json" and f.name.startswith(("scholar_relevant_", "all_citations_")):
            files.append({"name": f.name, "path": str(f)})
    files.sort(key=lambda x: x["name"], reverse=True)
    return {"files": files}


@app.get("/api/paper-logs/{filename}")
def get_paper_log(filename: str):
    """Return content of a paper log JSON file."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = PAPER_LOG_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 启动后端
# 命令: python scholar_monitor_app.py [端口]
# 示例: python scholar_monitor_app.py        # 默认 8765
#       python scholar_monitor_app.py 8766   # 指定端口
# 或:   uvicorn scholar_monitor_app:app --host 0.0.0.0 --port 8765
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import uvicorn
    port = 8765
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    uvicorn.run(app, host="0.0.0.0", port=port)
