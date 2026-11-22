"""Tests for Windows NSIS packaging script, version metadata, and build script syntax."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import studio

ROOT = Path(__file__).resolve().parent.parent
NSI = ROOT / "packaging" / "ClipForge.nsi"
PS1 = ROOT / "packaging" / "build_setup.ps1"


class PackagingTests(unittest.TestCase):
    def test_version_semver(self):
        self.assertRegex(studio.__version__, r"^\d+\.\d+\.\d+$")

    def test_nsis_script_directives(self):
        text = NSI.read_text(encoding="utf-8")
        for expected in (
            'Unicode true',
            'RequestExecutionLevel user',
            'InstallDir "$LOCALAPPDATA\\ClipForge"',
            '/ISOLATEDTEST',
            'WriteUninstaller "$INSTDIR\\Uninstall.exe"',
            'UshaLabs',
            'ClipForge.exe',
        ):
            self.assertIn(expected, text)
        self.assertNotIn("ClipKontrast", text)
        self.assertNotIn("PeakCut", text)

    def test_build_setup_powershell_syntax(self):
        self.assertTrue(PS1.is_file())
        ps = shutil.which("powershell") or shutil.which("pwsh")
        if not ps:
            self.skipTest("PowerShell not installed on this platform")
        cmd = (
            f"$errors = $null; "
            f"$null = [System.Management.Automation.Language.Parser]::ParseFile('{PS1}', [ref]$null, [ref]$errors); "
            f"exit ($errors.Count)"
        )
        res = subprocess.run([ps, "-NoProfile", "-Command", cmd], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, msg=res.stderr or res.stdout)


if __name__ == "__main__":
    unittest.main()
