"""The Textual application: 3-panel layout, navigation, and action wiring."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical

from . import config, markup, notebook, search
from .notebook import Notebook
from .screens import ConfirmModal, HelpModal, InputModal, LinkPickModal, SearchModal
from .state import NotebookState
from .widgets import NotebooksPanel, PreviewPanel, StatusBar, TreePanel


class ZimApp(App):
    CSS_PATH = "app.tcss"
    # Disable the default footer/command palette bindings we don't want.
    BINDINGS = []  # global keys handled in on_key for precise dispatch control

    def __init__(self, nb: Notebook, notebooks: list[str]) -> None:
        super().__init__()
        self.state = NotebookState(root=nb.root, pages=nb.pages)
        self.notebooks: list[str] = list(notebooks)
        self.notebook_cursor: int = 0
        self.tree_offset: int = 0
        self.status: str = ""
        self.status_err: bool = False

    # --- layout -------------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield NotebooksPanel(id="notebooks")
                yield TreePanel(id="tree")
            yield PreviewPanel(id="preview")
        yield StatusBar(id="status")

    def on_mount(self) -> None:
        self._sync_notebook_cursor()
        self._size_notebooks_panel()
        self.query_one(TreePanel).border_title = f"[2]─{os.path.basename(self.state.root)}"
        self.query_one(NotebooksPanel).border_title = "[1]─notebooks"
        self.query_one(TreePanel).focus()
        self.refresh_preview()
        self.refresh_panels()

    def on_resize(self, event: events.Resize) -> None:
        self.refresh_preview()

    # --- focus --------------------------------------------------------------

    def focus_name(self) -> str:
        focused = self.focused
        if focused is None:
            return "tree"
        return {"notebooks": "notebooks", "tree": "tree", "preview": "preview"}.get(
            focused.id or "", "tree"
        )

    def focus_panel(self, name: str) -> None:
        widget = {
            "tree": TreePanel,
            "preview": PreviewPanel,
            "notebooks": NotebooksPanel,
        }[name]
        self.query_one(widget).focus()
        if name == "notebooks":
            self._sync_notebook_cursor()
        self.refresh_panels()

    # --- refresh helpers ----------------------------------------------------

    def refresh_panels(self) -> None:
        self.query_one(TreePanel).refresh()
        self.query_one(NotebooksPanel).refresh()
        self.query_one(StatusBar).refresh()

    def refresh_preview(self) -> None:
        preview = self.query_one(PreviewPanel)
        page = self.state.current_page()
        if page is None:
            preview.set_content(markup.render_zim_content("", 0), "(empty notebook)")
            self.query_one(StatusBar).refresh()
            return
        width = max(preview.content_size.width - 2, 20)
        try:
            content = notebook.read_content(page.path)
            text = markup.render_zim_content(content, width)
        except OSError as exc:
            from rich.text import Text

            text = Text(f"error reading file: {exc}", style="bold #FF5555")
        preview.set_content(text, search.page_breadcrumb(page))
        self.query_one(StatusBar).refresh()

    def set_status(self, msg: str, err: bool = False) -> None:
        self.status = msg
        self.status_err = err
        self.query_one(StatusBar).refresh()

    # --- tree navigation ----------------------------------------------------

    def tree_up(self) -> None:
        if self.state.cursor > 0:
            self.state.cursor -= 1
            self._after_cursor_move()

    def tree_down(self) -> None:
        if self.state.cursor < len(self.state.visible_pages()) - 1:
            self.state.cursor += 1
            self._after_cursor_move()

    def tree_page(self, delta: int) -> None:
        vp = self.state.visible_pages()
        self.state.cursor = max(0, min(len(vp) - 1, self.state.cursor + delta))
        self._after_cursor_move()

    def tree_top(self) -> None:
        self.state.cursor = 0
        self.tree_offset = 0
        self._after_cursor_move()

    def tree_bottom(self) -> None:
        self.state.cursor = max(0, len(self.state.visible_pages()) - 1)
        self._after_cursor_move()

    def toggle_collapse(self) -> None:
        self.state.toggle_collapse()
        self._after_cursor_move()

    def _after_cursor_move(self) -> None:
        self.refresh_preview()
        self.refresh_panels()

    # --- editor -------------------------------------------------------------

    def open_current_editor(self) -> None:
        page = self.state.current_page()
        if page is None:
            return
        editor = os.environ.get("EDITOR") or "vim"
        err: Exception | None = None
        with self.suspend():
            try:
                subprocess.run([editor, page.path])
            except Exception as exc:  # noqa: BLE001 - report any launch failure
                err = exc
        if err is not None:
            self.set_status(f"editor error: {err}", err=True)
        else:
            self.set_status("saved")
        self.refresh_preview()

    # --- page mutations -----------------------------------------------------

    def _current_parent_dir(self) -> str:
        page = self.state.current_page()
        if page is None:
            return self.state.root
        return os.path.dirname(page.path)

    def new_page(self) -> None:
        self.push_screen(InputModal("new page", "New page name:", ""), self._commit_new_page)

    def _commit_new_page(self, name: str | None) -> None:
        if not name:
            return
        try:
            notebook.create_page(self._current_parent_dir(), name)
            self.set_status(f"created: {name}")
        except OSError as exc:
            self.set_status(str(exc), err=True)
        self.reload_from_disk()

    def new_sub_page(self) -> None:
        page = self.state.current_page()
        if page is None:
            return
        self.push_screen(
            InputModal("new sub-page", f"New sub-page under {page.name!r}:", ""),
            self._commit_new_sub,
        )

    def _commit_new_sub(self, name: str | None) -> None:
        if not name:
            return
        page = self.state.current_page()
        if page is None:
            return
        try:
            notebook.create_sub_page(page, name)
            self.set_status(f"created: {name}")
        except OSError as exc:
            self.set_status(str(exc), err=True)
        self.reload_from_disk()

    def rename_current(self) -> None:
        page = self.state.current_page()
        if page is None:
            return
        self.push_screen(
            InputModal("rename", f"Rename {page.name!r} to:", page.name),
            self._commit_rename,
        )

    def _commit_rename(self, name: str | None) -> None:
        if not name:
            return
        page = self.state.current_page()
        if page is None:
            return
        try:
            notebook.rename_page(page, name)
            self.set_status(f"renamed: {name}")
        except OSError as exc:
            self.set_status(str(exc), err=True)
        self.reload_from_disk()

    def delete_current(self) -> None:
        page = self.state.current_page()
        if page is None:
            return
        if page.name == "Home" and page.parent is None:
            self.set_status(
                "Home page cannot be deleted — Zim requires it as the notebook entry point",
                err=True,
            )
            return
        msg = (
            f"Delete {page.name!r} and all sub-pages?"
            if page.children
            else f"Delete {page.name!r}?"
        )
        self._pending_delete = page
        self.push_screen(ConfirmModal(msg), self._commit_delete)

    def _commit_delete(self, confirmed: bool | None) -> None:
        page = getattr(self, "_pending_delete", None)
        self._pending_delete = None
        if not confirmed or page is None:
            self.set_status("cancelled")
            return
        try:
            notebook.delete_page(page)
            self.set_status(f"deleted: {page.name}")
        except OSError as exc:
            self.set_status(str(exc), err=True)
        self.reload_from_disk()

    # --- search -------------------------------------------------------------

    def open_search(self) -> None:
        self.push_screen(
            SearchModal("name", self.state.pages, self.state.root),
            self._after_search,
        )

    def open_grep(self) -> None:
        self.push_screen(
            SearchModal("content", self.state.pages, self.state.root),
            self._after_search,
        )

    def _after_search(self, page_index: int | None) -> None:
        if page_index is None:
            return
        if self.state.navigate_to_page(page_index):
            self.focus_panel("tree")
            self._after_cursor_move()

    # --- link following -----------------------------------------------------

    def follow_link(self) -> None:
        page = self.state.current_page()
        if page is None:
            return
        try:
            content = notebook.read_content(page.path)
        except OSError as exc:
            self.set_status(f"error reading file: {exc}", err=True)
            return
        links = search.extract_links(content)
        if not links:
            self.set_status("no links on this page")
            return
        self.push_screen(LinkPickModal(links), self._after_link_pick)

    def _after_link_pick(self, target: str | None) -> None:
        if target is None:
            return
        idx = self.state.resolve_link_index(target)
        if idx >= 0:
            self.state.navigate_to_page(idx)
            self.focus_panel("tree")
            self._after_cursor_move()
        else:
            self.set_status(f"page not found: {target}", err=True)

    # --- notebooks ----------------------------------------------------------

    def notebook_select(self) -> None:
        if self.notebook_cursor == len(self.notebooks):
            self.push_screen(
                InputModal("open notebook", "Notebook path:", ""),
                self._commit_open_notebook,
            )
            return
        self.switch_to_notebook(self.notebooks[self.notebook_cursor])

    def _commit_open_notebook(self, raw: str | None) -> None:
        if not raw:
            return
        path = str(Path(os.path.expanduser(raw)).resolve())
        if not os.path.exists(path):
            self._pending_new_notebook = path
            self.push_screen(
                ConfirmModal(f"Create new notebook at {path!r}?"),
                self._commit_create_notebook,
            )
            return
        self.switch_to_notebook(path)

    def _commit_create_notebook(self, confirmed: bool | None) -> None:
        path = getattr(self, "_pending_new_notebook", None)
        self._pending_new_notebook = None
        if not confirmed or path is None:
            self.set_status("cancelled")
            return
        try:
            notebook.create_notebook(path)
        except OSError as exc:
            self.set_status(str(exc), err=True)
            return
        self.switch_to_notebook(path)

    def switch_to_notebook(self, path: str) -> None:
        try:
            nb = notebook.load(path)
        except OSError as exc:
            self.set_status(f"error loading notebook: {exc}", err=True)
            return
        config.add_notebook(path)
        if path not in self.notebooks:
            self.notebooks.append(path)
        self.state = NotebookState(root=nb.root, pages=nb.pages)
        self.tree_offset = 0
        self._sync_notebook_cursor()
        self._size_notebooks_panel()
        self.query_one(TreePanel).border_title = f"[2]─{os.path.basename(self.state.root)}"
        self.focus_panel("tree")
        self.set_status(f"opened: {os.path.basename(path)}")
        self.refresh_preview()
        self.refresh_panels()

    def _sync_notebook_cursor(self) -> None:
        for i, path in enumerate(self.notebooks):
            if path == self.state.root:
                self.notebook_cursor = i
                return
        self.notebook_cursor = 0

    def _size_notebooks_panel(self) -> None:
        height = min(len(self.notebooks) + 4, 12)
        self.query_one(NotebooksPanel).styles.height = height

    # --- help ---------------------------------------------------------------

    def open_help(self) -> None:
        self.push_screen(HelpModal(self.focus_name()))

    # --- reload -------------------------------------------------------------

    def reload_from_disk(self) -> None:
        try:
            nb = notebook.load(self.state.root)
        except OSError as exc:
            self.set_status(f"reload error: {exc}", err=True)
            return
        self.state.pages = nb.pages
        vp = self.state.visible_pages()
        if self.state.cursor >= len(vp):
            self.state.cursor = max(0, len(vp) - 1)
        self.refresh_preview()
        self.refresh_panels()

    # --- global keys --------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if key == "1":
            self.focus_panel("notebooks")
        elif key == "2":
            self.focus_panel("tree")
        elif key == "3":
            self.focus_panel("preview")
        elif key in ("q", "ctrl+c"):
            self.exit()
        elif event.character == "?":
            self.open_help()
        else:
            return
        event.stop()
        event.prevent_default()
