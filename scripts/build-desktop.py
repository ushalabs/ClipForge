"""Build a standalone ClipForge desktop bundle using PyInstaller."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_icons(build_dir: Path):
    from studio.desktop import build_tray_icon

    img = build_tray_icon()
    if img is None:
        return
    build_dir.mkdir(parents=True, exist_ok=True)
    png = build_dir / "clipforge.png"
    ico = build_dir / "clipforge.ico"
    img.resize((256, 256)).save(png, format="PNG")
    img.resize((256, 256)).save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def main():
    missing = []
    for mod in ("PyInstaller", "webview"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(
            f"\n  Missing build dependencies: {', '.join(missing)}\n"
            "  Install desktop dependencies first:\n\n"
            "      pip install -r requirements-desktop.txt\n",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    _make_icons(ROOT / "build")
    spec = ROOT / "clipforge.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec)]
    print("  Building ClipForge desktop bundle...", flush=True)
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        sys.exit(rc)

    out_dir = ROOT / "dist" / "ClipForge"
    print(f"\n  Build complete: {out_dir}", flush=True)
    if sys.platform == "win32":
        print("  Note: Keep the installed ClipForge folder in a short path such as C:\\ClipForge.", flush=True)


if __name__ == "__main__":
    main()
