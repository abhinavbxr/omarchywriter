"""Filesystem locations used by OmarchyWriter.

Keeping path resolution in one small module makes the rest of the application
easy to test with temporary directories and prevents accidental writes to
Omarchy-owned files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _xdg_path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default))).expanduser()


@dataclass(frozen=True)
class AppPaths:
    """All paths OmarchyWriter needs at runtime."""

    config: Path
    custom_colors: Path
    state_dir: Path
    omarchy_colors: Path

    @classmethod
    def from_environment(cls) -> "AppPaths":
        config_dir = _xdg_path("XDG_CONFIG_HOME", Path.home() / ".config") / "omarchywriter"
        state_dir = _xdg_path("XDG_STATE_HOME", Path.home() / ".local" / "state")
        return cls(
            config=config_dir / "config.toml",
            custom_colors=config_dir / "colors.toml",
            state_dir=state_dir,
            omarchy_colors=state_dir / "omarchy" / "current" / "theme" / "colors.toml",
        )

    @property
    def config_dir(self) -> Path:
        return self.config.parent
