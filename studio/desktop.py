"""Native desktop window wrapper for ClipForge using pywebview and optional system tray."""
import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

LOADING_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ClipForge</title>
<style>
*{box-sizing:border-box}
html,body{height:100%;margin:0;background:#0F1012;color:#F4F4F5;font:15px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}
body{display:flex;align-items:center;justify-content:center}
.wrap{display:flex;flex-direction:column;align-items:center;gap:18px;text-align:center;padding:24px;max-width:420px}
.mark{width:64px;height:64px;display:block}
.title{font-size:20px;font-weight:700;letter-spacing:-.02em;color:#F4F4F5}
.pill{display:inline-block;padding:4px 12px;border-radius:6px;background:#16171A;border:1px solid #26272B;color:#38BDF8;font-size:13px;font-weight:600}
</style>
</head>
<body>
<div class="wrap">
  <svg class="mark" viewBox="0 0 220 220" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <rect width="220" height="220" rx="56" fill="#0B1116"/>
    <rect x="50" y="50" width="34" height="120" rx="10" fill="#0EA5E9"/>
    <path d="M100 62Q100 50 111 56L170 100Q180 110 170 120L111 164Q100 170 100 158Z" fill="#FFFFFF"/>
  </svg>
  <div class="title">ClipForge</div>
  <div class="pill" id="status">Starting ClipForge...</div>
</div>
</body>
</html>
"""


def port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if a TCP socket can bind to (host, port)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def is_clipforge_running(port: int, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
    """Return True if an existing ClipForge server is already answering on port."""
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/app", timeout=timeout) as r:
            body = r.read(65536)
        return r.status == 200 and b"ClipForge" in body
    except Exception:  # noqa: BLE001
        return False


def find_port(preferred: int = 8765, host: str = "127.0.0.1") -> tuple[int, bool]:
    """Find a running ClipForge instance to reuse, or an available local port.

    Returns (port, already_running).
    """
    for p in range(preferred, preferred + 10):
        if is_clipforge_running(p, host=host):
            return p, True
    for p in range(preferred, 8801):
        if port_free(p, host=host):
            return p, False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        return int(s.getsockname()[1]), False
    finally:
        s.close()


def wait_ready(port: int, host: str = "127.0.0.1", timeout: float = 60.0, stop_check=None) -> bool:
    """Poll /healthz until the local server answers HTTP 200, times out, or stop_check returns True."""
    deadline = time.monotonic() + timeout
    url = f"http://{host}:{port}/healthz"
    while time.monotonic() < deadline:
        if stop_check and stop_check():
            return False
        try:
            with urllib.request.urlopen(url, timeout=1.5) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.25)
    return False


class DesktopApi:
    """Bridge exposed to the page via window.pywebview.api."""

    def open_external(self, url: str) -> bool:
        clean = str(url or "").strip()
        if not clean:
            return False
        parsed = urllib.parse.urlparse(clean)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            return False
        return bool(webbrowser.open(clean))

    def is_desktop(self) -> bool:
        return True


def build_tray_icon():
    """Create a crisp 64x64 ClipForge icon with Pillow, or None if Pillow is unavailable."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=16, fill=(11, 17, 22, 255))
    d.rounded_rectangle([14, 14, 24, 50], radius=3, fill=(14, 165, 233, 255))
    d.polygon([(30, 16), (52, 32), (30, 48)], fill=(255, 255, 255, 255))
    return img


def _parse_args(argv=None):
    p = argparse.ArgumentParser(prog="clipforge-desktop", description="ClipForge Desktop Application")
    p.add_argument("--port", type=int, default=None, help="Preferred local port (default: 8765)")
    p.add_argument("--fallback-browser", action="store_true", help="Open in the default browser if pywebview is unavailable")
    p.add_argument("--tray-on-close", action="store_true", help="Minimize to system tray when closing the window")
    return p.parse_args(argv)


def _ensure_stdio():
    """Ensure stdout/stderr are writable streams when launched without a console (console=False / pythonw)."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) if sys.platform == "win32" else Path.home()
    log_path = base / "ClipForge" / "desktop.log"
    stream = None
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stream = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        try:
            stream = open(os.devnull, "w", encoding="utf-8")
        except OSError:
            return
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


def main(argv=None):
    _ensure_stdio()
    args = _parse_args(argv)
    try:
        import webview
    except ImportError:
        print(
            "\n  pywebview is required to launch ClipForge in desktop mode.\n"
            "  Install desktop dependencies with:\n\n"
            "      pip install -r requirements-desktop.txt\n",
            file=sys.stderr,
            flush=True,
        )
        if args.fallback_browser:
            os.environ["CLIPFORGE_OPEN_BROWSER"] = "1"
            from . import server
            server.main()
            return
        sys.exit(1)

    preferred = args.port or int(os.environ.get("CLIPFORGE_PORT") or 8765)
    port, already_running = find_port(preferred)

    os.environ["CLIPFORGE_HOST"] = "127.0.0.1"
    os.environ["CLIPFORGE_PORT"] = str(port)
    os.environ["CLIPFORGE_OPEN_BROWSER"] = "0"

    uv_server = None
    server_thread = None
    server_error = {"msg": ""}
    live_mod = None

    if not already_running:
        import uvicorn
        from . import live as live_mod, server, storage

        uv_config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning", log_config=None, backlog=4096)
        uv_server = uvicorn.Server(uv_config)
        uv_server.install_signal_handlers = lambda: None

        def run_server():
            try:
                uv_server.run()
            except Exception as e:  # noqa: BLE001
                server_error["msg"] = str(e)

        server_thread = threading.Thread(target=run_server, daemon=True, name="clipforge-server")
        server_thread.start()

    window = webview.create_window(
        "ClipForge",
        html=LOADING_HTML,
        width=1280,
        height=840,
        min_size=(960, 640),
        background_color="#0F1012",
        js_api=DesktopApi(),
    )

    if not already_running:
        def desktop_pick_folder():
            dialog_type = getattr(getattr(webview, "FileDialog", None), "FOLDER", getattr(webview, "FOLDER_DIALOG", 20))
            res = window.create_file_dialog(dialog_type)
            if not res:
                return ""
            return str(res[0] if isinstance(res, (list, tuple)) else res)

        storage.set_folder_picker(desktop_pick_folder)

    tray_icon = None
    force_quit = {"yes": False}
    app_url = f"http://127.0.0.1:{port}/app"

    def shutdown():
        force_quit["yes"] = True
        if tray_icon is not None:
            try:
                tray_icon.stop()
            except Exception:  # noqa: BLE001
                pass
        if live_mod is not None:
            live_mod.stop_all("ClipForge closed")
        if uv_server is not None:
            uv_server.should_exit = True

    try:
        import pystray
        tray_img = build_tray_icon()
        if tray_img is not None:
            def _open_window(icon=None, item=None):
                try:
                    window.show()
                    window.restore()
                except Exception:  # noqa: BLE001
                    pass

            def _open_browser(icon=None, item=None):
                webbrowser.open(app_url)

            def _quit_app(icon=None, item=None):
                shutdown()
                try:
                    window.destroy()
                except Exception:  # noqa: BLE001
                    pass

            menu = pystray.Menu(
                pystray.MenuItem("Open ClipForge", _open_window, default=True),
                pystray.MenuItem("Open in Browser", _open_browser),
                pystray.MenuItem("Quit ClipForge", _quit_app),
            )
            tray_icon = pystray.Icon("clipforge", tray_img, "ClipForge", menu)
            threading.Thread(target=tray_icon.run, daemon=True, name="clipforge-tray").start()
    except Exception:  # noqa: BLE001
        tray_icon = None

    def on_closing():
        if not force_quit["yes"] and tray_icon is not None:
            keep_in_tray = args.tray_on_close or os.environ.get("CLIPFORGE_TRAY_ON_CLOSE") == "1"
            if keep_in_tray or (live_mod is not None and live_mod.active()):
                try:
                    window.hide()
                except Exception:  # noqa: BLE001
                    pass
                return False
        shutdown()
        return True

    window.events.closing += on_closing

    def on_start():
        if already_running or wait_ready(port, stop_check=lambda: bool(server_error["msg"]) or force_quit["yes"]):
            window.load_url(app_url)
            return
        msg = server_error["msg"] or "ClipForge server failed to start."
        try:
            window.evaluate_js(f"document.getElementById('status').textContent = {json.dumps(msg)};")
        except Exception:  # noqa: BLE001
            pass

    try:
        webview.start(on_start)
    finally:
        shutdown()
        if server_thread is not None and server_thread.is_alive():
            server_thread.join(timeout=4)


if __name__ == "__main__":
    main()
