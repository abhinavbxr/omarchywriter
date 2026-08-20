# Changelog

## 1.1.0 - 2026-08-20

- Removed the editor's right-click context-menu GUI while keeping keyboard
  cut, copy, and paste available.
- Changed the generated defaults to the simpler OmarchyWriter 1.1 settings:
  Iosevka 12 editor text, line numbers enabled, word wrap disabled, 1100x700
  window, GUI font size 9, and autosave enabled every 5 seconds.
- Added the `gui.show_tab_bar` configuration key, defaulting to `false`.
- Added safe migration for existing configuration files. Old generated values
  are updated, while customized values are preserved.
- Expanded configuration documentation and documented the upgrade procedure.
