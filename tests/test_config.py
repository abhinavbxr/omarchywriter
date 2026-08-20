from pathlib import Path

from omarchywriter.config import (
    CONFIG_DEFAULTS,
    init_user_config,
    load_config,
    load_omarchy_colors,
)


def test_init_creates_only_the_requested_app_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    colors_path = tmp_path / "colors.toml"

    init_user_config(config_path, colors_path)

    assert config_path.read_text(encoding="utf-8") == CONFIG_DEFAULTS
    assert colors_path.exists()


def test_config_values_are_loaded(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """[theme]
source = "custom"
mode = "light"
[editor]
font_size = 20
show_line_numbers = true
[gui]
window_width = 1200
[behavior]
auto_save = true
auto_save_interval = 12
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.theme.source == "custom"
    assert config.theme.mode == "light"
    assert config.editor.font_size == 20
    assert config.editor.show_line_numbers is True
    assert config.gui.window_width == 1200
    assert config.behavior.auto_save is True
    assert config.behavior.auto_save_interval == 12


def test_omarchy_palette_is_mapped_without_writing_source(tmp_path: Path) -> None:
    path = tmp_path / "colors.toml"
    source = """mode = \"light\"\nbackground = \"#faf4ed\"\nforeground = \"#575279\"\naccent = \"#56949f\"\nselection = \"#dfdad9\"\nred = \"#b4637a\"\nyellow = \"#ea9d34\"\norange = \"#cf8057\"\ngreen = \"#286983\"\ncyan = \"#d7827e\"\nblue = \"#56949f\"\nmuted = \"#cecacd\"\n"""
    path.write_text(source, encoding="utf-8")

    colors = load_omarchy_colors(path)

    assert colors.mode == "light"
    assert colors.light.bg == "#faf4ed"
    assert colors.light.markdown_heading == "#ea9d34"
    assert colors.light.markdown_quote == "#286983"
    assert path.read_text(encoding="utf-8") == source
