"""CLI entry point. ``zim-tui [notebook-path]``."""

from __future__ import annotations

import os
import sys

from . import config, notebook
from .app import ZimApp

DEFAULT_ROOT = os.path.expanduser("~/Projects/zim-notes")


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    root = os.path.abspath(os.path.expanduser(root))

    try:
        nb = notebook.load(root)
    except OSError as exc:
        print(f"error loading notebook: {exc}", file=sys.stderr)
        sys.exit(1)

    config.add_notebook(root)
    cfg = config.load()

    app = ZimApp(nb, cfg.notebooks)
    app.run()


if __name__ == "__main__":
    main()
