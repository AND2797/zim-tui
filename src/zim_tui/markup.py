"""Zim wiki markup to Rich Text.

Block rules are matched top to bottom in a fixed order; inline rules scan for
two-character delimiters and fall back to a single codepoint (Python ``str`` is
codepoint-based, so multi-byte characters are never split).
"""

from __future__ import annotations

from rich.text import Text

from . import styles


def render_zim_content(content: str, width: int) -> Text:
    """Convert Zim markup to a styled Rich Text, skipping the file header."""
    result = Text()
    in_header = True  # skip the file-level header lines
    first = True

    for line in content.split("\n"):
        if in_header:
            if (
                line.startswith("Content-Type:")
                or line.startswith("Wiki-Format:")
                or line.startswith("Creation-Date:")
            ):
                continue
            in_header = False

        if not first:
            result.append("\n")
        first = False
        result.append_text(render_line(line, width))

    return result


def render_line(line: str, width: int) -> Text:
    """Render a single source line to styled Text."""
    # H1: ====== Title ======
    if line.startswith("====== ") and line.endswith(" ======"):
        return Text(line[7:-7], style=styles.STYLE_H1)
    # H2: ===== Title ===== (with an underline separator)
    if line.startswith("===== ") and line.endswith(" ====="):
        separator = "─" * min(width - 2, 60)
        text = Text(line[6:-6], style=styles.STYLE_H2)
        text.append("\n")
        text.append(separator, style=styles.STYLE_SUBTLE)
        return text
    # H3: ==== Title ====
    if line.startswith("==== ") and line.endswith(" ===="):
        return Text(line[5:-5], style=styles.STYLE_H3)
    # H4: === Title ===
    if line.startswith("=== ") and line.endswith(" ==="):
        return Text(line[4:-4], style=styles.STYLE_H4)
    # Bullet list: "* item" or "\t* item" (single leading tab only)
    if line.startswith("* ") or line.startswith("\t* "):
        indent = "  " * line.count("\t")
        text = line.lstrip("\t")
        text = text[2:] if text.startswith("* ") else text
        out = Text(indent)
        out.append("•", style=styles.STYLE_SUBTLE)
        out.append(" ")
        out.append_text(render_inline(text))
        return out
    # Numbered list: "1. item" (single leading digit 1-9)
    if len(line) > 2 and "1" <= line[0] <= "9" and line[1] == ".":
        out = Text(line[0] + ".", style=styles.STYLE_SUBTLE)
        out.append(" ")
        out.append_text(render_inline(line[2:]))
        return out
    # Unchecked checkbox: "[ ] item"
    if line.startswith("[ ] "):
        out = Text("☐", style=styles.STYLE_SUBTLE)
        out.append(" ")
        out.append_text(render_inline(line[4:]))
        return out
    # Checked checkbox: "[x] item" / "[X] item" (text greyed out)
    if line.startswith("[x] ") or line.startswith("[X] "):
        out = Text("☑", style=styles.STYLE_SUCCESS)
        out.append(" ")
        out.append(render_inline(line[4:]).plain, style=styles.STYLE_SUBTLE)
        return out
    # Separator line
    if line == "----" or line == "---":
        return Text("─" * min(width - 2, 60), style=styles.STYLE_SUBTLE)
    # Code-block marker
    if line.startswith("''"):
        return Text(line, style=styles.STYLE_SUBTLE)
    return render_inline(line)


def render_inline(s: str) -> Text:
    """Render inline markup: **bold**, //italic//, __underline__, [[links]], ``code``."""
    result = Text()
    i = 0
    n = len(s)
    while i < n:
        if i + 1 < n:
            two = s[i : i + 2]
            if two == "**":
                end = s.find("**", i + 2)
                if end >= 0:
                    result.append(s[i + 2 : end], style=styles.STYLE_BOLD)
                    i = end + 2
                    continue
            elif two == "//":
                end = s.find("//", i + 2)
                if end >= 0:
                    result.append(s[i + 2 : end], style=styles.STYLE_ITALIC)
                    i = end + 2
                    continue
            elif two == "__":
                end = s.find("__", i + 2)
                if end >= 0:
                    result.append(s[i + 2 : end], style=styles.STYLE_UNDERLINE)
                    i = end + 2
                    continue
            elif two == "[[":
                end = s.find("]]", i + 2)
                if end >= 0:
                    link = s[i + 2 : end]
                    pipe = link.find("|")
                    display = link[pipe + 1 :] if pipe >= 0 else link
                    result.append(display, style=styles.STYLE_LINK)
                    i = end + 2
                    continue
            elif two == "``":
                end = s.find("``", i + 2)
                if end >= 0:
                    result.append(s[i + 2 : end], style=styles.STYLE_CODE)
                    i = end + 2
                    continue
        result.append(s[i])
        i += 1
    return result
