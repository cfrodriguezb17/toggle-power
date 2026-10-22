# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('panel_update', Path(__file__).resolve().parent.parent / 'scripts/recompilar-panel.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)

OLD = 'powerdevil 6.8.0-1\nlibplasma 6.8.0-1\nplasma-workspace 6.8.0-1\nqt6-base 6.12.0-1\nqt6-declarative 6.12.0-1\n'
NEW = OLD.replace('6.8.0', '6.8.1')


class PanelUpdateTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name) / 'data'
        self.cache = Path(self.directory.name) / 'cache'
        (self.base / 'source').mkdir(parents=True)
        (self.base / 'source/CMakeLists.txt').write_text('build kit')
        (self.base / update.PLUGIN).parent.mkdir(parents=True)
        (self.base / update.PLUGIN).write_bytes(b'original plugin')
        (self.base / 'kde-version.txt').write_text(OLD)
        self.commands = []
        self.actual = NEW
        self.failure = False
        self.instance = update.Updater(self.base, self.cache, self.fake_run)

    def fake_run(self, command, **kwargs):
        self.commands.append(command)
        if command[0] == 'pacman':
            return subprocess.CompletedProcess(command, 0, stdout=self.actual)
        if command[:2] == ['cmake', '--build']:
            if self.failure:
                raise subprocess.CalledProcessError(1, command)
            library = self.cache / 'build' / update.PLUGIN
            library.parent.mkdir(parents=True, exist_ok=True)
            library.write_bytes(b'new plugin')
        return subprocess.CompletedProcess(command, 0)

    def test_update_validates_then_installs_and_restarts(self):
        self.assertTrue(self.instance.rebuild(restart=True))
        self.assertEqual((self.base / update.PLUGIN).read_bytes(), b'new plugin')
        self.assertEqual((self.base / 'kde-version.txt').read_text(), NEW)
        self.assertTrue(any('check_applet' in cmd[0] for cmd in self.commands))
        self.assertTrue(any('preview_panel' in cmd[0] for cmd in self.commands))
        self.assertIn(['systemctl', '--user', '--no-block', 'restart', 'plasma-plasmashell.service'], self.commands)
        self.commands.clear()
        self.assertFalse(self.instance.rebuild(restart=True))
        self.assertEqual(len(self.commands), 1)  # version query only

    def test_packaging_revision_does_not_recompile(self):
        self.instance.rebuild()
        self.actual = NEW.replace('-1\n', '-99.2\n')
        self.commands.clear()
        self.assertFalse(self.instance.rebuild())
        self.assertEqual(len(self.commands), 1)

    def test_failure_preserves_plugin_and_fingerprint_and_does_not_loop(self):
        self.failure = True
        with patch.object(update.shutil, 'which', return_value=None):
            with self.assertRaises(subprocess.CalledProcessError): self.instance.rebuild(restart=True)
            self.assertEqual((self.base / update.PLUGIN).read_bytes(), b'original plugin')
            self.assertEqual((self.base / 'kde-version.txt').read_text(), OLD)
            self.commands.clear()
            with self.assertRaises(RuntimeError): self.instance.rebuild()
            self.assertEqual(len(self.commands), 1)
            self.failure = False
            self.assertTrue(self.instance.rebuild(force=True))

    def test_source_change_rebuilds_without_package_update(self):
        self.instance.rebuild()
        (self.base / 'source/CMakeLists.txt').write_text('fixed build kit')
        self.assertTrue(self.instance.rebuild())

    def test_package_change_during_build_never_installs_result(self):
        with patch.object(self.instance, 'versions', side_effect=[NEW, NEW.replace('6.8.1', '6.8.2')]), \
             patch.object(update.shutil, 'which', return_value=None):
            with self.assertRaises(RuntimeError): self.instance.rebuild()
        self.assertEqual((self.base / update.PLUGIN).read_bytes(), b'original plugin')

    def test_package_transaction_blocks_compilation(self):
        original = Path.exists
        with patch.object(Path, 'exists', lambda p: True if str(p) == '/var/lib/pacman/db.lck' else original(p)):
            with self.assertRaises(RuntimeError): self.instance.rebuild()
        self.assertFalse(self.commands)

    def test_versions_reject_incomplete_duplicate_or_invalid_packages(self):
        for bad in ('', OLD.replace('libplasma', 'powerdevil'), OLD.replace('6.8.0-1', 'invalid')):
            with self.subTest(bad=bad), self.assertRaises(ValueError): update.normalized(bad)

    def test_delayed_reload_after_login_used_standard_panel(self):
        self.instance.rebuild()
        (self.cache / 'needs-reload').touch()
        self.commands.clear()
        self.assertFalse(self.instance.rebuild(restart=True))
        self.assertIn(['systemctl', '--user', '--no-block', 'restart', 'plasma-plasmashell.service'], self.commands)
        self.assertFalse((self.cache / 'needs-reload').exists())
