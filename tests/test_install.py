# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from install import Deployment, ROOT, battery_rule, check_hardware


class InstallTest(unittest.TestCase):
    def test_install_and_remove_in_staging_never_runs_services(self):
        with tempfile.TemporaryDirectory() as directory, patch('install.subprocess.run', side_effect=AssertionError('Host operation')):
            deployment=Deployment(directory)
            deployment.system('install','demo')
            deployment.session('install',Path('/home/demo'))
            rule=deployment.path('/etc/polkit-1/rules.d/49-lenovo-battery.rules')
            self.assertEqual(rule.read_text(),battery_rule('demo'))
            self.assertEqual(rule.stat().st_mode & 0o777,0o644)
            helper=deployment.path('/usr/local/lib/lenovo-modes/bateria-control')
            self.assertEqual(helper.stat().st_mode & 0o777,0o755)
            self.assertIn('subject.local && subject.active',rule.read_text())
            self.assertTrue(deployment.path('/home/demo/.config/systemd/user/lenovo-mode-indicator.service').is_file())
            deployment.session('uninstall',Path('/home/demo'))
            deployment.system('uninstall','demo')
            self.assertFalse(rule.exists()); self.assertFalse(helper.exists())
            self.assertFalse([p for p in Path(directory).rglob('*') if p.is_file()])

    def test_staging_cli_follows_spanish_locale(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ, LANGUAGE='es', LC_ALL='en_US.UTF-8')
            args = ['--destdir', directory, '--user', 'demo', '--home', '/home/demo']
            result = subprocess.run([str(ROOT/'install.sh'), *args], env=environment,
                                    capture_output=True, text=True, check=True)
            self.assertIn('Instalación completada.', result.stdout)
            result = subprocess.run([str(ROOT/'uninstall.sh'), *args], env=environment,
                                    capture_output=True, text=True, check=True)
            self.assertIn('Desinstalación completada.', result.stdout)
            self.assertFalse([p for p in Path(directory).rglob('*') if p.is_file()])

    def test_edited_override_and_rule_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            deployment=Deployment(directory)
            rule=Path('/etc/polkit-1/rules.d/49-lenovo-battery.rules')
            deployment.write(rule,'// other policy')
            with self.assertRaises(RuntimeError): deployment.system('uninstall','demo')
            self.assertEqual(deployment.path(rule).read_text(),'// other policy')
            override=Path('/home/demo/.config/systemd/user/plasma-plasmashell.service.d/60-lenovo-battery-panel.conf')
            deployment.write(override,'# unrelated config')
            with self.assertRaises(RuntimeError): deployment.session('install',Path('/home/demo'))
            self.assertEqual(deployment.path(override).read_text(),'# unrelated config')

    def test_rule_escapes_account_name(self):
        user='name"\\suffix'
        self.assertIn(json.dumps(user),battery_rule(user))

    def test_staging_cannot_target_host_root(self):
        with self.assertRaises(RuntimeError): Deployment('/')

    def test_hardware_checks_do_not_write_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            values={'class/dmi/id/sys_vendor':'LENOVO',
                    'firmware/acpi/platform_profile_choices':'low-power balanced performance',
                    'firmware/acpi/platform_profile':'balanced',
                    'bus/platform/devices/VPC2004:00/conservation_mode':'0',
                    'class/powercap/intel-rapl:0/enabled':'1',
                    'class/powercap/intel-rapl:0/constraint_0_name':'long_term',
                    'class/powercap/intel-rapl:0/constraint_1_name':'short_term'}
            for name,value in values.items():
                file=root/name; file.parent.mkdir(parents=True,exist_ok=True); file.write_text(value)
            with patch('install.Path.write_text',side_effect=AssertionError('Hardware write')):
                check_hardware(root)
            (root/'firmware/acpi/platform_profile_choices').write_text('balanced')
            with self.assertRaises(RuntimeError): check_hardware(root)
