# zim-tui

A fast terminal UI for [Zim](https://zim-wiki.org) notebooks. Browse, search, and edit your notes without leaving the terminal — while staying fully compatible with the Zim desktop app.

Built with [Textual](https://textual.textualize.io/).

## Features

- **Page tree** — collapsible hierarchy, keyboard navigation
- **Live preview** — rendered Zim markup (headings, bold, italic, underline, lists, checkboxes, links, code, rules)
- **Search** — search page names (`/`) or grep content (`ctrl+f`), with an inline preview
- **Full editing** — opens pages in `$EDITOR` (default: vim)
- **Notebook switcher** — manage multiple notebooks, persistent across sessions
- **Create notebooks** — new notebooks are fully compatible with the Zim GUI
- **Panel navigation** — numbered panels (`[1]`/`[2]`/`[3]`) switchable by keyboard or mouse
- **Word wrap** — long lines in the preview wrap to fit the panel width
- **Modal overlays** — all input prompts and confirmations appear as floating panels

## Limitations

- **No file watching** — changes made by the Zim desktop app or another editor won't appear until you restart the TUI.
- **No image or table rendering** — images are not displayed; Zim tables are shown as raw markup.
- **No page move** — moving a page to a different section isn't wired to the UI yet (use the Zim GUI for this).
- **macOS / Linux only** — not tested on Windows.

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (for development / running from source)
- `rg` (ripgrep) — for content search
- `$EDITOR` set, or vim in `$PATH`

## Install & run

From source with `uv`:

```bash
git clone <repo-url> zim-tui
cd zim-tui
uv sync

# Open your default Zim notebook (~/Projects/zim-notes)
uv run zim-tui

# Open a specific notebook
uv run zim-tui /path/to/notebook
```

Or install the console script into a tool environment:

```bash
uv tool install .
zim-tui /path/to/notebook
```

The notebook path defaults to `~/Projects/zim-notes`. You can override it with a CLI argument or switch notebooks inside the TUI.

## Keybindings

| Key | Action |
|-----|--------|
| `j / k` | Move down / up |
| `enter` / `o` | Open page in editor |
| `space / tab` | Collapse / expand |
| `n / N` | New page / sub-page |
| `r` | Rename page |
| `d` | Delete page |
| `/` | Search page names |
| `ctrl+f` | Search page content |
| `f` | Follow link (in preview) |
| `1 / 2 / 3` | Focus notebooks / pages / preview |
| `?` | Help (context-sensitive) |
| `q` | Quit |

Press `?` from any panel for the full keybinding list for that panel.

## Notebook compatibility

Notebooks created by zim-tui are valid Zim notebooks — they include the standard `notebook.zim` config file and a `Home.txt` starting page. You can open them in the Zim desktop app at any time.

## Demo notebook

A sample notebook is included at `demo-notebook/` to try out the TUI and see how various markup elements render:

```bash
uv run zim-tui demo-notebook
```

## Development

Layout:

```
src/zim_tui/
  __main__.py        entry point (CLI arg, launches the app)
  notebook.py        filesystem I/O — no UI (Page, Notebook, create/delete/rename/...)
  config.py          persistent list of known notebooks (JSON)
  markup.py          Zim markup → Rich Text
  search.py          link extraction, name filtering, ripgrep content search
  state.py           pure tree/navigation state (visible pages, collapse, link resolution)
  styles.py          Dracula palette + Rich style strings
  app.py             the Textual App: layout, actions, message wiring
  app.tcss           widget styling (mirrors styles.py)
  widgets/           tree, notebooks, preview panels + status bar
  screens/           input / confirm / help / link-pick / search modals
```

Run the tests:

```bash
uv run pytest
```

The suite covers the pure-logic layers (notebook I/O, config, markup, search, tree state) plus headless Textual smoke and action tests driven through the app's `Pilot`.
