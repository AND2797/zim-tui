"""Dracula-ish colour palette and Rich style strings.

The same hex values are mirrored in ``app.tcss`` for widget-level styling; these
constants drive Rich-rendered content (the Zim markup preview) where CSS does
not reach.
"""

from __future__ import annotations

# Palette
COLOR_BG = "#282A36"  # background
COLOR_CURRENT_LINE = "#44475A"  # input-field background
COLOR_BORDER = "#888888"  # inactive panel border/title
COLOR_BORDER_ACTIVE = "#50FA7B"  # active panel border/title
COLOR_SELECTED = "#7D56F4"  # selected-row background (purple)
COLOR_SELECTED_FG = "#FFFFFF"  # selected-row foreground
COLOR_SUBTLE = "#555555"  # subtle grey (separators, hints, counts)
COLOR_ERROR = "#FF5555"  # error red
COLOR_SUCCESS = "#50FA7B"  # success / modal-border green
COLOR_WARNING = "#F1FA8C"  # warning yellow
COLOR_NORMAL = "#F8F8F2"  # normal foreground (off-white)
COLOR_HEADER = "#8BE9FD"  # cyan (H1, links)
COLOR_BOLD = "#FFB86C"  # orange (bold, H2, keys)

# Rich style strings for the markup renderer
STYLE_H1 = f"bold {COLOR_HEADER}"
STYLE_H2 = f"bold {COLOR_BOLD}"
STYLE_H3 = f"bold {COLOR_NORMAL}"
STYLE_H4 = f"bold {COLOR_NORMAL}"
STYLE_BOLD = f"bold {COLOR_BOLD}"
STYLE_ITALIC = f"italic {COLOR_SUBTLE}"
STYLE_UNDERLINE = f"underline {COLOR_NORMAL}"
STYLE_LINK = f"underline {COLOR_HEADER}"
STYLE_CODE = COLOR_SUCCESS
STYLE_SUBTLE = COLOR_SUBTLE
STYLE_SUCCESS = COLOR_SUCCESS
STYLE_NORMAL = COLOR_NORMAL
