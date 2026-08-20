"""Static default color palettes (Python dict form).

Used as fallbacks when:
- color.toml does not define a section
- The app starts before any user config exists
"""

DARK_COLORS = {
    "bg": "#1a1b1e",
    "fg": "#d4d4d4",
    "cursor": "#569cd6",
    "selection": "#264f78",
    "line_number": "#404040",
    "current_line": "#2a2b2e",
    "markdown_heading": "#e6c384",
    "markdown_code": "#9cdcfe",
    "markdown_quote": "#6a9955",
    "markdown_link": "#569cd6",
    "markdown_list": "#ce9178",
    "markdown_hr": "#808080",
    "status_bg": "#1a1b1e",
    "status_fg": "#808080",
}

LIGHT_COLORS = {
    "bg": "#ffffff",
    "fg": "#1a1b1e",
    "cursor": "#000000",
    "selection": "#cce5ff",
    "line_number": "#a0a0a0",
    "current_line": "#f0f0f0",
    "markdown_heading": "#0000ff",
    "markdown_code": "#4444cc",
    "markdown_quote": "#4a7a3a",
    "markdown_link": "#0000ff",
    "markdown_list": "#cc0000",
    "markdown_hr": "#888888",
    "status_bg": "#ffffff",
    "status_fg": "#666666",
}
