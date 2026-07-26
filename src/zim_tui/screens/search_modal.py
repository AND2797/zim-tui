"""Search modal: name (synchronous) or content (async rg) with a live preview."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, Static

from .. import markup, notebook, search, styles
from ..notebook import Page
from ..search import SearchResult

if TYPE_CHECKING:
    pass

SELECTED = f"bold {styles.COLOR_SELECTED_FG} on {styles.COLOR_SELECTED}"


class _ResultsList(Widget):
    """Renders the search results with a windowed cursor (no own focus)."""

    def render(self) -> Text:
        modal: SearchModal = self.screen  # type: ignore[assignment]
        results = modal.results
        cursor = modal.result_cursor
        height = max(self.content_size.height, 1)
        width = max(self.content_size.width, 1)

        visible = min(len(results), height)
        start = cursor - visible + 1 if cursor >= visible else 0
        start = max(0, start)
        end = min(start + visible, len(results))

        text = Text()
        for i in range(start, end):
            disp = results[i].display
            if len(disp) > width - 3:
                disp = disp[: width - 4] + "…"
            prefix = "▶ " if i == cursor else "  "
            full = (prefix + disp).ljust(width)[:width]
            text.append(full, style=SELECTED if i == cursor else styles.COLOR_NORMAL)
            if i < end - 1:
                text.append("\n")
        return text


class SearchModal(ModalScreen[int | None]):
    BINDINGS = [
        ("escape", "cancel", "cancel"),
        ("up", "cursor_up", "up"),
        ("ctrl+p", "cursor_up", "up"),
        ("down", "cursor_down", "down"),
        ("ctrl+n", "cursor_down", "down"),
        ("enter", "select", "select"),
    ]

    def __init__(self, kind: str, pages: list[Page], root: str) -> None:
        super().__init__()
        self._kind = kind  # "name" or "content"
        self._pages = pages
        self._root = root
        self.results: list[SearchResult] = []
        self.result_cursor = 0
        self._query = ""
        self._seq = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Input(id="q", placeholder="type to search…")
            yield Static("", id="search-count")
            with Horizontal(id="search-body"):
                yield _ResultsList(id="search-results")
                with VerticalScroll(id="search-preview"):
                    yield Static("", id="search-preview-body")
            yield Static("↑↓ navigate   enter select   esc cancel", id="hint")

    def on_mount(self) -> None:
        label = "search: pages" if self._kind == "name" else "search: content"
        self.query_one("#dialog").border_title = f" {label} "
        self.query_one(Input).focus()
        if self._kind == "name":
            self.results = search.filter_pages_by_name("", self._pages)
        self._refresh_all()

    # --- input --------------------------------------------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        self._query = event.value
        self.result_cursor = 0
        if self._kind == "name":
            self.results = search.filter_pages_by_name(self._query, self._pages)
            self._refresh_all()
        else:
            self._seq += 1
            self.results = []
            self._refresh_all()
            if self._query.strip():
                self.run_worker(
                    partial(self._run_grep, self._query, self._seq),
                    thread=True,
                    exclusive=True,
                    group="grep",
                )

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        # Enter is consumed by the Input widget, so select from here.
        self.action_select()

    def _run_grep(self, query: str, seq: int) -> None:
        results = search.run_content_search(query, self._pages, self._root)
        self.app.call_from_thread(self._apply_grep, seq, results)

    def _apply_grep(self, seq: int, results: list[SearchResult]) -> None:
        if seq != self._seq:
            return  # stale response, a newer query is in flight
        self.results = results
        self.result_cursor = 0
        self._refresh_all()

    # --- navigation ---------------------------------------------------------

    def action_cursor_up(self) -> None:
        if self.result_cursor > 0:
            self.result_cursor -= 1
            self._refresh_results()

    def action_cursor_down(self) -> None:
        if self.result_cursor < len(self.results) - 1:
            self.result_cursor += 1
            self._refresh_results()

    def action_select(self) -> None:
        if self.results:
            self.dismiss(self.results[self.result_cursor].page_index)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    # --- rendering ----------------------------------------------------------

    def _count_text(self) -> str:
        if self._kind == "content" and self._query.strip() == "":
            return "  type to search…"
        n = len(self.results)
        if n == 0:
            return "  no results"
        if n == 1:
            return "  1 result"
        return f"  {n} results"

    def _refresh_results(self) -> None:
        self.query_one("#search-results", _ResultsList).refresh()
        self._refresh_preview()

    def _refresh_all(self) -> None:
        self.query_one("#search-count", Static).update(self._count_text())
        self._refresh_results()

    def _refresh_preview(self) -> None:
        body = self.query_one("#search-preview-body", Static)
        if not self.results or not (0 <= self.result_cursor < len(self.results)):
            body.update("")
            return
        idx = self.results[self.result_cursor].page_index
        if not (0 <= idx < len(self._pages)):
            body.update("")
            return
        try:
            content = notebook.read_content(self._pages[idx].path)
        except OSError:
            body.update("")
            return
        width = max(self.query_one("#search-preview").content_size.width - 2, 20)
        body.update(markup.render_zim_content(content, width))
