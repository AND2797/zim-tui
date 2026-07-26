"""Persistent config: the list of known notebook paths.

Stored as JSON at ``<user config dir>/zim-tui/notebooks.json``, where the user
config directory is macOS ``~/Library/Application Support``, Linux
``$XDG_CONFIG_HOME`` or ``~/.config``, and Windows ``%AppData%``.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    notebooks: list[str] = field(default_factory=list)


def _config_dir() -> Path:
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    elif sys.platform == "win32":
        base = os.environ.get("AppData") or os.path.expanduser("~")
    else:  # linux and others
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    return Path(base) / "zim-tui"


def _config_file() -> Path:
    return _config_dir() / "notebooks.json"


def load() -> Config:
    """Load config, returning an empty config on any read/parse error."""
    try:
        raw = _config_file().read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError):
        return Config()
    notebooks = data.get("notebooks") or []
    return Config(notebooks=list(notebooks))


def save(config: Config) -> None:
    """Persist config as pretty-printed JSON."""
    directory = _config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"notebooks": config.notebooks}, indent=2)
    _config_file().write_text(payload, encoding="utf-8")


def add_notebook(path: str) -> None:
    """Add ``path`` to the known notebooks (idempotent, saves only on change)."""
    config = load()
    if path in config.notebooks:
        return
    config.notebooks.append(path)
    try:
        save(config)
    except OSError:
        pass
