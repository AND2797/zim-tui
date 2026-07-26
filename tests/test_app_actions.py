"""Action-level tests driven through the Textual Pilot against a temp notebook."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from zim_tui import notebook
from zim_tui.app import ZimApp

DEMO = Path(__file__).resolve().parent.parent / "demo-notebook"


@pytest.fixture
def temp_notebook(tmp_path):
    dest = tmp_path / "nb"
    shutil.copytree(DEMO, dest)
    return dest


def make_app(root: Path) -> ZimApp:
    nb = notebook.load(str(root))
    return ZimApp(nb, [str(root)])


async def _type(pilot, text: str) -> None:
    for ch in text:
        await pilot.press(ch)


@pytest.mark.asyncio
async def test_new_page(temp_notebook):
    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        await _type(pilot, "My New Page")
        await pilot.press("enter")
        await pilot.pause()
        assert (temp_notebook / "My_New_Page.txt").exists()
        assert any(p.name == "My_New_Page" for p in app.state.pages)


@pytest.mark.asyncio
async def test_delete_page(temp_notebook):
    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        # move cursor onto a deletable leaf: "Research" under Notes
        names = [p.name for p in app.state.visible_pages()]
        app.state.cursor = names.index("Research")
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
        assert not (temp_notebook / "Notes" / "Research.txt").exists()


@pytest.mark.asyncio
async def test_delete_home_blocked(temp_notebook):
    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.state.cursor = 0  # Home
        assert app.state.visible_pages()[0].name == "Home"
        await pilot.press("d")
        await pilot.pause()
        # no confirm modal; Home still on disk; error status set
        assert (temp_notebook / "Home.txt").exists()
        assert app.status_err


@pytest.mark.asyncio
async def test_grep_search(temp_notebook):
    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("ctrl+f")
        await pilot.pause()
        await _type(pilot, "sprint")
        await pilot.pause(0.5)  # let the rg worker finish
        assert len(app.screen.results) >= 1


@pytest.mark.asyncio
async def test_editor_launch(temp_notebook, monkeypatch):
    import contextlib

    from zim_tui import app as app_module

    calls = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda cmd, *a, **k: calls.append(cmd))
    monkeypatch.setenv("EDITOR", "my-editor")

    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext())
        app.state.cursor = 0  # Home
        app.open_current_editor()
        await pilot.pause()
        assert calls and calls[0][0] == "my-editor"
        assert calls[0][1].endswith("Home.txt")
        assert app.status == "saved"


@pytest.mark.asyncio
async def test_follow_link(temp_notebook):
    app = make_app(temp_notebook)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.state.cursor = 0  # Home (has internal links)
        app.focus_panel("preview")
        await pilot.press("f")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "LinkPickModal"
        await pilot.press("enter")
        await pilot.pause()
        # navigated to a real resolved page
        assert app.state.current_page() is not None
        assert app.focus_name() == "tree"
