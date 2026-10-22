# SPDX-License-Identifier: GPL-3.0-or-later
"""Checks the actual shell compatibility guard without changing KDE."""

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
BASELINE = (ROOT / "panel-bateria/kde-version.txt").read_text()


class VersionCompatibilityTest(unittest.TestCase):
    def compare(self, actual, expected=BASELINE):
        with tempfile.TemporaryDirectory() as directory:
            expected_path = Path(directory) / "expected"
            actual_path = Path(directory) / "actual"
            expected_path.write_text(expected)
            actual_path.write_text(actual)
            result = subprocess.run(
                ["bash", "-c", 'source "$1"; versiones_fixture=$3; '
                 'versiones_panel_sistema() { cat -- "$versiones_fixture"; }; '
                 'versiones_panel_comprobar "$2"', "test",
                 str(ROOT / "scripts/versiones-panel-bateria.sh"),
                 str(expected_path), str(actual_path)],
                capture_output=True, text=True, check=False,
            )
            return result.returncode == 0

    def test_same_versions(self):
        self.assertTrue(self.compare(BASELINE))

    def test_packaging_revisions_are_accepted(self):
        revised = "\n".join(line.rsplit("-", 1)[0] + "-99.2" for line in BASELINE.splitlines()) + "\n"
        self.assertTrue(self.compare(revised))

    def test_qt_upstream_change_is_rejected(self):
        self.assertFalse(self.compare(BASELINE.replace("qt6-declarative 6.12.0", "qt6-declarative 6.13.0")))

    def test_plasma_upstream_change_is_rejected(self):
        self.assertFalse(self.compare(BASELINE.replace("powerdevil 6.8.0", "powerdevil 6.8.1")))

    def test_epoch_is_preserved(self):
        with_epoch = BASELINE.replace("qt6-base 6.", "qt6-base 1:6.")
        self.assertFalse(self.compare(with_epoch))
        self.assertTrue(self.compare(with_epoch, expected=with_epoch))

    def test_incomplete_or_invalid_input_is_rejected(self):
        for bad in ("", "\n".join(BASELINE.splitlines()[:-1]),
                    BASELINE.replace("qt6-declarative 6.12.0-1.1", "qt6-declarative invalid")):
            with self.subTest(actual=bad):
                self.assertFalse(self.compare(bad))


if __name__ == "__main__":
    unittest.main()
