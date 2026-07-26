"""Follow-link picker: choose an internal link on the current page to open."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from .. import styles
from ..search import LinkItem

SELECTED = f"bold {styles.COLOR_SELECTED_FG} on {styles.COLOR_SELECTED}"
MAX_VISIBLE = 12


class LinkPickModal(ModalScreen[str | None]):
    def __init__(self, links: list[LinkItem]) -> None:
        super().__init__()
        self._links = links
        self._cursor = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._build(), id="linkpick-body")
            yield Static("enter follow   esc back", id="hint")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = " follow link "

    def _build(self) -> Text:
        text = Text()
        n = len(self._links)
        visible = min(n, MAX_VISIBLE)
        start = self._cursor - visible + 1 if self._cursor >= visible else 0
        start = max(0, start)
        end = min(start + visible, n)
        for i in range(start, end):
            item = self._links[i]
            disp = item.display
            if len(disp) > 48:
                disp = disp[:47] + "…"
            prefix = "▶ " if i == self._cursor else "  "
            style = SELECTED if i == self._cursor else styles.COLOR_NORMAL
            text.append(prefix + disp, style=style)
            if i < end - 1:
                text.append("\n")
        return text

    def _refresh(self) -> None:
        self.query_one("#linkpick-body", Static).update(self._build())

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        key = event.key
        if key in ("j", "down"):
            self._cursor = min(len(self._links) - 1, self._cursor + 1)
            self._refresh()
        elif key in ("k", "up"):
            self._cursor = max(0, self._cursor - 1)
            self._refresh()
        elif key == "enter":
            if 0 <= self._cursor < len(self._links):
                self.dismiss(self._links[self._cursor].target)
            else:
                self.dismiss(None)
        elif key in ("escape", "q"):
            self.dismiss(None)
