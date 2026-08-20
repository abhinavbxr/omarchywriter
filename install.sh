#!/usr/bin/env bash

# Install OmarchyWriter for the current user.
# The installer never uses sudo and never edits Omarchy configuration.

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
readonly BIN_HOME="${XDG_BIN_HOME:-${HOME}/.local/bin}"
readonly APPLICATIONS_DIR="${DATA_HOME}/applications"
readonly INSTALL_DIR="${DATA_HOME}/omarchywriter"
readonly VENV_DIR="${INSTALL_DIR}/venv"
readonly APP_BIN="${VENV_DIR}/bin/omarchywriter"
readonly DESKTOP_FILE="${APPLICATIONS_DIR}/omarchywriter.desktop"

install_desktop=true
dry_run=false

usage() {
    cat <<'EOF'
Usage: ./install.sh [--no-desktop] [--dry-run]

Install OmarchyWriter for the current user in an isolated virtual environment.

Options:
  --no-desktop  Do not install the user-level desktop entry.
  --dry-run     Check prerequisites and print planned paths without installing.
  -h, --help    Show this help message.
EOF
}

die() {
    printf 'install.sh: error: %s\n' "$*" >&2
    exit 1
}

for argument in "$@"; do
    case "$argument" in
        --no-desktop)
            install_desktop=false
            ;;
        --dry-run)
            dry_run=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            die "unknown option: $argument"
            ;;
    esac
done

command -v python3 >/dev/null 2>&1 || die "python3 is required"

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    die "Python 3.10 or newer is required"
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    die "the Python venv module is required; install your distribution's python-venv package"
fi

if ! command -v omarchy >/dev/null 2>&1; then
    printf 'install.sh: warning: omarchy was not found in PATH; theme integration will activate on Omarchy.\n' >&2
fi

if [[ "$dry_run" == true ]]; then
    printf 'Dry run: prerequisites are available. No files were changed.\n'
    printf 'Virtual environment: %s\n' "$VENV_DIR"
    printf 'Command link: %s\n' "$BIN_HOME/omarchywriter"
    if [[ "$install_desktop" == true ]]; then
        printf 'Desktop entry: %s\n' "$DESKTOP_FILE"
    else
        printf 'Desktop entry: skipped\n'
    fi
    exit 0
fi

mkdir -p "$INSTALL_DIR" "$BIN_HOME"
python3 -m venv "$VENV_DIR"

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install --upgrade "$SCRIPT_DIR"

launcher="$BIN_HOME/omarchywriter"
if [[ -e "$launcher" && ! -L "$launcher" ]]; then
    die "$launcher already exists and is not a symbolic link; remove it or choose another XDG_BIN_HOME"
fi
ln -sfn "$APP_BIN" "$launcher"

if [[ "$install_desktop" == true ]]; then
    mkdir -p "$APPLICATIONS_DIR"
    desktop_tmp="$(mktemp)"
    cleanup() {
        rm -f -- "$desktop_tmp"
    }
    trap cleanup EXIT

    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == Exec=* ]]; then
            printf 'Exec="%s" %%F\n' "$APP_BIN"
        else
            printf '%s\n' "$line"
        fi
    done < "$SCRIPT_DIR/omawrite.desktop" > "$desktop_tmp"
    install -Dm644 "$desktop_tmp" "$DESKTOP_FILE"

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 ||
            printf 'install.sh: warning: could not update the desktop database.\n' >&2
    fi
fi

printf '\nOmarchyWriter installed successfully.\n'
printf 'Command: %s\n' "$launcher"
printf 'Run: %s\n' "$launcher"
printf 'If needed, add %s to PATH for shell use.\n' "$BIN_HOME"
if [[ "$install_desktop" == true ]]; then
    printf 'Desktop entry: %s\n' "$DESKTOP_FILE"
fi
