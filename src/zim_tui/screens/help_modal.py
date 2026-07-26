"""Context-sensitive keybinding help. Content depends on the focused panel."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from .. import styles

SECTIONS = {
    "tree": (
        "pages",
        [
            ("j / ↓", "move down"),
            ("k / ↑", "move up"),
            ("ctrl+d / u", "half page down/up"),
            ("g / G", "top / bottom"),
            ("enter / o", "open in editor"),
            ("space / tab", "collapse / expand"),
            ("n", "new page"),
            ("N", "new sub-page"),
            ("d", "delete"),
            ("r", "rename"),
            ("/", "search pages"),
            ("ctrl+f", "search content"),
            ("l / →", "focus preview"),
            ("1", "focus notebooks"),
        ],
    ),
    "notebooks": (
        "notebooks",
        [
            ("j / k", "navigate"),
            ("enter", "switch notebook"),
            ("+ open path", "open directory"),
            ("h / esc", "back to pages"),
        ],
    ),
    "preview": (
        "preview",
        [
            ("j / ↓", "scroll down"),
            ("k / ↑", "scroll up"),
            ("ctrl+d / u", "half page down/up"),
            ("g / G", "top / bottom"),
            ("e / enter", "open in editor"),
            ("f", "follow link"),
            ("h / ← / esc", "focus pages"),
        ],
    ),
}

GLOBAL = (
    "global",
    [
        ("1 / 2 / 3", "switch panel"),
        ("q / ctrl+c", "quit"),
        ("?", "close help"),
    ],
)


class HelpModal(ModalScreen[None]):
    BINDINGS = [
        ("escape,q,question_mark", "close", "close"),
        ("j,down", "scroll_down", "down"),
        ("k,up", "scroll_up", "up"),
        ("ctrl+d", "half_down", "half down"),
        ("ctrl+u", "half_up", "half up"),
        ("g", "top", "top"),
        ("G", "bottom", "bottom"),
    ]

    def __init__(self, focus: str) -> None:
        super().__init__()
        self._focus = focus

    def _build(self) -> Text:
        text = Text()
        sections = [SECTIONS.get(self._focus, SECTIONS["tree"]), GLOBAL]
        for si, (title, rows) in enumerate(sections):
            if si:
                text.append("\n")
            text.append(f" {title}\n", style=f"bold {styles.COLOR_NORMAL}")
            for key, desc in rows:
                text.append("  ")
                text.append(key.ljust(14), style=f"bold {styles.COLOR_BOLD}")
                text.append(desc + "\n", style=styles.STYLE_SUBTLE)
        return text

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with VerticalScroll(id="help-scroll"):
                yield Static(self._build(), id="help-body")
            yield Static("j/k scroll   esc close", id="hint")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = " keybindings "

    def action_close(self) -> None:
        self.dismiss(None)

    def action_scroll_down(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_up(animate=False)

    def action_half_down(self) -> None:
        s = self.query_one("#help-scroll", VerticalScroll)
        s.scroll_relative(y=s.scrollable_content_region.height // 2, animate=False)

    def action_half_up(self) -> None:
        s = self.query_one("#help-scroll", VerticalScroll)
        s.scroll_relative(y=-s.scrollable_content_region.height // 2, animate=False)

    def action_top(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_home(animate=False)

    def action_bottom(self) -> None:
        self.query_one("#help-scroll", VerticalScroll).scroll_end(animate=False)
