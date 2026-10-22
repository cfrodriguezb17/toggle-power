# SPDX-License-Identifier: GPL-3.0-or-later
"""Pruebas de cambios de límite sin escribir al hardware real."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from potencia_servicio import aplicar


class LimitesTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        for nombre in ("intel-rapl:0", "intel-rapl-mmio:0"):
            zona = self.raiz / nombre
            zona.mkdir()
            (zona / "enabled").write_text("1")
            # Índices invertidos: se deben usar los nombres, no asumir 0/1.
            for indice, tipo in ((0, "short_term"), (1, "long_term"), (2, "peak_power")):
                (zona / f"constraint_{indice}_name").write_text(tipo)
                (zona / f"constraint_{indice}_power_limit_uw").write_text("95000000" if indice == 2 else "37000000")

    def test_los_tres_modos_en_ambas_interfaces(self):
        for modo, esperado in (("low-power", (8, 17)), ("balanced", (24, 24)), ("performance", (37, 37))):
            resultado = aplicar(modo, self.raiz)
            self.assertEqual(len(resultado), 2)
            self.assertTrue(all(r["ok"] for r in resultado))
            for zona in self.raiz.iterdir():
                self.assertEqual(int((zona / "constraint_1_power_limit_uw").read_text()), esperado[0] * 1_000_000)
                self.assertEqual(int((zona / "constraint_0_power_limit_uw").read_text()), esperado[1] * 1_000_000)
                self.assertEqual((zona / "constraint_2_power_limit_uw").read_text(), "95000000")

    def test_no_reescribe_si_ya_coinciden_y_corrige_desajustes(self):
        aplicar("low-power", self.raiz)
        with patch.object(Path, "write_text", side_effect=AssertionError("escritura innecesaria")):
            aplicar("low-power", self.raiz)
        archivo = self.raiz / "intel-rapl:0/constraint_1_power_limit_uw"
        archivo.write_text("37000000")
        aplicar("low-power", self.raiz)
        self.assertEqual(archivo.read_text().strip(), "8000000")

    def test_sube_primero_pl2_y_baja_primero_pl1(self):
        escribir = Path.write_text
        escrituras = []

        def registrar(ruta, valor, *args, **kwargs):
            escrituras.append(ruta.name)
            return escribir(ruta, valor, *args, **kwargs)

        with patch.object(Path, "write_text", registrar):
            aplicar("low-power", self.raiz)
            self.assertEqual(escrituras[:2], ["constraint_1_power_limit_uw", "constraint_0_power_limit_uw"])
            escrituras.clear()
            aplicar("performance", self.raiz)
            self.assertEqual(escrituras[:2], ["constraint_0_power_limit_uw", "constraint_1_power_limit_uw"])

    def test_perfil_desconocido_no_escribe(self):
        with patch.object(Path, "write_text", side_effect=AssertionError("no debe escribir")):
            with self.assertRaises(ValueError):
                aplicar("custom", self.raiz)

    def test_rechazo_y_zona_deshabilitada_no_se_reportan_como_exito(self):
        (self.raiz / "intel-rapl-mmio:0/enabled").write_text("0")
        escribir = Path.write_text

        def rechazar(ruta, valor, *args, **kwargs):
            if ruta.parent.name == "intel-rapl:0":
                raise PermissionError("registro bloqueado")
            return escribir(ruta, valor, *args, **kwargs)

        with patch.object(Path, "write_text", rechazar):
            resultado = aplicar("low-power", self.raiz)
        self.assertFalse(any(r["ok"] for r in resultado))
        self.assertIn("registro bloqueado", resultado[0]["error"])
        self.assertIn("disabled", resultado[1]["error"])


if __name__ == "__main__":
    unittest.main()
