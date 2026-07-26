"""Tests for link extraction, name filtering, link resolution, and rg search."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from zim_tui import notebook, search
from zim_tui.state import NotebookState

DEMO = Path(__file__).resolve().parent.parent / "demo-notebook"


def test_extract_links():
    content = (
        "See [[Tasks:Active]] and [[target|display label]].\n"
        "External [[https://example.com]] is skipped.\n"
        "Duplicate [[Tasks:Active]] appears once."
    )
    links = search.extract_links(content)
    targets = [l.target for l in links]
    assert targets == ["Tasks:Active", "target"]  # external skipped, dupe deduped
    assert links[1].display == "display label"


def test_page_breadcrumb():
    nb = notebook.load(str(DEMO))
    by_name = {p.name: p for p in nb.pages}
    assert search.page_breadcrumb(by_name["Meeting_Notes"]) == "Notes > Meeting_Notes"


def test_filter_pages_by_name():
    nb = notebook.load(str(DEMO))
    all_results = search.filter_pages_by_name("", nb.pages)
    assert len(all_results) == len(nb.pages)  # empty query returns all

    meeting = search.filter_pages_by_name("meeting", nb.pages)
    assert any("Meeting_Notes" in r.display for r in meeting)


def test_resolve_link_absolute():
    nb = notebook.load(str(DEMO))
    st = NotebookState(root=str(DEMO), pages=nb.pages)
    idx = st.resolve_link_index("Tasks:Active")
    assert idx >= 0
    assert nb.pages[idx].name == "Active"


def test_resolve_link_loose_name_with_space():
    nb = notebook.load(str(DEMO))
    st = NotebookState(root=str(DEMO), pages=nb.pages)
    # "Meeting Notes" (space) must resolve to Meeting_Notes.txt on disk
    idx = st.resolve_link_index("Meeting Notes")
    assert idx >= 0
    assert nb.pages[idx].name == "Meeting_Notes"


def test_resolve_link_missing():
    nb = notebook.load(str(DEMO))
    st = NotebookState(root=str(DEMO), pages=nb.pages)
    assert st.resolve_link_index("Nonexistent:Page") == -1


@pytest.mark.skipif(shutil.which("rg") is None, reason="ripgrep not installed")
def test_run_content_search():
    nb = notebook.load(str(DEMO))
    results = search.run_content_search("Tasks", nb.pages, str(DEMO))
    assert len(results) >= 1
    assert all(0 <= r.page_index < len(nb.pages) for r in results)


def test_run_content_search_empty_query():
    nb = notebook.load(str(DEMO))
    assert search.run_content_search("   ", nb.pages, str(DEMO)) == []
