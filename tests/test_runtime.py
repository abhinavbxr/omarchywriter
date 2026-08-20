import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "")

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from omarchywriter.config import ColorSet, Config, load_config, load_omarchy_colors
from omarchywriter.editor import EditorWindow
from omarchywriter.paths import AppPaths
from omarchywriter.runtime import LiveReloadController


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths(
        config=tmp_path / "config" / "config.toml",
        custom_colors=tmp_path / "config" / "colors.toml",
        state_dir=tmp_path / "state",
        omarchy_colors=tmp_path / "state" / "omarchy" / "current" / "theme" / "colors.toml",
    )


def test_controller_applies_saved_config_and_switches_palette_source(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    paths = _paths(tmp_path)
    paths.config.parent.mkdir(parents=True)
    paths.omarchy_colors.parent.mkdir(parents=True)
    paths.config.write_text(
        """[theme]\nsource = \"omarchy\"\n\n[editor]\nfont_size = 14\nshow_line_numbers = false\n\n[gui]\nshow_status_bar = true\ncenter_on_screen = false\n""",
        encoding="utf-8",
    )
    paths.omarchy_colors.write_text(
        'mode = "dark"\nbackground = "#101010"\nforeground = "#eeeeee"\naccent = "#ff0000"\n',
        encoding="utf-8",
    )
    config = load_config(paths.config)
    window = EditorWindow(config, load_omarchy_colors(paths.omarchy_colors))
    rendered: list[str] = []

    def render_colors(colors: ColorSet, updated_config: Config) -> None:
        rendered.append(colors.dark.bg)
        window.apply_colors(colors)

    controller = LiveReloadController(paths, config, window.apply_config, render_colors, debounce_ms=25)
    replacement = tmp_path / "config.new"
    replacement.write_text(
        """[theme]\nsource = \"custom\"\nmode = \"dark\"\n\n[editor]\nfont = \"DejaVu Sans Mono\"\nfont_size = 20\nshow_line_numbers = true\n\n[gui]\nshow_status_bar = false\ncenter_on_screen = false\n""",
        encoding="utf-8",
    )
    paths.custom_colors.write_text(
        """[dark]\nbg = \"#202020\"\nfg = \"#dddddd\"\ncursor = \"#00ff00\"\n""",
        encoding="utf-8",
    )
    replacement.replace(paths.config)
    QTest.qWait(300)

    assert controller.config.theme.source == "custom"
    assert controller.watchers[1].path == paths.custom_colors
    assert window.editor.font().family() == "DejaVu Sans Mono"
    assert window.editor.font().pointSize() == 20
    assert window.gutter.isHidden() is False
    assert window.status_bar.isHidden() is True
    assert rendered[-1] == "#202020"
    controller.close()
    window.close()
    app.processEvents()


def test_controller_keeps_last_valid_config_on_invalid_save(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])
    paths = _paths(tmp_path)
    paths.config.parent.mkdir(parents=True)
    paths.omarchy_colors.parent.mkdir(parents=True)
    paths.config.write_text("[editor]\nfont_size = 14\n", encoding="utf-8")
    paths.omarchy_colors.write_text('mode = "dark"\n', encoding="utf-8")
    config = load_config(paths.config)
    window = EditorWindow(config, load_omarchy_colors(paths.omarchy_colors))
    controller = LiveReloadController(
        paths,
        config,
        window.apply_config,
        lambda colors, updated_config: window.apply_colors(colors),
        debounce_ms=25,
    )

    replacement = tmp_path / "invalid-config.new"
    replacement.write_text("[editor\nfont_size = 99\n", encoding="utf-8")
    replacement.replace(paths.config)
    QTest.qWait(300)

    assert controller.config.editor.font_size == 14
    assert window.editor.font().pointSize() == 14
    controller.close()
    window.close()
    app.processEvents()
