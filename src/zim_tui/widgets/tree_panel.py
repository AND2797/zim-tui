"""The page-tree panel ([2]). Renders a scrolling window over visible_pages()."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual import events
from textual.widget import Widget

from .. import styles

if TYPE_CHECKING:
    from ..app import ZimApp

SELECTED = f"bold {styles.COLOR_SELECTED_FG} on {styles.COLOR_SELECTED}"
NORMAL = styles.COLOR_NORMAL


class TreePanel(Widget):
    can_focus = True

    @property
    def zim(self) -> "ZimApp":
        return self.app  # type: ignore[return-value]

    def visible_rows(self) -> int:
        return max(self.content_size.height, 1)

    def clamp_offset(self) -> None:
        """Keep the cursor within the visible window."""
        st = self.zim.state
        visible = self.visible_rows()
        if st.cursor < self.zim.tree_offset:
            self.zim.tree_offset = st.cursor
        if st.cursor >= self.zim.tree_offset + visible:
            self.zim.tree_offset = st.cursor - visible + 1
        if self.zim.tree_offset < 0:
            self.zim.tree_offset = 0

    def render(self) -> Text:
        st = self.zim.state
        vp = st.visible_pages()
        height = self.visible_rows()
        width = max(self.content_size.width, 1)
        self.clamp_offset()
        offset = self.zim.tree_offset

        out = Text()
        end = min(offset + height, len(vp))
        for i in range(offset, end):
            p = vp[i]
            indent = "  " * p.depth
            if p.children:
                icon = "▶ " if p.path in st.collapsed else "▼ "
            else:
                icon = "  "
            label = indent + icon + p.name
            if len(label) > width - 1:
                label = label[: width - 2] + "…"
            full = label.ljust(width)[:width]
            style = SELECTED if i == st.cursor else NORMAL
            out.append(full, style=style)
            if i < end - 1:
                out.append("\n")
        return out

    def on_key(self, event: events.Key) -> None:
        app = self.zim
        key = event.key
        handled = True
        if key in ("k", "up"):
            app.tree_up()
        elif key in ("j", "down"):
            app.tree_down()
        elif key == "ctrl+u":
            app.tree_page(-self.visible_rows() // 2)
        elif key == "ctrl+d":
            app.tree_page(self.visible_rows() // 2)
        elif key == "g":
            app.tree_top()
        elif key == "G":
            app.tree_bottom()
        elif key in ("enter", "o"):
            app.open_current_editor()
        elif key in ("space", "tab"):
            app.toggle_collapse()
        elif key == "n":
            app.new_page()
        elif key == "N":
            app.new_sub_page()
        elif key == "d":
            app.delete_current()
        elif key == "r":
            app.rename_current()
        elif key == "slash":
            app.open_search()
        elif key == "ctrl+f":
            app.open_grep()
        elif key == "ctrl+n":
            app.focus_panel("notebooks")
        elif key in ("l", "right"):
            app.focus_panel("preview")
        else:
            handled = False
        if handled:
            event.stop()
            event.prevent_default()

    def on_mouse_scroll_down(self, event: events.MouseScrollDown) -> None:
        self.zim.tree_down()
        event.stop()

    def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self.zim.tree_up()
        event.stop()

    def on_click(self, event: events.Click) -> None:
        app = self.zim
        vp = app.state.visible_pages()
        row = event.y  # 0-based within the widget content (border excluded)
        idx = app.tree_offset + row
        if 0 <= idx < len(vp):
            app.state.cursor = idx
            app.refresh_preview()
            app.refresh_panels()
        self.focus()
