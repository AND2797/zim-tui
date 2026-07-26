"""Headless smoke tests: the app boots, navigates, and opens each modal."""

from __future__ import annotations

from pathlib import Path

import pytest

from zim_tui import notebook
from zim_tui.app import ZimApp

DEMO = Path(__file__).resolve().parent.parent / "demo-notebook"


def make_app() -> ZimApp:
    nb = notebook.load(str(DEMO))
    return ZimApp(nb, [str(DEMO)])


@pytest.mark.asyncio
async def test_boot_and_navigate():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.state.current_page() is not None
        # move down the tree
        await pilot.press("j")
        await pilot.press("j")
        assert app.state.cursor == 2
        # move back up
        await pilot.press("k")
        assert app.state.cursor == 1
        # collapse/expand a folder (cursor 0 is a top-level page)
        await pilot.press("g")  # top
        assert app.state.cursor == 0
        # panel switching
        await pilot.press("3")
        assert app.focus_name() == "preview"
        await pilot.press("2")
        assert app.focus_name() == "tree"
        await pilot.press("1")
        assert app.focus_name() == "notebooks"


@pytest.mark.asyncio
async def test_collapse_expand():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # navigate to a folder page (Notes has children)
        names = [p.name for p in app.state.pages]
        notes_idx = names.index("Notes")
        app.state.cursor = app.state.visible_pages().index(app.state.pages[notes_idx])
        await pilot.press("space")  # collapse Notes
        assert app.state.pages[notes_idx].path in app.state.collapsed
        await pilot.press("space")  # expand
        assert app.state.pages[notes_idx].path not in app.state.collapsed


@pytest.mark.asyncio
async def test_help_modal_opens_and_closes():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "HelpModal"
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen.__class__.__name__ != "HelpModal"


@pytest.mark.asyncio
async def test_search_modal_name():
    app = make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("slash")  # open name search
        await pilot.pause()
        assert app.screen.__class__.__name__ == "SearchModal"
        for ch in "meeting":
            await pilot.press(ch)
        await pilot.pause()
        # results should include Meeting_Notes
        assert any("Meeting_Notes" in r.display for r in app.screen.results)
        await pilot.press("enter")
        await pilot.pause()
        assert app.state.current_page().name == "Meeting_Notes"
