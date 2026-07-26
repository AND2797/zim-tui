"""Search helpers: link extraction, name filtering, content grep via ripgrep.

Link resolution and navigation live in :mod:`zim_tui.state` because they depend
on tree/cursor state.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .notebook import Page


@dataclass
class LinkItem:
    display: str
    target: str  # raw Zim link target (may use ":" separators)


@dataclass
class SearchResult:
    page_index: int  # index into the flat pages list
    display: str


def extract_links(content: str) -> list[LinkItem]:
    """Parse ``[[...]]`` links, skipping external http(s) links, deduped by target."""
    items: list[LinkItem] = []
    seen: set[str] = set()
    s = content
    while True:
        start = s.find("[[")
        if start < 0:
            break
        s = s[start + 2 :]
        end = s.find("]]")
        if end < 0:
            break
        inner = s[:end].strip()
        s = s[end + 2 :]
        pipe = inner.find("|")
        if pipe >= 0:
            target = inner[:pipe].strip()
            display = inner[pipe + 1 :].strip()
        else:
            target = inner
            display = inner
        if target.startswith("http://") or target.startswith("https://"):
            continue
        if target and target not in seen:
            seen.add(target)
            items.append(LinkItem(display=display, target=target))
    return items


def page_breadcrumb(page: Page) -> str:
    """Ancestor names root→page joined with ' > '."""
    parts = [page.name]
    cur = page.parent
    while cur is not None:
        parts.insert(0, cur.name)
        cur = cur.parent
    return " > ".join(parts)


def filter_pages_by_name(query: str, pages: list[Page]) -> list[SearchResult]:
    """Pages whose breadcrumb contains ``query`` (case-insensitive). Empty → all."""
    q = query.lower()
    out: list[SearchResult] = []
    for i, page in enumerate(pages):
        crumb = page_breadcrumb(page)
        if q == "" or q in crumb.lower():
            out.append(SearchResult(page_index=i, display=crumb))
    return out


def run_content_search(query: str, pages: list[Page], root: str) -> list[SearchResult]:
    """Grep page content with ripgrep. At most 5 matches per file, 100 total.

    Runs synchronously (the caller drives it from a worker thread). Invokes
    ``rg --line-number --no-heading --color=never --smart-case --max-count=5 --
    <query> <root>``.
    """
    if query.strip() == "":
        return []

    path_to_idx = {p.path: i for i, p in enumerate(pages)}
    try:
        proc = subprocess.run(
            [
                "rg",
                "--line-number",
                "--no-heading",
                "--color=never",
                "--smart-case",
                "--max-count=5",
                "--",
                query,
                root,
            ],
            capture_output=True,
            text=True,
        )
        raw = proc.stdout
    except OSError:
        return []

    results: list[SearchResult] = []
    for line in raw.strip().split("\n"):
        if line == "":
            continue
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        abs_path = parts[0]
        if not Path(abs_path).is_absolute():
            abs_path = str(Path(root) / abs_path)
        idx = path_to_idx.get(abs_path)
        if idx is None:
            continue
        line_num = parts[1]
        snippet = parts[2].strip()
        if len(snippet) > 55:
            snippet = snippet[:55] + "…"
        display = f"{page_breadcrumb(pages[idx])} :{line_num}  {snippet}"
        results.append(SearchResult(page_index=idx, display=display))
        if len(results) >= 100:
            break
    return results
