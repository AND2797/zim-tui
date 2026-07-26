"""Pure tree-navigation state, independent of the UI framework.

Holds the flat page list, the collapsed set, and the cursor (an index into
``visible_pages()``, never into the full ``pages`` list).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .notebook import Page


@dataclass
class NotebookState:
    root: str
    pages: list[Page]
    collapsed: set[str] = field(default_factory=set)  # page.path values
    cursor: int = 0

    # --- visibility ---------------------------------------------------------

    def visible_pages(self) -> list[Page]:
        """Pages not hidden under a collapsed ancestor (a collapsed page stays visible)."""
        if not self.collapsed:
            return self.pages
        return [p for p in self.pages if not self._is_ancestor_collapsed(p)]

    def _is_ancestor_collapsed(self, page: Page) -> bool:
        cur = page.parent
        while cur is not None:
            if cur.path in self.collapsed:
                return True
            cur = cur.parent
        return False

    def current_page(self) -> Page | None:
        vp = self.visible_pages()
        if not vp or not (0 <= self.cursor < len(vp)):
            return None
        return vp[self.cursor]

    # --- collapse -----------------------------------------------------------

    def toggle_collapse(self) -> None:
        """Collapse/expand the selected node. On a leaf, collapse its parent instead."""
        vp = self.visible_pages()
        if not vp:
            return
        page = vp[self.cursor]

        if not page.children:  # leaf
            if page.parent is None:
                return  # top-level leaf: nothing to do
            page = page.parent
            for i, p in enumerate(vp):
                if p.path == page.path:
                    self.cursor = i
                    break

        if page.path in self.collapsed:
            self.collapsed.discard(page.path)  # expand
            return

        self.collapsed.add(page.path)
        new_vp = self.visible_pages()
        if self.cursor >= len(new_vp):
            self.cursor = len(new_vp) - 1
        for i, p in enumerate(new_vp):  # keep selection on the collapsed node
            if p.path == page.path:
                self.cursor = i
                break

    # --- link resolution ----------------------------------------------------

    def resolve_link_index(self, target: str) -> int:
        """Map a Zim link target to its index in ``pages``, or -1.

        Strategies in order: absolute from root, relative to current page's
        directory, then a loose name match handling the ``_``↔space convention.
        """
        target = target[1:] if target.startswith(":") else target
        parts = target.split(":")

        def find(path: str) -> int:
            for i, p in enumerate(self.pages):
                if p.path == path:
                    return i
            return -1

        rel_path = "/".join(parts) + ".txt"

        i = find(os.path.join(self.root, rel_path))
        if i >= 0:
            return i

        vp = self.visible_pages()
        if vp and self.cursor < len(vp):
            cur_dir = os.path.dirname(vp[self.cursor].path)
            i = find(os.path.join(cur_dir, rel_path))
            if i >= 0:
                return i

        name = parts[-1]
        name_alt = name.replace("_", " ")
        for i, p in enumerate(self.pages):
            p_name_alt = p.name.replace("_", " ")
            if (
                p.name.casefold() == name.casefold()
                or p.name.casefold() == name_alt.casefold()
                or p_name_alt.casefold() == name.casefold()
            ):
                return i
        return -1

    def navigate_to_page(self, idx: int) -> bool:
        """Expand collapsed ancestors of ``pages[idx]`` and move the cursor there.

        Returns False if ``idx`` is out of range (no change).
        """
        if not (0 <= idx < len(self.pages)):
            return False
        target = self.pages[idx]
        cur = target.parent
        while cur is not None:
            self.collapsed.discard(cur.path)
            cur = cur.parent
        vp = self.visible_pages()
        for i, p in enumerate(vp):
            if p.path == target.path:
                self.cursor = i
                break
        return True
