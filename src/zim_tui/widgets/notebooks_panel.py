"""The notebooks panel ([1]). Lists known notebooks plus an 'open path' row."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich.text import Text
from textual import events
from textual.widget import Widget

from .. import styles

if TYPE_CHECKING:
    from ..app import ZimApp

SELECTED = f"bold {styles.COLOR_SELECTED_FG} on {styles.COLOR_SELECTED}"
NORMAL = styles.COLOR_NORMAL


class NotebooksPanel(Widget):
    can_focus = True

    @property
    def zim(self) -> "ZimApp":
        return self.app  # type: ignore[return-value]

    def render(self) -> Text:
        app = self.zim
        notebooks = app.notebooks
        cursor = app.notebook_cursor
        current = app.state.root
        focused = self.has_focus
        width = max(self.content_size.width, 1)

        out = Text()
        for i, path in enumerate(notebooks):
            name = os.path.basename(path.rstrip("/")) or path
            selected = focused and cursor == i
            is_current = path == current
            prefix = "▶ " if selected else ("• " if is_current else "  ")
            label = prefix + name
            if is_current:
                label += " (current)"
            full = label.ljust(width)[:width]
            out.append(full, style=SELECTED if selected else NORMAL)
            out.append("\n")

        out.append("─" * width, style=styles.STYLE_SUBTLE)
        out.append("\n")

        op_selected = focused and cursor == len(notebooks)
        op_label = ("▶ " if op_selected else "  ") + "+ open path..."
        full = op_label.ljust(width)[:width]
        out.append(full, style=SELECTED if op_selected else NORMAL)
        return out

    def on_key(self, event: events.Key) -> None:
        app = self.zim
        key = event.key
        handled = True
        total = len(app.notebooks) + 1
        if key in ("k", "up"):
            app.notebook_cursor = max(0, app.notebook_cursor - 1)
            self.refresh()
        elif key in ("j", "down"):
            app.notebook_cursor = min(total - 1, app.notebook_cursor + 1)
            self.refresh()
        elif key == "g":
            app.notebook_cursor = 0
            self.refresh()
        elif key == "G":
            app.notebook_cursor = total - 1
            self.refresh()
        elif key == "enter":
            app.notebook_select()
        elif key in ("h", "left", "escape"):
            app.focus_panel("tree")
        elif key in ("l", "right"):
            app.focus_panel("preview")
        else:
            handled = False
        if handled:
            event.stop()
            event.prevent_default()

    def on_click(self, event: events.Click) -> None:
        app = self.zim
        row = event.y
        if 0 <= row < len(app.notebooks):
            app.notebook_cursor = row
        self.focus()
        self.refresh()
