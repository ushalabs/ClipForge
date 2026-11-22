#!/usr/bin/env bash
# ClipForge - one-click start for Mac and Linux.
# First run: checks Python and ffmpeg (installs them with Homebrew on a Mac when possible), sets up a private
# Python folder (.venv) and the packages. Every run: starts ClipForge and opens it in your browser.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say()  { printf "  %s\n" "$1"; }
fail() { printf "\n  \033[31m%s\033[0m\n\n" "$1"; exit 1; }
echo; say "=== ClipForge ==="; echo

if [ "$(uname)" = "Darwin" ] && [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
if [ "$(uname)" = "Darwin" ] && [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"; fi

find_python() {
  for p in python3.12 python3.11 python3.13 python3.10 python3; do
    if command -v "$p" >/dev/null 2>&1 &&
       "$p" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] < (3,14) else 1)' 2>/dev/null; then
      echo "$p"; return
    fi
  done
}

PY="$(find_python)"
if [ -z "$PY" ]; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    say "Python 3.10+ not found. Installing Python 3.12 with Homebrew..."
    brew install python@3.12
    PY="$(find_python)"
  fi
  [ -n "$PY" ] || {
    if [ "$(uname)" = "Darwin" ]; then
      open "https://www.python.org/downloads/release/python-3129/" 2>/dev/null || true
      fail "Install Python 3.12 from the page that just opened, then run this again."
    else
      fail "Python 3.10+ is needed. Install it (for example: sudo apt install python3 python3-venv), then run this again."
    fi
  }
fi
say "Python: $($PY --version)"

if ! command -v ffmpeg >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    say "ffmpeg not found. Installing it with Homebrew..."
    brew install ffmpeg
  elif [ "$(uname)" = "Darwin" ]; then
    say "ffmpeg not found. Install Homebrew from https://brew.sh then run: brew install ffmpeg"
  else
    say "ffmpeg not found. Install it with: sudo apt install ffmpeg"
  fi
fi

if [ ! -x .venv/bin/python ]; then
  say "Setting up (one time)..."
  "$PY" -m venv .venv || fail "Could not create the Python environment (on Linux: sudo apt install python3-venv)."
fi
HAS_GUI=0
if [ "${CLIPFORGE_BROWSER_ONLY:-0}" != "1" ] && [ -f requirements-desktop.txt ]; then
  if [ "$(uname)" = "Darwin" ] || [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    HAS_GUI=1
  fi
fi

HASH="$("$PY" -c "import hashlib,os; h=hashlib.sha256(open('requirements.txt','rb').read()); os.path.exists('requirements-desktop.txt') and '$HAS_GUI'=='1' and h.update(open('requirements-desktop.txt','rb').read()); print(h.hexdigest())")"
if [ ! -f .venv/requirements.sha ] || [ "$(cat .venv/requirements.sha)" != "$HASH" ]; then
  say "Installing packages (one time, a few minutes)..."
  .venv/bin/python -m pip install --upgrade pip --disable-pip-version-check -q
  if [ "$HAS_GUI" = "1" ]; then
    .venv/bin/python -m pip install -r requirements-desktop.txt --disable-pip-version-check || \
      .venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check || \
      fail "Installing packages failed. Check your internet connection and run this again."
  else
    .venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check || \
      fail "Installing packages failed. Check your internet connection and run this again."
  fi
  echo "$HASH" > .venv/requirements.sha
fi

echo
say "Starting ClipForge. The first start downloads the speech model (about 480 MB, once)."
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Already running? Then just open it. Port taken by another program? Then use the next free one.
open_url() { if command -v open >/dev/null 2>&1; then open "$1"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1"; fi; }
PORT="${CLIPFORGE_PORT:-8765}"
USE_DESKTOP=0
if [ "$HAS_GUI" = "1" ] && .venv/bin/python -c "import webview" 2>/dev/null; then
  USE_DESKTOP=1
fi
for p in $(seq "$PORT" $((PORT + 9))); do
  if .venv/bin/python -c "import sys,urllib.request; sys.exit(0 if b'ClipForge' in urllib.request.urlopen('http://127.0.0.1:$p/app', timeout=3).read() else 1)" 2>/dev/null; then
    if [ "$USE_DESKTOP" = "1" ]; then
      say "ClipForge is already running. Opening desktop window..."
      export CLIPFORGE_PORT="$p"
      exec .venv/bin/python -m studio.desktop --port "$p"
    fi
    say "ClipForge is already running (in another window). Opening it in your browser."
    open_url "http://127.0.0.1:$p/app"; exit 0
  fi
done
while ! .venv/bin/python -c "import socket,sys; s=socket.socket(); s.bind(('127.0.0.1',$PORT)); s.close()" 2>/dev/null; do
  say "Port $PORT is used by another program, trying $((PORT + 1))..."
  PORT=$((PORT + 1))
  [ "$PORT" -le 8800 ] || fail "No free port found between 8765 and 8800."
done
export CLIPFORGE_PORT="$PORT"
if [ "$USE_DESKTOP" = "1" ]; then
  say "Opening ClipForge desktop window..."
  exec .venv/bin/python -m studio.desktop --port "$PORT"
fi
say "Your browser opens by itself. Keep this window open while you use ClipForge; close it to stop."
echo
export CLIPFORGE_OPEN_BROWSER=1
exec .venv/bin/python -m studio.server
