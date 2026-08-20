"""Live configuration and theme reload orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from omarchywriter.config import (
    Config,
    ColorSet,
    load_colors,
    load_config,
    load_omarchy_colors,
)
from omarchywriter.paths import AppPaths
from omarchywriter.watcher import FileWatcher

ColorRenderer = Callable[[ColorSet, Config], None]
ConfigApplier = Callable[[Config], None]


def active_colors_path(config: Config, paths: AppPaths) -> Path:
    """Return the palette source selected by the current configuration."""
    return paths.custom_colors if config.theme.source == "custom" else paths.omarchy_colors


def load_active_colors(config: Config, paths: AppPaths) -> ColorSet:
    """Load the palette selected by a configuration snapshot."""
    if config.theme.source == "custom":
        return load_colors(paths.custom_colors)
    return load_omarchy_colors(paths.omarchy_colors)


class LiveReloadController:
    """Coordinate independent config and palette watchers.

    The controller owns no widgets. It only loads valid snapshots and delegates
    application to callbacks, so the editor can change without rewriting the
    file-loading layer.
    """

    def __init__(
        self,
        paths: AppPaths,
        config: Config,
        apply_config: ConfigApplier,
        render_colors: ColorRenderer,
        logger: logging.Logger | None = None,
        debounce_ms: int = 150,
    ) -> None:
        self.paths = paths
        self.config = config
        self._apply_config = apply_config
        self._render_colors = render_colors
        self._logger = logger or logging.getLogger("omarchywriter")
        self._config_watcher = FileWatcher(paths.config, self.reload_config, debounce_ms)
        self._color_watcher = FileWatcher(
            active_colors_path(config, paths),
            self.reload_colors,
            debounce_ms,
        )

    @property
    def watchers(self) -> tuple[FileWatcher, FileWatcher]:
        return self._config_watcher, self._color_watcher

    def reload_config(self) -> None:
        if not self.paths.config.exists():
            self._logger.warning("keeping the previous configuration; waiting for %s", self.paths.config)
            return
        try:
            updated = load_config(self.paths.config)
        except (OSError, ValueError) as error:
            self._logger.warning("keeping the previous configuration: %s", error)
            return

        self.config = updated
        self._apply_config(updated)
        new_color_path = active_colors_path(updated, self.paths)
        if self._color_watcher.path != new_color_path:
            self._color_watcher.set_path(new_color_path)
        self.reload_colors()

    def reload_colors(self) -> None:
        color_path = active_colors_path(self.config, self.paths)
        if not color_path.exists():
            self._logger.warning("keeping the previous colors; waiting for %s", color_path)
            return
        try:
            colors = load_active_colors(self.config, self.paths)
        except (OSError, ValueError) as error:
            self._logger.warning("keeping the previous colors: %s", error)
            return
        self._render_colors(colors, self.config)

    def close(self) -> None:
        self._config_watcher.close()
        self._color_watcher.close()
