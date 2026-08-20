# OmarchyWriter

A focused Markdown editor for Omarchy. It follows the active Omarchy theme in
real time while keeping every OmarchyWriter preference in one user-editable
directory.

OmarchyWriter is inspired by the distraction-free approach of Omawrite. It
never changes `/usr/share/omarchy`, `~/.config/omarchy`, Hyprland settings, or
the active Omarchy theme. It only reads the palette that Omarchy already
generates for the current theme.

## Features

- Markdown syntax highlighting and a distraction-free editor
- Open, save, drag-and-drop, line numbers, word count, and optional autosave
- Hot reload for every setting in `config.toml`
- Automatic palette updates after `omarchy theme set <theme>`
- Optional independent custom light and dark palettes

Theme and configuration changes are applied while the application is running;
you do not need to restart the editor.

## Install and run

Requires Python 3.10 or newer and a working Qt/Wayland desktop session.

### Install with the standalone script

Clone the repository and run the user-scoped installer:

```bash
git clone https://github.com/abhinavbxr/omarchywriter.git
cd omarchywriter
chmod +x install.sh
./install.sh
```

If you are installing a fork, replace the clone URL with your fork's URL. If
you already have a checkout, start at `cd omarchywriter`.

The script installs a private virtual environment under
`~/.local/share/omarchywriter/`, creates the `omarchywriter` command under
`~/.local/bin/`, and installs a user-level desktop entry. It does not require
`sudo` and does not modify Omarchy configuration. To skip the desktop entry:

```bash
./install.sh --no-desktop
```

To inspect prerequisites and planned paths without changing anything:

```bash
./install.sh --dry-run
```

The script warns if the `omarchy` command is not available, but it does not
block installation; theme integration becomes active when the Omarchy theme
file is present.

### Install manually

The installer is a convenience wrapper around the standard Python package
installation. A manual install is also supported:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
omarchywriter
```

To open a document directly:

```bash
omarchywriter ~/Documents/notes.md
```

For development, install the test tools too:

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

The package also supports `python -m omarchywriter` when run from a checkout
or installed environment.

### Modular layout

The application is intentionally split by responsibility:

- `paths.py` resolves XDG and Omarchy paths without performing writes.
- `config.py` contains configuration models, defaults, and TOML loaders.
- `watcher.py` contains the reusable Qt watcher for normal and atomic saves.
- `runtime.py` coordinates configuration/theme reloads through callbacks and
  does not know about editor widgets.
- `styles.py` selects and applies palettes.
- `editor.py` contains the Markdown editor and its widgets.
- `main.py` only bootstraps Qt and connects these modules.

This keeps theme sources, configuration formats, and UI components replaceable
without rewriting the reload coordinator.

### Optional desktop launcher

After installing the package, copy the included launcher into your user
applications directory:

```bash
install -Dm644 omawrite.desktop ~/.local/share/applications/omarchywriter.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

This is a user-level desktop entry; it does not alter Omarchy configuration.

## Configuration

On first launch the app creates only these files:

```text
~/.config/omarchywriter/config.toml
~/.config/omarchywriter/colors.toml
```

Edit and save `config.toml`; changes take effect immediately. If the file is
temporarily invalid while editing, the running app keeps the last valid
configuration and prints a short error to the terminal instead of crashing.
This also works with editors that save by writing a temporary file and
atomically replacing `config.toml`.

```toml
[theme]
# Follow Omarchy's active theme. This is the default and is read-only.
source = "omarchy"
# For custom themes: "auto", "dark", or "light".
mode = "auto"

[editor]
font = "Iosevka"
font_size = 14
line_spacing = 1.2
tab_width = 4
show_line_numbers = false
word_wrap = true
paragraph_spacing = 0
cursor_width = 2

[gui]
font = "Iosevka"
font_size = 12
window_width = 900
window_height = 700
show_status_bar = true
center_on_screen = true

[behavior]
auto_save = false
# Seconds. Autosave operates only after opening or saving a file.
auto_save_interval = 5
confirm_quit = true
```

All listed options are active. `Ctrl+O` opens a document and `Ctrl+S` saves
it. To change a setting, edit `config.toml` in another editor, save it, and
watch the running OmarchyWriter window update.

## Omarchy theme integration

With `theme.source = "omarchy"`, the app reads:

```text
~/.local/state/omarchy/current/theme/colors.toml
```

Omarchy atomically replaces that file when a theme changes. OmarchyWriter
watches both it and its parent directory, so it follows a normal
`omarchy theme set <theme-name>` change without restarting. The integration is
strictly read-only: OmarchyWriter does not install hooks, write symlinks, or
modify the active theme. If the file is briefly unavailable or invalid during
the replacement, the last valid palette remains active until the next valid
theme file is available.

On an Omarchy system, verify the behavior manually:

```bash
omarchy theme set <theme-name>
```

The editor should update its background, foreground, cursor, selection,
syntax-highlighting, line-number, and status-bar colors while it remains open.

## Custom palette

To use a palette independent of Omarchy, set this in `config.toml`:

```toml
[theme]
source = "custom"
mode = "dark"
```

Then edit `~/.config/omarchywriter/colors.toml`. It contains `[dark]` and
`[light]` sections and hot-reloads on save. Switch back to `source =
"omarchy"` at any time to resume following Omarchy.

## Dry-run verification

The project can be checked without changing Omarchy or opening a visible
window. From the project directory:

```bash
python -m pip install -e '.[dev]'
env QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= python -m pytest
python -m compileall -q omarchywriter tests
```

The tests cover configuration parsing, Omarchy color mapping without writing
the source file, normal and atomic-save file watching, live configuration
application, live Omarchy palette replacement, source switching, and invalid
configuration recovery. The latest verification completed with 9 tests
passing on 2026-08-20.

For a launch smoke check in a headless environment:

```bash
env QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= timeout 3s python -m omarchywriter
```

The command is expected to end with a timeout because the GUI event loop is
still running; absence of a Python traceback before the timeout confirms that
startup completed. On a real desktop session, use `omarchywriter` instead.

## Development

```bash
python -m pytest
python -m compileall -q omarchywriter
```

The test suite includes configuration, Omarchy palette mapping, normal and
atomic-save watcher coverage, live configuration reload, live theme reload,
and headless Qt window smoke coverage.

## Safety and scope

OmarchyWriter writes only its own files under `~/.config/omarchywriter/` and
the Markdown files you explicitly save. It reads Omarchy's active palette from
`~/.local/state/omarchy/current/theme/colors.toml`; it does not modify
`~/.config/omarchy`, Hyprland configuration, `/usr/share/omarchy`, or the
active Omarchy theme.
