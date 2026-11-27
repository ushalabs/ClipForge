"""Unit tests for the desktop wrapper, frozen path resolution, and folder picker hooks."""
import os
import shutil
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TMP_DATA = tempfile.mkdtemp(prefix="cf-desktop-test-")
os.environ.setdefault("CLIPFORGE_DATA", _TMP_DATA)
os.environ.setdefault("DATABASE_URL", "")

from studio import config, desktop, storage, tools  # noqa: E402


def tearDownModule():
    shutil.rmtree(_TMP_DATA, ignore_errors=True)


class DesktopTests(unittest.TestCase):
    def test_port_free_and_find_port_skips_occupied(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        busy_port = sock.getsockname()[1]
        try:
            self.assertFalse(desktop.port_free(busy_port))
            with mock.patch.object(desktop, "is_clipforge_running", return_value=False):
                chosen, running = desktop.find_port(preferred=busy_port)
            self.assertFalse(running)
            self.assertNotEqual(chosen, busy_port)
            self.assertTrue(desktop.port_free(chosen))
        finally:
            sock.close()

    def test_open_external_allows_only_http_and_https(self):
        api = desktop.DesktopApi()
        self.assertTrue(api.is_desktop())
        with mock.patch.object(desktop.webbrowser, "open", return_value=True) as open_mock:
            self.assertTrue(api.open_external("https://example.com/oauth"))
            self.assertTrue(api.open_external("http://127.0.0.1:8765/app"))
            self.assertEqual(open_mock.call_count, 2)

        with mock.patch.object(desktop.webbrowser, "open", return_value=True) as open_mock:
            self.assertFalse(api.open_external("javascript:alert(1)"))
            self.assertFalse(api.open_external("file:///C:/Windows/System32/cmd.exe"))
            self.assertFalse(api.open_external(""))
            open_mock.assert_not_called()

    def test_loading_html_branding(self):
        self.assertIn("FrameForge", desktop.LOADING_HTML)
        self.assertNotIn("ClipKontrast", desktop.LOADING_HTML)
        self.assertNotIn("PeakCut", desktop.LOADING_HTML)

    def test_folder_picker_hook_and_frozen_guard(self):
        old_picker = storage._folder_picker
        try:
            storage.set_folder_picker(lambda: str(Path(_TMP_DATA) / "chosen"))
            self.assertEqual(storage.pick_folder(), str(Path(_TMP_DATA) / "chosen"))

            storage.set_folder_picker(None)
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.object(storage.subprocess, "run") as run_mock:
                    self.assertEqual(storage.pick_folder(), "")
                    run_mock.assert_not_called()
        finally:
            storage.set_folder_picker(old_picker)

    def test_bundle_dir_has_web_and_fonts(self):
        self.assertTrue((config.BUNDLE_DIR / "web" / "index.html").is_file())
        self.assertTrue((config.BUNDLE_DIR / "studio" / "fonts").is_dir())

    def test_tools_places_respects_env_and_frozen_dir(self):
        custom_dir = str(Path(_TMP_DATA) / "custom-ffmpeg")
        fake_exe_dir = Path(_TMP_DATA) / "frozen-app"
        with mock.patch.dict(os.environ, {"CLIPFORGE_FFMPEG_DIR": custom_dir}):
            with mock.patch.object(sys, "frozen", True, create=True), \
                 mock.patch.object(sys, "executable", str(fake_exe_dir / "ClipForge.exe")):
                places = tools._places()
        self.assertEqual(places[0], Path(custom_dir))
        self.assertIn(fake_exe_dir / "ffmpeg" / "bin", places)
        self.assertIn(fake_exe_dir, places)


if __name__ == "__main__":
    unittest.main()
