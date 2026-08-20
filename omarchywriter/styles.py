"""Theme selection and Qt palette application."""

from __future__ import annotations

import os

from PyQt6.QtGui import QColor, QPalette

from omarchywriter.config import ColorPalette, ColorSet


def detect_system_theme() -> str:
    """Best-effort system-mode detection for custom palettes."""
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Light:
                return "light"
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
    except Exception:
        pass
    return "light" if "light" in os.environ.get("GTK_THEME", "").lower() else "dark"


def palette_for_theme(colors: ColorSet, mode: str = "auto") -> ColorPalette:
    selected = colors.mode if mode == "auto" and colors.mode in {"dark", "light"} else mode
    if selected not in {"dark", "light"}:
        selected = detect_system_theme()
    return colors.light if selected == "light" else colors.dark


def apply_style(palette: ColorPalette) -> None:
    """Apply the shared Qt palette. Widget-specific styling stays in editor.py."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return
    qt_palette = app.palette()
    qt_palette.setColor(QPalette.ColorRole.Window, QColor(palette.bg))
    qt_palette.setColor(QPalette.ColorRole.WindowText, QColor(palette.fg))
    qt_palette.setColor(QPalette.ColorRole.Base, QColor(palette.bg))
    qt_palette.setColor(QPalette.ColorRole.Text, QColor(palette.fg))
    qt_palette.setColor(QPalette.ColorRole.Button, QColor(palette.status_bg))
    qt_palette.setColor(QPalette.ColorRole.ButtonText, QColor(palette.fg))
    qt_palette.setColor(QPalette.ColorRole.Highlight, QColor(palette.selection))
    qt_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(palette.fg))
    app.setPalette(qt_palette)
