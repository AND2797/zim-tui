"""The preview panel ([3]). A scrollable container rendering Zim markup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual import events
from textual.containers import VerticalScroll
from textual.widgets import Static

if TYPE_CHECKING:
    from ..app import ZimApp


class PreviewPanel(VerticalScroll):
    can_focus = True

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._body = Static(id="preview-body")
        self._breadcrumb = "(empty notebook)"

    @property
    def zim(self) -> "ZimApp":
        return self.app  # type: ignore[return-value]

    def compose(self):
        yield self._body

    def set_content(self, text: Text, breadcrumb: str) -> None:
        self._breadcrumb = breadcrumb
        self._body.update(text)
        self.scroll_home(animate=False)
        self.update_title()

    def update_title(self) -> None:
        title = f"[3]─{self._breadcrumb}"
        if self.max_scroll_y > 0:
            pct = int(round(self.scroll_y / self.max_scroll_y * 100)) if self.max_scroll_y else 0
            title += f"  {pct}%"
        self.border_title = title

    def watch_scroll_y(self, old: float, new: float) -> None:  # type: ignore[override]
        super().watch_scroll_y(old, new)
        self.update_title()

    def on_key(self, event: events.Key) -> None:
        app = self.zim
        key = event.key
        handled = True
        if key in ("j", "down"):
            self.scroll_down(animate=False)
        elif key in ("k", "up"):
            self.scroll_up(animate=False)
        elif key == "ctrl+d":
            self.scroll_relative(y=self.scrollable_content_region.height // 2, animate=False)
        elif key == "ctrl+u":
            self.scroll_relative(y=-self.scrollable_content_region.height // 2, animate=False)
        elif key == "g":
            self.scroll_home(animate=False)
        elif key == "G":
            self.scroll_end(animate=False)
        elif key in ("e", "enter"):
            app.open_current_editor()
        elif key == "f":
            app.follow_link()
        elif key in ("h", "left", "escape"):
            app.focus_panel("tree")
        else:
            handled = False
        if handled:
            event.stop()
            event.prevent_default()

    def on_click(self, event: events.Click) -> None:
        self.focus()
