"""Application entry point."""

from __future__ import annotations

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from omarchywriter.config import (
    init_user_config,
    load_config,
)
from omarchywriter.editor import EditorWindow
from omarchywriter.paths import AppPaths
from omarchywriter.runtime import LiveReloadController, load_active_colors
from omarchywriter.styles import apply_style, palette_for_theme


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("OmarchyWriter")
    app.setOrganizationName("OmarchyWriter")
    app.setQuitOnLastWindowClosed(True)

    paths = AppPaths.from_environment()
    init_user_config(paths.config, paths.custom_colors)

    config = load_config(paths.config)
    colors = load_active_colors(config, paths)
    apply_style(palette_for_theme(colors, config.theme.mode))
    window = EditorWindow(config, colors)

    def render_colors(updated_colors, updated_config) -> None:
        apply_style(palette_for_theme(updated_colors, updated_config.theme.mode))
        window.apply_colors(updated_colors)

    live_reload = LiveReloadController(
        paths,
        config,
        window.apply_config,
        render_colors,
    )
    app.aboutToQuit.connect(live_reload.close)

    # A file argument is useful for desktop-file MIME handling and shell use.
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        window.load_file(str(Path(sys.argv[1]).expanduser()))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
