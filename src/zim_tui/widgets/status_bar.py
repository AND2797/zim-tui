"""The bottom status bar: focus-dependent hint, status message, right-side counter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text

from textual.widget import Widget

from .. import styles

if TYPE_CHECKING:
    from ..app import ZimApp

HINTS = {
    "tree": " n:new  N:sub  d:del  r:rename  /:search  ctrl+f:grep  1:notebooks  ?:help  q:quit",
    "notebooks": " j/k:navigate  enter:switch  h/esc:back to tree  l:preview  ?:help  q:quit",
    "preview": " e:edit  f:follow link  h:tree  ?:help  q:quit",
}


class StatusBar(Widget):
    @property
    def zim(self) -> "ZimApp":
        return self.app  # type: ignore[return-value]

    def render(self) -> Text:
        app = self.zim
        width = max(self.size.width, 1)

        if app.status and app.status_err:
            left = Text(f" ✗ {app.status}", style=f"bold {styles.COLOR_ERROR}")
        elif app.status:
            left = Text(f" ✓ {app.status}", style=styles.COLOR_SUCCESS)
        else:
            left = Text(HINTS.get(app.focus_name(), HINTS["tree"]), style=styles.STYLE_SUBTLE)

        vp = app.state.visible_pages()
        total = len(vp)
        pos = app.state.cursor + 1 if total else 0
        right = Text(f" {pos}/{total} ", style=styles.STYLE_SUBTLE)

        gap = max(width - left.cell_len - right.cell_len, 0)
        line = Text()
        line.append_text(left)
        line.append(" " * gap)
        line.append_text(right)
        return line
