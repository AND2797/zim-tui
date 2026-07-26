"""Filesystem I/O for Zim notebooks. No UI concerns.

A Zim page is dual-natured: ``foo.txt`` holds the page's own content and a
sibling ``foo/`` directory holds its sub-pages. A single :class:`Page` covers
both — ``path`` is the ``.txt`` file, ``dir`` is the sub-page directory (empty
for a leaf). A directory with no matching ``.txt`` is ignored.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Page:
    """A single Zim wiki page."""

    name: str  # base filename without .txt, still underscore-encoded (e.g. "My_Page")
    path: str  # absolute path to the page's .txt file
    dir: str = ""  # absolute path to the sub-page directory, or "" if a leaf
    parent: "Page | None" = field(default=None, repr=False, compare=False)
    children: list["Page"] = field(default_factory=list, repr=False, compare=False)
    depth: int = 0


@dataclass
class Notebook:
    """A loaded notebook: a root and a flat, pre-order list of every page."""

    root: str
    pages: list[Page]


def load(root: str) -> Notebook:
    """Load a notebook by scanning ``root`` recursively."""
    pages = _scan_dir(root, None, 0)
    return Notebook(root=root, pages=pages)


def _scan_dir(directory: str, parent: Page | None, depth: int) -> list[Page]:
    """Recursively scan ``directory`` into a flat pre-order list of pages."""
    txt_files: dict[str, str] = {}
    sub_dirs: dict[str, bool] = {}

    for entry in Path(directory).iterdir():
        if entry.is_dir():
            sub_dirs[entry.name] = True
        elif entry.name.endswith(".txt"):
            key = entry.name[: -len(".txt")]
            txt_files[key] = str(entry)

    out: list[Page] = []
    for name in sorted(txt_files):  # lexicographic byte-order, capitals before lowercase
        page = Page(name=name, path=txt_files[name], parent=parent, depth=depth)
        if sub_dirs.get(name):
            page.dir = str(Path(directory) / name)
            page.children = _scan_dir(page.dir, page, depth + 1)
        out.append(page)
        out.extend(page.children)  # children are already flattened by recursion
    return out


def read_content(path: str) -> str:
    """Return the text content of a page file."""
    return Path(path).read_text(encoding="utf-8")


def create_page(parent_dir: str, name: str) -> str:
    """Create a new page ``name`` in ``parent_dir``. Returns the created path.

    Raises :class:`FileExistsError` if the page already exists.
    """
    name = sanitize_name(name)
    file_path = Path(parent_dir) / f"{name}.txt"
    if file_path.exists():
        raise FileExistsError(f"page {name!r} already exists")
    file_path.write_text(zim_header(name), encoding="utf-8")
    return str(file_path)


def create_sub_page(parent: Page, name: str) -> str:
    """Create a sub-page under ``parent``, materialising its directory if needed.

    If ``parent`` was a leaf, its sub-page directory is created and ``parent.dir``
    is mutated in place so subsequent creations in the same session work.
    """
    if not parent.dir:
        sub_dir = parent.path[: -len(".txt")] if parent.path.endswith(".txt") else parent.path
        Path(sub_dir).mkdir(parents=True, exist_ok=True)
        parent.dir = sub_dir
    return create_page(parent.dir, name)


def delete_page(page: Page) -> None:
    """Delete a page's ``.txt`` and its sub-page directory. Missing files are ignored."""
    Path(page.path).unlink(missing_ok=True)
    if page.dir:
        shutil.rmtree(page.dir, ignore_errors=False)


def rename_page(page: Page, new_name: str) -> None:
    """Rename a page within its current parent directory (both .txt and dir)."""
    new_name = sanitize_name(new_name)
    directory = Path(page.path).parent
    new_path = directory / f"{new_name}.txt"
    Path(page.path).rename(new_path)
    if page.dir:
        new_dir = directory / new_name
        Path(page.dir).rename(new_dir)


def move_page(page: Page, new_parent_dir: str) -> None:
    """Move a page (keeping its base name) into a different parent directory."""
    new_path = Path(new_parent_dir) / Path(page.path).name
    Path(page.path).rename(new_path)
    if page.dir:
        new_dir = Path(new_parent_dir) / Path(page.dir).name
        Path(page.dir).rename(new_dir)


_NOTEBOOK_ZIM = """[Notebook]
version=0.4
name=%s
interwiki=
home=Home
icon=
document_root=
short_links=False
shared=False
endofline=unix
disable_trash=False
default_file_format=zim-wiki
default_file_extension=.txt
notebook_layout=files
"""


def create_notebook(root: str) -> None:
    """Initialise a new Zim-compatible notebook at ``root``."""
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    name = root_path.name
    (root_path / "notebook.zim").write_text(_NOTEBOOK_ZIM % name, encoding="utf-8")
    (root_path / "Home.txt").write_text(zim_header("Home"), encoding="utf-8")


def sanitize_name(name: str) -> str:
    """Trim whitespace and replace spaces with underscores (the filename convention)."""
    return name.strip().replace(" ", "_")


def zim_header(title: str) -> str:
    """Return the standard Zim page header seeded into new pages."""
    display_title = title.replace("_", " ")
    creation_date = datetime.now().astimezone().isoformat(timespec="seconds")
    created = datetime.now().strftime("%A %d %B %Y")
    return (
        "Content-Type: text/x-zim-wiki\n"
        "Wiki-Format: zim 0.6\n"
        f"Creation-Date: {creation_date}\n"
        "\n"
        f"====== {display_title} ======\n"
        f"Created {created}\n"
    )
