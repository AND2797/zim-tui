"""Tests for the persistent notebook-list config."""

from __future__ import annotations

import pytest

from zim_tui import config


@pytest.fixture
def point_config_at(tmp_path, monkeypatch):
    """Redirect the config dir into a temp HOME / XDG_CONFIG_HOME."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    # macOS UserConfigDir path stub, harmless elsewhere.
    (tmp_path / "Library" / "Application Support").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_load_missing(point_config_at):
    cfg = config.load()
    assert cfg.notebooks == []


def test_save_and_load(point_config_at):
    want = ["/a/b/notes", "/c/d/work"]
    config.save(config.Config(notebooks=want))
    got = config.load()
    assert got.notebooks == want


def test_add_notebook(point_config_at):
    config.add_notebook("/path/one")
    config.add_notebook("/path/two")
    config.add_notebook("/path/one")  # duplicate — should not appear twice

    cfg = config.load()
    assert cfg.notebooks == ["/path/one", "/path/two"]


def test_save_creates_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "nested" / "deep" / ".config"))
    config.save(config.Config(notebooks=["/nb"]))
    cfg = config.load()
    assert cfg.notebooks == ["/nb"]
