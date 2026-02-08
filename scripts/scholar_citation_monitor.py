#!/usr/bin/env python3
"""
Semantic Scholar Citation Monitor for LLM Copyright Protection Research

This script:
1. Extracts existing papers from the website HTML files
2. Searches Semantic Scholar for papers that cite these papers
3. Deduplicates and analyzes each citing paper
4. Logs relevant papers with classification suggestions

Usage:
    python scholar_citation_monitor.py [--api-base API_BASE]
"""

import os
import sys
import json
import re
import argparse
import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Deque, Tuple, Set, Callable

import pytz
import requests

from paper_analysis import (
    CATEGORIES,
    GenerationConfig,
    DEFAULT_GENERATION_CONFIG,
    OpenAIClientWrapper,
    analyze_paper as analyze_paper_shared,
)

# ============================================================================
# Configuration
# ============================================================================

# Default API settings
DEFAULT_API_BASE = "http://127.0.0.1:8000/v1"
DEFAULT_API_KEY = "EMPTY"

# Semantic Scholar API
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
DEFAULT_S2_API_KEY = os.environ.get("S2_API_KEY")  # optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
HTML_DIR = PROJECT_ROOT / "docs" / "html"
LOG_DIR = SCRIPT_DIR / "logs"
PAPER_LOG_DIR = SCRIPT_DIR / "paper_logs"
CACHE_DIR = SCRIPT_DIR / "cache"

# Timezone for Beijing
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

# Rate limiting (seconds between requests) - Semantic Scholar allows 100 req/5min
# Using 5 seconds to be safe
REQUEST_DELAY = 5.0

# Paper-level retry (when request failures happen repeatedly)
MAX_PAPER_RETRIES = 10

# HTML files containing paper references
HTML_FILES = [
    "invasive.html",
    "non-invasive.html",
    "fingerprint-transfer.html",
    "fingerprint-detection-remove.html",
]





# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging():
    """Setup logging configuration."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = LOG_DIR / f"scholar_monitor_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# Extract Papers from Website
# ============================================================================

def extract_papers_from_html(html_path: Path) -> List[Dict[str, Any]]:
    """Extract paper information from an HTML file.
    
    Note: Papers wrapped in /* */ comments are excluded (commented out papers).
    """
    papers = []
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove multi-line comments (/* ... */) to exclude commented-out papers
        content_without_comments = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Extract paper titles and links using regex
        paper_pattern = r'\{\s*title:\s*["\']([^"\']+)["\'].*?link:\s*["\']([^"\']+)["\']'
        
        matches = re.findall(paper_pattern, content_without_comments, re.DOTALL)
        
        for title, link in matches:
            title = title.replace('\\\'', "'").strip()
            
            paper = {
                "title": title,
                "url": link,
                "source_file": html_path.name,
            }
            
            # Extract arxiv ID if present
            arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', link)
            if arxiv_match:
                paper["arxiv_id"] = arxiv_match.group(1)
            
            papers.append(paper)
            
    except Exception as e:
        logger.error(f"Error parsing {html_path}: {e}")
    
    return papers


def extract_all_existing_papers() -> List[Dict[str, Any]]:
    """Extract all papers from the website HTML files."""
    all_papers = []
    seen_titles = set()
    
    for html_file in HTML_FILES:
        html_path = HTML_DIR / html_file
        if html_path.exists():
            logger.info(f"Extracting papers from {html_file}...")
            papers = extract_papers_from_html(html_path)
            
            for paper in papers:
                title_lower = paper["title"].lower()
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    all_papers.append(paper)
            
            logger.info(f"  Found {len(papers)} papers in {html_file}")
        else:
            logger.warning(f"HTML file not found: {html_path}")
    
    logger.info(f"Total unique existing papers: {len(all_papers)}")
    return all_papers


# ============================================================================
# Semantic Scholar API Functions
# ============================================================================

MAX_RETRIES = 10
RETRY_DELAY = 3.0  # Seconds to wait before retry (Semantic Scholar API)


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


class SemanticScholarClient:
    """Thin Semantic Scholar Graph API client with retries."""

    def __init__(
        self,
        *,
        base_url: str = SEMANTIC_SCHOLAR_API,
        api_key: Optional[str] = DEFAULT_S2_API_KEY,
        request_delay_s: float = REQUEST_DELAY,
        max_retries: int = MAX_RETRIES,
        retry_delay_s: float = RETRY_DELAY,
        timeout_s: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.request_delay_s = float(request_delay_s)
        self.max_retries = int(max_retries)
        self.retry_delay_s = float(retry_delay_s)
        self.timeout_s = float(timeout_s)

        self.session = requests.Session()
        self.headers: Dict[str, str] = {
            "User-Agent": "awesome-llm-copyright-protection/semantic-scholar-monitor",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def _request_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout_s)

                # Rate limiting (429)
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait_s = float(retry_after) if retry_after and str(retry_after).isdigit() else self.retry_delay_s
                    logger.warning(f"[429] Rate limited. Sleep {wait_s:.1f}s then retry {attempt}/{self.max_retries}.")
                    time.sleep(wait_s)
                    continue

                # Server errors (5xx)
                if resp.status_code >= 500:
                    logger.warning(f"[{resp.status_code}] Server error. Sleep {self.retry_delay_s:.1f}s then retry {attempt}/{self.max_retries}.")
                    time.sleep(self.retry_delay_s)
                    continue

                resp.raise_for_status()
                return resp.json()

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                logger.warning(f"Request failed ({type(e).__name__}). Sleep {self.retry_delay_s:.1f}s then retry {attempt}/{self.max_retries}.")
                time.sleep(self.retry_delay_s)
                continue
            except requests.exceptions.RequestException as e:
                last_exc = e
                logger.warning(f"Request error: {e}. Sleep {self.retry_delay_s:.1f}s then retry {attempt}/{self.max_retries}.")
                time.sleep(self.retry_delay_s)
                continue

        raise RuntimeError(f"Semantic Scholar request failed after {self.max_retries} retries: {url}") from last_exc

    def search_paper_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        data = self._request_json(
            "/paper/search",
            {
                "query": title,
                "limit": 1,
                "fields": "paperId,title,authors,year,abstract,citationCount,url",
            },
        )
        items = data.get("data") or []
        return items[0] if items else None

    def get_citations(self, paper_id: str, limit: int) -> List[Dict[str, Any]]:
        data = self._request_json(
            f"/paper/{paper_id}/citations",
            {
                "limit": limit,
                "fields": "paperId,title,authors,year,abstract,venue,url,citationCount",
            },
        )
        out: List[Dict[str, Any]] = []
        for item in data.get("data", []):
            citing_paper = (item or {}).get("citingPaper") or {}
            if citing_paper.get("title"):
                out.append(citing_paper)
        return out


def search_citations_for_paper(
    s2: SemanticScholarClient,
    paper: Dict[str, Any],
    max_citations: int = 50,
) -> Tuple[List[Dict[str, Any]], str]:
    """Search Semantic Scholar for papers that cite the given paper."""
    citations = []
    title = paper["title"]
    
    logger.info(f"Searching citations for: {title[:50]}...")
    
    # First, find the paper on Semantic Scholar
    ss_paper = s2.search_paper_by_title(title)
    time.sleep(s2.request_delay_s)

    if ss_paper is None:
        logger.warning("  Seed paper not found on Semantic Scholar")
        return citations, "not_found"
    
    paper_id = ss_paper.get("paperId")
    citation_count = ss_paper.get("citationCount", 0)
    logger.info(f"  Found paper (ID: {paper_id}, Citations: {citation_count})")

    time.sleep(s2.request_delay_s)
    raw_citations = s2.get_citations(paper_id, limit=max_citations)
    
    for citing_paper in raw_citations:
        # Format authors
        authors = citing_paper.get("authors", [])
        author_names = ", ".join([a.get("name", "") for a in authors[:5]])
        if len(authors) > 5:
            author_names += " et al."
        
        citation = {
            "title": citing_paper.get("title", ""),
            "authors": author_names,
            "year": citing_paper.get("year", ""),
            "venue": citing_paper.get("venue", ""),
            "abstract": citing_paper.get("abstract", ""),
            "url": citing_paper.get("url", ""),
            "semantic_scholar_id": citing_paper.get("paperId", ""),
            "citation_count": citing_paper.get("citationCount", 0),
            "cited_paper": title,
        }
        citations.append(citation)
    
    logger.info(f"  Retrieved {len(citations)} citations")
    time.sleep(s2.request_delay_s)
    return citations, "ok"


def collect_all_citations(
    existing_papers: List[Dict[str, Any]],
    max_citations_per_paper: int = 50,
    max_papers_to_check: int = None,
    s2_api_key: Optional[str] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    """Collect citations for all existing papers. Optional progress_callback(event_dict)."""
    all_citations = []
    seen_keys: Set[str] = set()

    s2 = SemanticScholarClient(api_key=s2_api_key or DEFAULT_S2_API_KEY)
    
    # Add existing paper titles to seen set
    for paper in existing_papers:
        seen_keys.add(f"title:{_normalize_title(paper['title'])}")
    
    papers_to_check = existing_papers
    if max_papers_to_check:
        papers_to_check = existing_papers[:max_papers_to_check]

    # Queue-based processing: if request failures happen, requeue and retry up to MAX_PAPER_RETRIES.
    queue: Deque[Tuple[Dict[str, Any], int]] = deque((p, 0) for p in papers_to_check)
    total = len(papers_to_check)
    attempts = 0
    completed = 0

    while queue:
        paper, tries = queue.popleft()
        attempts += 1
        logger.info(f"[{attempts}/{total}] Processing: {paper['title'][:50]}... (try {tries + 1}/{MAX_PAPER_RETRIES})")

        try:
            citations, status = search_citations_for_paper(s2, paper, max_citations=max_citations_per_paper)
        except RuntimeError as e:
            # Request failed even after internal retries -> requeue paper-level up to 10 times
            if tries + 1 < MAX_PAPER_RETRIES:
                logger.warning(f"Request failed for seed, requeueing: {e}")
                if progress_callback:
                    progress_callback({
                        "type": "paper",
                        "action": "retry",
                        "title": paper["title"],
                        "attempt": tries + 1,
                        "max_retries": MAX_PAPER_RETRIES,
                        "attempts": attempts,
                        "completed": completed,
                        "total": total,
                        "reason": str(e),
                    })
                queue.append((paper, tries + 1))
                time.sleep(RETRY_DELAY)
                continue
            logger.error(f"Seed failed after {MAX_PAPER_RETRIES} attempts, skipping: {paper['title'][:80]}")
            completed += 1
            if progress_callback:
                progress_callback({
                    "type": "paper",
                    "action": "failed",
                    "title": paper["title"],
                    "attempt": tries + 1,
                    "max_retries": MAX_PAPER_RETRIES,
                    "attempts": attempts,
                    "completed": completed,
                    "total": total,
                    "count": len(all_citations),
                    "reason": str(e),
                })
                progress_callback({
                    "type": "progress",
                    "processed": completed,
                    "total": total,
                    "title": paper["title"],
                    "count": len(all_citations),
                })
            continue

        if status == "not_found":
            completed += 1
            if progress_callback:
                progress_callback({
                    "type": "paper",
                    "action": "not_found",
                    "title": paper["title"],
                    "attempt": tries + 1,
                    "max_retries": MAX_PAPER_RETRIES,
                    "attempts": attempts,
                    "completed": completed,
                    "total": total,
                    "count": len(all_citations),
                })
                progress_callback({
                    "type": "progress",
                    "processed": completed,
                    "total": total,
                    "title": paper["title"],
                    "count": len(all_citations),
                })
            continue

        added_this_round = 0
        for citation in citations:
            ssid = citation.get("semantic_scholar_id") or ""
            if ssid:
                key = f"s2:{ssid}"
            else:
                key = f"title:{_normalize_title(citation.get('title', ''))}"
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_citations.append(citation)
                added_this_round += 1

        completed += 1
        if progress_callback:
            progress_callback({
                "type": "paper",
                "action": "success",
                "title": paper["title"],
                "attempt": tries + 1,
                "max_retries": MAX_PAPER_RETRIES,
                "attempts": attempts,
                "completed": completed,
                "total": total,
                "added": added_this_round,  # 本种子新加入的篇数（去重后）
                "count": len(all_citations),
            })
            progress_callback({
                "type": "progress",
                "processed": completed,
                "total": total,
                "title": paper["title"],
                "count": len(all_citations),
            })
    
    logger.info(f"Total unique new citations found: {len(all_citations)}")
    return all_citations


# ============================================================================
# Paper Analysis
# ============================================================================

def analyze_paper(client: OpenAIClientWrapper, paper: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a paper using the LLM API."""
    return analyze_paper_shared(client, paper, include_extra_fields=True)


# ============================================================================
# Save Results
# ============================================================================

def save_results(papers: List[Dict[str, Any]], date_str: str):
    """Save analysis results."""
    PAPER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    relevant = [p for p in papers if p.get("analysis", {}).get("is_model_copyright_protection", False)]
    
    # Save all citations JSON
    all_json_file = PAPER_LOG_DIR / f"all_citations_{date_str}.json"
    with open(all_json_file, 'w', encoding='utf-8') as f:
        json.dump({"total": len(papers), "papers": papers}, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved all {len(papers)} citations to {all_json_file}")
    
    # Save relevant JSON
    json_file = PAPER_LOG_DIR / f"scholar_relevant_{date_str}.json"
    output = {
        "date": date_str,
        "total_citations_found": len(papers),
        "relevant_papers_count": len(relevant),
        "papers": relevant,
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved {len(relevant)} relevant papers to {json_file}")
    
    # Save Markdown summary
    md_file = PAPER_LOG_DIR / f"scholar_summary_{date_str}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Semantic Scholar Citation Monitor - {date_str}\n\n")
        f.write(f"**Total citations found:** {len(papers)}\n")
        f.write(f"**Relevant papers:** {len(relevant)}\n\n")
        f.write("---\n\n")
        
        for i, paper in enumerate(relevant, 1):
            analysis = paper.get("analysis", {})
            f.write(f"## {i}. {paper['title']}\n\n")
            f.write(f"- **Year:** {paper.get('year', 'N/A')}\n")
            f.write(f"- **Authors:** {paper.get('authors', 'N/A')}\n")
            f.write(f"- **Venue:** {paper.get('venue', 'N/A')}\n")
            f.write(f"- **Cited paper:** {paper.get('cited_paper', 'N/A')}\n")
            f.write(f"- **Category:** {analysis.get('category')}/{analysis.get('subcategory')}\n")
            f.write(f"- **Confidence:** {analysis.get('classification_confidence', 'N/A')}\n")
            f.write(f"- **Summary:** {analysis.get('brief_summary', 'N/A')}\n\n")
            if paper.get('abstract'):
                abstract = paper['abstract']
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                f.write(f"**Abstract:** {abstract}\n\n")
            f.write(f"**Reasoning:** {analysis.get('reasoning', 'N/A')}\n\n")
            f.write("---\n\n")
    
    logger.info(f"Saved summary to {md_file}")


# ============================================================================
# Cache Functions
# ============================================================================

def load_cache() -> Dict[str, Any]:
    """Load cached data."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "scholar_cache.json"
    
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"analyzed_titles": [], "citations": []}


def save_cache(cache: Dict[str, Any]):
    """Save cache data."""
    cache_file = CACHE_DIR / "scholar_cache.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Monitor Semantic Scholar citations")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="LLM API base URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="LLM API key")
    parser.add_argument("--model", default=None, help="Model name (e.g., gpt-4, gpt-5.2). If not specified, uses first available model")
    parser.add_argument("--s2-api-key", default=DEFAULT_S2_API_KEY, help="Semantic Scholar API key (optional; can also set env S2_API_KEY)")
    parser.add_argument("--max-papers", type=int, default=10, help="Max existing papers to check")
    parser.add_argument("--max-citations", type=int, default=50, help="Max citations per paper")
    parser.add_argument("--skip-search", action="store_true", help="Skip search, use cache")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip LLM analysis")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Starting Semantic Scholar Citation Monitor...")
    logger.info("=" * 60)
    
    date_str = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    
    # Step 1: Extract existing papers
    logger.info("Step 1: Extracting existing papers from website...")
    existing_papers = extract_all_existing_papers()
    
    if not existing_papers:
        logger.error("No existing papers found!")
        return
    
    # Step 2: Search citations
    if args.skip_search:
        logger.info("Step 2: Loading citations from cache...")
        cache = load_cache()
        citations = cache.get("citations", [])
    else:
        logger.info("Step 2: Searching Semantic Scholar for citations...")
        citations = collect_all_citations(
            existing_papers,
            max_citations_per_paper=args.max_citations,
            max_papers_to_check=args.max_papers,
            s2_api_key=args.s2_api_key,
        )
        
        # Cache results
        cache = load_cache()
        cache["citations"] = citations
        save_cache(cache)
    
    if not citations:
        logger.info("No new citations found.")
        return
    
    # Step 3: Analyze with LLM
    if args.skip_analysis:
        logger.info("Step 3: Skipping LLM analysis...")
    else:
        logger.info("Step 3: Analyzing citations with LLM...")
        client = OpenAIClientWrapper(
            api_base=args.api_base,
            api_key=args.api_key,
            model_name=args.model,
        )
        
        for i, paper in enumerate(citations, 1):
            logger.info(f"Analyzing [{i}/{len(citations)}]: {paper['title'][:50]}...")
            analysis = analyze_paper(client, paper)
            paper["analysis"] = analysis
            
            if analysis.get("is_model_copyright_protection"):
                logger.info(f"  -> RELEVANT: {analysis.get('category')}/{analysis.get('subcategory')}")
            else:
                logger.info(f"  -> Not relevant")
    
    # Step 4: Save results
    logger.info("Step 4: Saving results...")
    save_results(citations, date_str)
    
    logger.info("=" * 60)
    logger.info("Job completed.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
