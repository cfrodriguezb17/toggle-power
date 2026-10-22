# SPDX-License-Identifier: GPL-3.0-or-later
import gettext
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bateria_control import cambiar
from perfiles import mode_payload, MonitorPerfil, IndicadorModo


class LocaleTest(unittest.TestCase):
    def test_system_languages_and_mode_ids(self):
        for language, expected in [('en','Power Save'), ('en_US','Power Save'),
                                   ('es','Ahorro de energía'), ('es_CO','Ahorro de energía'),
                                   ('es_ES','Ahorro de energía'), ('fr_FR','Power Save')]:
            with self.subTest(language=language), patch.dict(os.environ, {'LANGUAGE': language, 'LC_ALL': 'en_US.UTF-8'}):
                payload = mode_payload('low-power')
                self.assertEqual(payload['name'],expected)
                self.assertEqual(payload['mode'],'low-power')
                for mode in ('balanced','performance'):
                    self.assertTrue(mode_payload(mode)['name'])

    def test_no_language_env_uses_session_locale(self):
        environment = {k:v for k,v in os.environ.items() if k not in ('LANGUAGE','LC_ALL','LC_MESSAGES','LANG')}
        environment['LANG'] = 'es_CO.UTF-8'
        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(mode_payload('balanced')['name'],'Equilibrado')

    def test_c_message_locale_uses_source_text(self):
        with patch.dict(os.environ, {'LANGUAGE':'es', 'LC_ALL':'C.UTF-8'}):
            self.assertEqual(mode_payload('balanced')['name'],'Balanced')

    def test_notification_uses_same_catalog(self):
        with patch.dict(os.environ, {'LANGUAGE':'es','LC_ALL':'en_US.UTF-8'}), patch('perfiles.shutil.which', return_value=None):
            indicator=IndicadorModo(); indicator.command='/fake/notify-send'
            with patch('perfiles.subprocess.run') as run:
                run.return_value.stdout='12\n'
                indicator.mostrar('performance')
                self.assertIn('Rendimiento',run.call_args.args[0])
                self.assertIn('Perfil de energía activado',run.call_args.args[0])
                self.assertEqual(indicator.identifier,'12')

    def test_unknown_profile_never_displays_a_mode(self):
        with self.assertRaises(ValueError): mode_payload('custom')
        with patch('perfiles.shutil.which',return_value=None):
            indicator=IndicadorModo()
        with patch('perfiles.subprocess.run') as command:
            indicator.mostrar('custom'); command.assert_not_called()


class FirmwareAndBatteryTest(unittest.TestCase):
    def test_profile_changes_and_missing_firmware(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'profile'
            monitor=MonitorPerfil(file)
            self.assertFalse(monitor.comprobar())
            file.write_text('balanced\n'); self.assertTrue(monitor.comprobar())
            self.assertEqual(monitor.estado,'balanced'); self.assertFalse(monitor.comprobar())
            file.write_text('performance\n'); self.assertTrue(monitor.comprobar())
            file.unlink(); self.assertFalse(monitor.comprobar())
            self.assertEqual(monitor.estado,'performance')

    def test_only_binary_battery_values_are_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'conservation'
            file.write_text('0\n')
            cambiar('1',file); self.assertEqual(file.read_text().strip(),'1')
            cambiar('0',file); self.assertEqual(file.read_text().strip(),'0')
            for invalid in ('2','yes','1\n', '../other'):
                with self.assertRaises(ValueError): cambiar(invalid,file)
                self.assertEqual(file.read_text().strip(),'0')

    def test_unconfirmed_battery_write_is_rejected(self):
        with patch.object(Path,'write_text'), patch.object(Path,'read_text',return_value='0'):
            with self.assertRaises(OSError): cambiar('1',Path('/mock'))
