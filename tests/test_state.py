"""Tests for tree-navigation state: visible_pages and toggle_collapse."""

from __future__ import annotations

import pytest

from zim_tui.notebook import Page
from zim_tui.state import NotebookState


def build_tree() -> list[Page]:
    """root(folder) > child1(leaf), child2(folder) > grand(leaf)."""
    root = Page(name="root", path="/nb/root.txt", dir="/nb/root", depth=0)
    child1 = Page(name="child1", path="/nb/root/child1.txt", parent=root, depth=1)
    child2 = Page(
        name="child2", path="/nb/root/child2.txt", dir="/nb/root/child2", parent=root, depth=1
    )
    grand = Page(name="grand", path="/nb/root/child2/grand.txt", parent=child2, depth=2)
    child2.children = [grand]
    root.children = [child1, child2]
    return [root, child1, child2, grand]


def make_state(pages: list[Page]) -> NotebookState:
    return NotebookState(root="/nb", pages=pages)


@pytest.mark.parametrize(
    "collapse_paths, want_names",
    [
        ([], ["root", "child1", "child2", "grand"]),
        (["/nb/root/child2.txt"], ["root", "child1", "child2"]),
        (["/nb/root.txt"], ["root"]),
        (["/nb/root.txt", "/nb/root/child2.txt"], ["root"]),
    ],
)
def test_visible_pages(collapse_paths, want_names):
    st = make_state(build_tree())
    st.collapsed = set(collapse_paths)
    assert [p.name for p in st.visible_pages()] == want_names


def test_toggle_folder_collapses_cursor_stays():
    st = make_state(build_tree())
    st.cursor = 0  # root
    st.toggle_collapse()
    assert st.pages[0].path in st.collapsed
    assert st.cursor == 0


def test_toggle_collapsed_folder_expands():
    pages = build_tree()
    st = make_state(pages)
    st.cursor = 0
    st.collapsed.add(pages[0].path)
    st.toggle_collapse()
    assert pages[0].path not in st.collapsed


def test_toggle_leaf_collapses_parent_cursor_moves():
    pages = build_tree()
    st = make_state(pages)
    st.cursor = 3  # grand (leaf under child2)
    st.toggle_collapse()
    assert pages[2].path in st.collapsed  # child2 collapsed
    vp = st.visible_pages()
    assert vp[st.cursor].name == "child2"


def test_toggle_top_level_leaf_is_noop():
    leaf = Page(name="lone", path="/nb/lone.txt", depth=0)
    st = make_state([leaf])
    st.cursor = 0
    before = len(st.collapsed)
    st.toggle_collapse()
    assert len(st.collapsed) == before
