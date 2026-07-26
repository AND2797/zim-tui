"""Tests for the Zim markup renderer. Asserts on plain (unstyled) text."""

from __future__ import annotations

import pytest

from zim_tui.markup import render_inline, render_zim_content


def test_header_is_stripped():
    input_ = (
        "Content-Type: text/x-zim-wiki\n"
        "Wiki-Format: zim 0.6\n"
        "Creation-Date: 2024-01-01T00:00:00+00:00\n"
        "\n"
        "====== My Page ======\n"
        "Some content here."
    )
    out = render_zim_content(input_, 80).plain
    for forbidden in ("Content-Type", "Wiki-Format", "Creation-Date"):
        assert forbidden not in out
    assert "My Page" in out
    assert "Some content here." in out


@pytest.mark.parametrize(
    "input_, want_text, no_text",
    [
        ("====== Title One ======", "Title One", "======"),
        ("===== Title Two =====", "Title Two", "====="),
        ("==== Title Three ====", "Title Three", "===="),
        ("=== Title Four ===", "Title Four", "==="),
    ],
)
def test_headings(input_, want_text, no_text):
    out = render_zim_content(input_, 80).plain
    assert want_text in out
    assert no_text not in out


@pytest.mark.parametrize(
    "input_, contains, absent",
    [
        ("* list item", "list item", "* "),
        ("1. first", "first", ""),
        ("[ ] todo item", "todo item", "[ ]"),
        ("[x] done item", "done item", "[x]"),
        ("----", "─", "----"),
    ],
)
def test_structural(input_, contains, absent):
    out = render_zim_content(input_, 80).plain
    assert contains in out
    if absent:
        assert absent not in out


@pytest.mark.parametrize(
    "input_, contains, absent",
    [
        ("**bold text**", "bold text", "**"),
        ("//italic text//", "italic text", "//"),
        ("__under text__", "under text", "__"),
        ("[[PageName]]", "PageName", "[["),
        ("[[target|display label]]", "display label", "[["),
        ("[[target|display label]]", "", "target"),
        ("``some code``", "some code", "``"),
        ("just plain text", "just plain text", ""),
        ("**unclosed", "**unclosed", ""),
        ("**a** and //b//", "a", "**"),
    ],
)
def test_render_inline(input_, contains, absent):
    out = render_inline(input_).plain
    if contains:
        assert contains in out
    if absent:
        assert absent not in out
