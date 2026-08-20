import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from omarchywriter.config import ColorSet, Config, FileWatcher, load_config, load_omarchy_colors
from omarchywriter.editor import EditorWindow
from omarchywriter.styles import apply_style, palette_for_theme


def test_window_applies_live_configuration() -> None:
    app = QApplication.instance() or QApplication([])
    config = Config()
    config.editor.font_size = 18
    config.editor.show_line_numbers = True
    config.gui.window_width = 1000
    config.gui.window_height = 600
    config.gui.show_status_bar = False
    config.gui.center_on_screen = False
    config.behavior.confirm_quit = False

    window = EditorWindow(config, ColorSet())

    assert window.editor.font().pointSize() == 18
    assert window.gutter.isHidden() is False
    assert window.status_bar.isHidden() is True
    assert window.size().width() == 1000
    assert window.size().height() == 600
    window.close()
    app.processEvents()


def test_file_watcher_survives_an_atomic_save(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    path = tmp_path / "config.toml"
    path.write_text("first", encoding="utf-8")
    changed: list[bool] = []
    watcher = FileWatcher(path, lambda: changed.append(True), debounce_ms=25)

    replacement = tmp_path / "config.toml.new"
    replacement.write_text("second", encoding="utf-8")
    replacement.replace(path)
    QTest.qWait(300)

    assert changed
    assert watcher.path == path
    app.processEvents()


def test_saved_config_is_reloaded_and_applied(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """[editor]
font = "Iosevka"
font_size = 14
show_line_numbers = false

[gui]
show_status_bar = true
center_on_screen = false
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    window = EditorWindow(config, ColorSet())

    def reload_config() -> None:
        window.apply_config(load_config(config_path))

    watcher = FileWatcher(config_path, reload_config, debounce_ms=25)
    replacement = tmp_path / "config.toml.new"
    replacement.write_text(
        """[editor]
font = "DejaVu Sans Mono"
font_size = 20
show_line_numbers = true

[gui]
show_status_bar = false
center_on_screen = false
""",
        encoding="utf-8",
    )
    replacement.replace(config_path)
    QTest.qWait(300)

    assert window.editor.font().family() == "DejaVu Sans Mono"
    assert window.editor.font().pointSize() == 20
    assert window.gutter.isHidden() is False
    assert window.status_bar.isHidden() is True
    assert watcher.path == config_path
    window.close()
    app.processEvents()


def test_theme_change_reloads_the_current_omarchy_palette(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    theme_dir = tmp_path / "omarchy" / "current" / "theme"
    theme_dir.mkdir(parents=True)
    theme_path = theme_dir / "colors.toml"
    theme_path.write_text(
        'mode = "dark"\nbackground = "#101010"\nforeground = "#eeeeee"\naccent = "#ff0000"\n',
        encoding="utf-8",
    )
    colors = load_omarchy_colors(theme_path)
    window = EditorWindow(Config(), colors)

    def reload_theme() -> None:
        updated = load_omarchy_colors(theme_path)
        apply_style(palette_for_theme(updated, "auto"))
        window.apply_colors(updated)

    watcher = FileWatcher(theme_path, reload_theme, debounce_ms=25)
    replacement = theme_dir / "colors.toml.new"
    replacement.write_text(
        'mode = "dark"\nbackground = "#202020"\nforeground = "#dddddd"\naccent = "#00ff00"\n',
        encoding="utf-8",
    )
    replacement.replace(theme_path)
    QTest.qWait(300)

    assert window.editor._palette is not None
    assert window.editor._palette.bg == "#202020"
    assert window.editor._palette.fg == "#dddddd"
    assert window.editor._palette.cursor == "#00ff00"
    assert watcher.path == theme_path
    window.close()
    app.processEvents()
