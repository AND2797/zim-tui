"""Yes/no confirmation modal. Only 'y'/'Y' confirms; any other key cancels."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class ConfirmModal(ModalScreen[bool]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"⚠  {self._message}", id="confirm-msg")
            yield Static("y confirm   any other key cancel", id="hint")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = " confirm "

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        self.dismiss(event.key in ("y", "Y"))
