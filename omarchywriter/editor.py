"""The OmarchyWriter window and Markdown editor widgets."""

from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QKeySequence,
    QPainter,
    QPalette,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QTextBlockFormat,
    QTextFormat,
    QTextOption,
    QSyntaxHighlighter,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from omarchywriter.config import ColorPalette, ColorSet, Config
from omarchywriter.styles import palette_for_theme


MARKDOWN_RULES = [
    (re.compile(r"^#{1,6}\s+.*"), "markdown_heading"),
    (re.compile(r"^(\*{3,}|-{3,}|_{3,})$"), "markdown_hr"),
    (re.compile(r"^>\s+.*"), "markdown_quote"),
    (re.compile(r"^\s*(?:[-*+]|\d+\.)\s+.*"), "markdown_list"),
    (re.compile(r"`[^`]+`"), "markdown_code"),
    (re.compile(r"\[[^\]]+\]\([^)]+\)"), "markdown_link"),
]


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QPlainTextEdit) -> None:
        super().__init__(parent.document())
        self._formats: dict[str, QTextCharFormat] = {}

    def set_palette(self, palette: ColorPalette) -> None:
        def make_format(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
            result = QTextCharFormat()
            result.setForeground(QColor(color))
            result.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
            result.setFontItalic(italic)
            return result

        self._formats = {
            "markdown_heading": make_format(palette.markdown_heading, bold=True),
            "markdown_code": make_format(palette.markdown_code),
            "markdown_quote": make_format(palette.markdown_quote, italic=True),
            "markdown_link": make_format(palette.markdown_link),
            "markdown_list": make_format(palette.markdown_list),
            "markdown_hr": make_format(palette.markdown_hr),
        }
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        for pattern, name in MARKDOWN_RULES:
            text_format = self._formats.get(name)
            if text_format is None:
                continue
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), text_format)


class Editor(QPlainTextEdit):
    path_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_file_path = ""
        self._palette: ColorPalette | None = None
        self._applied_editor_settings: tuple[object, ...] | None = None
        self._highlighter = MarkdownHighlighter(self)
        self.setAcceptDrops(True)
        # Keep the editor deliberately minimal: keyboard editing remains
        # available, but right-click must not open an extra context-menu GUI.
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setUndoRedoEnabled(True)
        self.cursorPositionChanged.connect(self._update_current_line)

    def set_path(self, path: str) -> None:
        self._current_file_path = path
        self.path_changed.emit(path)

    def get_path(self) -> str:
        return self._current_file_path

    def apply_config(self, config: Config) -> None:
        editor = config.editor
        settings = (
            editor.font,
            editor.font_size,
            editor.line_spacing,
            editor.tab_width,
            editor.show_line_numbers,
            editor.word_wrap,
            editor.paragraph_spacing,
            editor.cursor_width,
        )
        if settings == self._applied_editor_settings:
            return
        self._applied_editor_settings = settings
        font = QFont(editor.font, editor.font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(QFontMetrics(font).horizontalAdvance(" " * editor.tab_width))
        self.setCursorWidth(editor.cursor_width)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere if editor.word_wrap else QTextOption.WrapMode.NoWrap)
        block_format = QTextBlockFormat()
        block_format.setLineHeight(max(1, int(editor.line_spacing * 100)), QTextBlockLineHeightMode.value)
        block_format.setBottomMargin(editor.paragraph_spacing)
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        was_modified = self.document().isModified()
        cursor.mergeBlockFormat(block_format)
        self.document().setModified(was_modified)

    def apply_colors(self, palette: ColorPalette) -> None:
        self._palette = palette
        qt_palette = self.palette()
        qt_palette.setColor(QPalette.ColorRole.Base, QColor(palette.bg))
        qt_palette.setColor(QPalette.ColorRole.Text, QColor(palette.fg))
        qt_palette.setColor(QPalette.ColorRole.Highlight, QColor(palette.selection))
        qt_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(palette.fg))
        self.setPalette(qt_palette)
        self.setStyleSheet(
            f"QPlainTextEdit {{ background: {palette.bg}; color: {palette.fg}; border: none; padding: 8px; }}"
        )
        self._highlighter.set_palette(palette)
        self._update_current_line()

    def _update_current_line(self) -> None:
        if self._palette is None:
            return
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(self._palette.current_line))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            window = self.window()
            if isinstance(window, EditorWindow):
                window.load_file(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# Kept separate so this widget can be hidden instantly on a config change.
class LineNumberGutter(QFrame):
    def __init__(self, editor: Editor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self._palette: ColorPalette | None = None
        self.setFixedWidth(48)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        editor.updateRequest.connect(lambda *_: self.update())
        editor.blockCountChanged.connect(lambda _: self.update())
        editor.cursorPositionChanged.connect(self.update)

    def set_palette(self, palette: ColorPalette) -> None:
        self._palette = palette
        self.update()

    def paintEvent(self, event) -> None:
        if self._palette is None:
            return
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(self._palette.status_bg))
        painter.setPen(QColor(self._palette.line_number))
        painter.setFont(self._editor.font())
        block = self._editor.firstVisibleBlock()
        number = block.blockNumber() + 1
        top = self._editor.blockBoundingGeometry(block).translated(self._editor.contentOffset()).top()
        bottom = top + self._editor.blockBoundingRect(block).height()
        metrics = QFontMetrics(self._editor.font())
        while block.isValid() and top <= self.height():
            if block.isVisible() and bottom >= 0:
                painter.drawText(0, int(top), self.width() - 8, metrics.height(), Qt.AlignmentFlag.AlignRight, str(number))
            block = block.next()
            top = bottom
            bottom = top + self._editor.blockBoundingRect(block).height()
            number += 1


class StatusBar(QFrame):
    def __init__(self, editor: Editor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self._path_label = QLabel("No file")
        self._path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._info_label = QLabel("Ln 1, Col 1  |  0 words")
        layout.addWidget(self._path_label)
        layout.addWidget(self._info_label)
        self._editor = editor
        editor.path_changed.connect(self._set_path)
        editor.cursorPositionChanged.connect(self.update_info)
        editor.textChanged.connect(self.update_info)

    def apply_config(self, config: Config) -> None:
        font = QFont(config.gui.font, config.gui.font_size)
        self._path_label.setFont(font)
        self._info_label.setFont(font)

    def set_palette(self, palette: ColorPalette) -> None:
        self.setStyleSheet(f"QFrame {{ background: {palette.status_bg}; color: {palette.status_fg}; }}")

    def _set_path(self, path: str) -> None:
        self._path_label.setText(path or "No file")

    def update_info(self) -> None:
        cursor = self._editor.textCursor()
        words = len(self._editor.toPlainText().split())
        self._info_label.setText(f"Ln {cursor.blockNumber() + 1}, Col {cursor.positionInBlock() + 1}  |  {words} words")


QTextBlockLineHeightMode = QTextBlockFormat.LineHeightTypes.ProportionalHeight


class EditorWindow(QWidget):
    def __init__(self, config: Config, colors: ColorSet, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._config = config
        self._config_applied = False
        self._colors = colors
        self._palette = palette_for_theme(colors, config.theme.mode)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self.save_file)
        self.setWindowTitle("OmarchyWriter")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        content = QWidget(self)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.editor = Editor(content)
        self.gutter = LineNumberGutter(self.editor, content)
        content_layout.addWidget(self.gutter)
        content_layout.addWidget(self.editor)
        self.status_bar = StatusBar(self.editor, self)
        root.addWidget(content, 1)
        root.addWidget(self.status_bar)

        QShortcut(QKeySequence.StandardKey.Open, self, activated=self.open_file_dialog)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=self.save_file)
        self.apply_config(config)
        self.apply_colors(colors)

    def apply_config(self, config: Config) -> None:
        if self._config_applied and config == self._config:
            return
        self._config = config
        self._config_applied = True
        self.resize(config.gui.window_width, config.gui.window_height)
        if config.gui.center_on_screen:
            screen = QApplication.primaryScreen()
            if screen is not None:
                self.move(screen.availableGeometry().center() - self.rect().center())
        self.editor.apply_config(config)
        self.gutter.setVisible(config.editor.show_line_numbers)
        self.status_bar.setVisible(config.gui.show_status_bar)
        self.status_bar.apply_config(config)
        if config.behavior.auto_save:
            self._auto_save_timer.start(config.behavior.auto_save_interval * 1000)
        else:
            self._auto_save_timer.stop()

    def apply_colors(self, colors: ColorSet) -> None:
        self._colors = colors
        self._palette = palette_for_theme(colors, self._config.theme.mode)
        self.editor.apply_colors(self._palette)
        self.gutter.set_palette(self._palette)
        self.status_bar.set_palette(self._palette)

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown", "", "Markdown (*.md *.markdown *.txt);;All files (*)")
        if path:
            self.load_file(path)

    def load_file(self, path: str) -> None:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(self, "Could not open file", str(error))
            return
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.editor.set_path(path)
        self.setWindowTitle(f"OmarchyWriter — {Path(path).name}")

    def save_file(self) -> bool:
        path = self.editor.get_path()
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save Markdown", "", "Markdown (*.md);;All files (*)")
            if not path:
                return False
        try:
            Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(self, "Could not save file", str(error))
            return False
        self.editor.set_path(path)
        self.editor.document().setModified(False)
        self.setWindowTitle(f"OmarchyWriter — {Path(path).name}")
        return True

    def closeEvent(self, event) -> None:
        if self.editor.document().isModified() and self._config.behavior.confirm_quit:
            response = QMessageBox.question(self, "Discard unsaved changes?", "Your changes have not been saved.")
            if response != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()
