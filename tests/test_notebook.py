"""Tests for notebook filesystem I/O (load, create, rename, delete)."""

from __future__ import annotations

from pathlib import Path

import pytest

from zim_tui import notebook


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.parametrize(
    "setup, want_names, want_depths",
    [
        pytest.param(lambda d: None, [], None, id="empty dir yields no pages"),
        pytest.param(
            lambda d: (write_file(d / "zebra.txt"), write_file(d / "apple.txt")),
            ["apple", "zebra"],
            [0, 0],
            id="flat pages sorted alphabetically",
        ),
        pytest.param(
            lambda d: (
                write_file(d / "parent.txt"),
                write_file(d / "parent" / "child.txt"),
            ),
            ["parent", "child"],
            [0, 1],
            id="nested pages appear depth-first, child depth=1",
        ),
        pytest.param(
            lambda d: (
                (d / "orphan").mkdir(),
                write_file(d / "visible.txt"),
            ),
            ["visible"],
            None,
            id="orphan dir without matching .txt is skipped",
        ),
        pytest.param(
            lambda d: (
                write_file(d / "page.txt"),
                write_file(d / "image.png"),
                write_file(d / "notebook.zim", "[Notebook]"),
            ),
            ["page"],
            None,
            id="non-.txt files and notebook.zim are ignored",
        ),
    ],
)
def test_load(tmp_path, setup, want_names, want_depths):
    setup(tmp_path)
    nb = notebook.load(str(tmp_path))
    assert [p.name for p in nb.pages] == want_names
    if want_depths is not None:
        assert [p.depth for p in nb.pages] == want_depths


def test_create_page(tmp_path):
    path = notebook.create_page(str(tmp_path), "my page")
    # spaces sanitized to underscores
    assert path.endswith("my_page.txt")
    # file must have the Zim wiki header
    data = Path(path).read_text()
    assert data.startswith("Content-Type: text/x-zim-wiki")
    # duplicate name must fail
    with pytest.raises(FileExistsError):
        notebook.create_page(str(tmp_path), "my page")


def test_create_sub_page(tmp_path):
    write_file(tmp_path / "parent.txt")
    nb = notebook.load(str(tmp_path))
    parent = nb.pages[0]

    notebook.create_sub_page(parent, "child_a")
    assert parent.dir != ""
    assert (tmp_path / "parent" / "child_a.txt").exists()

    # second sub-page in the same parent (dir already exists)
    notebook.create_sub_page(parent, "child_b")
    assert (tmp_path / "parent" / "child_b.txt").exists()


def test_rename_leaf(tmp_path):
    write_file(tmp_path / "old.txt")
    nb = notebook.load(str(tmp_path))
    notebook.rename_page(nb.pages[0], "new")
    assert (tmp_path / "new.txt").exists()
    assert not (tmp_path / "old.txt").exists()


def test_rename_with_subdir(tmp_path):
    write_file(tmp_path / "parent.txt")
    write_file(tmp_path / "parent" / "child.txt")
    nb = notebook.load(str(tmp_path))
    notebook.rename_page(nb.pages[0], "renamed")
    assert (tmp_path / "renamed.txt").exists()
    assert (tmp_path / "renamed").is_dir()


def test_delete_leaf(tmp_path):
    write_file(tmp_path / "page.txt")
    nb = notebook.load(str(tmp_path))
    notebook.delete_page(nb.pages[0])
    assert not (tmp_path / "page.txt").exists()


def test_delete_with_subdir(tmp_path):
    write_file(tmp_path / "parent.txt")
    write_file(tmp_path / "parent" / "child.txt")
    nb = notebook.load(str(tmp_path))
    notebook.delete_page(nb.pages[0])
    assert not (tmp_path / "parent.txt").exists()
    assert not (tmp_path / "parent").exists()


def test_create_notebook(tmp_path):
    dir_ = tmp_path / "my-notebook"
    notebook.create_notebook(str(dir_))

    zim = (dir_ / "notebook.zim").read_text()
    for want in ("[Notebook]", "version=0.4", "name=my-notebook"):
        assert want in zim

    home = (dir_ / "Home.txt").read_text()
    assert home.startswith("Content-Type: text/x-zim-wiki")
    assert "====== Home ======" in home
