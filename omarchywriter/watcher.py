"""Qt-backed file watching that survives normal and atomic saves."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


class FileWatcher:
    """Watch a file and debounce changes from common editor save strategies.

    QFileSystemWatcher drops a file watch when an editor replaces the file.
    Watching the nearest existing directory as well lets us reinstall the file
    watch after an atomic replacement or after a previously missing directory
    is created.
    """

    def __init__(self, path: Path, callback: Callable[[], None], debounce_ms: int = 150) -> None:
        from PyQt6.QtCore import QFileSystemWatcher, QTimer

        self._callback = callback
        self._path = path.expanduser()
        self._watcher = QFileSystemWatcher()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(callback)
        self._watcher.fileChanged.connect(self._schedule)
        self._watcher.directoryChanged.connect(self._schedule)
        self._install_paths()

    @property
    def path(self) -> Path:
        return self._path

    def set_path(self, path: Path) -> None:
        self._watcher.removePaths(self._watcher.files() + self._watcher.directories())
        self._path = path.expanduser()
        self._install_paths()

    def close(self) -> None:
        """Stop timers and release filesystem watches."""
        self._timer.stop()
        self._watcher.removePaths(self._watcher.files() + self._watcher.directories())

    def _nearest_existing_directory(self) -> Path:
        directory = self._path.parent
        while not directory.exists() and directory != directory.parent:
            directory = directory.parent
        return directory

    def _install_paths(self) -> None:
        watch_dir = self._nearest_existing_directory()
        if str(watch_dir) not in self._watcher.directories():
            self._watcher.addPath(str(watch_dir))
        if self._path.exists() and str(self._path) not in self._watcher.files():
            self._watcher.addPath(str(self._path))

    def _schedule(self, _changed_path: str) -> None:
        self._install_paths()
        self._timer.start()
