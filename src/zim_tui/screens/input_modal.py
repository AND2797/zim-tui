"""Text-input modal: new page / sub-page / rename / open notebook."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class InputModal(ModalScreen[str | None]):
    BINDINGS = [("escape", "cancel", "cancel")]

    def __init__(self, title: str, prompt: str, initial: str) -> None:
        super().__init__()
        self._title = title
        self._prompt = prompt
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._prompt, id="prompt")
            yield Input(value=self._initial, id="input")
            yield Static("enter confirm   esc cancel", id="hint")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = f" {self._title} "
        inp = self.query_one(Input)
        inp.focus()
        inp.cursor_position = len(self._initial)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value or None)

    def action_cancel(self) -> None:
        self.dismiss(None)
