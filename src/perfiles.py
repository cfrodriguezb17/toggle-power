# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe firmware profiles and display an OSD; never open keyboard devices."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from i18n import translations

def N_(text):
    """Mark source labels for xgettext without translating them at import time."""
    return text


MODES = {
    "low-power": (N_("Power Save"), "power-profile-power-saver-symbolic"),
    "balanced": (N_("Balanced"), "power-profile-balanced-symbolic"),
    "performance": (N_("Performance"), "power-profile-performance-symbolic"),
}


def mode_payload(mode):
    if mode not in MODES:
        raise ValueError(f"Unknown profile: {mode}")
    _ = translations().gettext
    return {"mode": mode, "name": _(MODES[mode][0]),
            "heading": _("POWER MODE"), "title": _("Toggle Power")}


class IndicadorModo:
    def __init__(self):
        self.command = shutil.which("notify-send")
        self.qml = shutil.which("qml6") or shutil.which("qml")
        self.file = Path(__file__).with_name("indicador.qml")
        self.process = None
        self.identifier = "0"
        self.environment = os.environ.copy()
        if self.environment.get("WAYLAND_DISPLAY"):
            self.environment["QT_QPA_PLATFORM"] = "wayland"
        else:
            self.qml = None
        if not self.file.is_file():
            self.qml = None

    def cerrar(self):
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        if self.process.stderr:
            self.process.stderr.close()
        self.process = None

    def mostrar(self, mode):
        if mode not in MODES:
            return
        _ = translations().gettext
        if self.process is not None and self.process.poll() not in (None, 0):
            print(_("The centered indicator failed; using desktop notifications."), file=sys.stderr)
            self.qml = None
        self.cerrar()
        payload = mode_payload(mode)
        if self.qml:
            try:
                self.process = subprocess.Popen(
                    [self.qml, str(self.file), "--", json.dumps(payload, ensure_ascii=False)],
                    env=self.environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                return
            except OSError:
                self.qml = None
        if not self.command:
            print(_("No indicator is available. Install qml6 or notify-send."), file=sys.stderr)
            return
        try:
            result = subprocess.run(
                [self.command, "--app-name=" + _("Toggle Power"), "--urgency=normal",
                 "--expire-time=2200", "--transient", "--print-id",
                 "--replace-id=" + self.identifier, "--icon=" + MODES[mode][1],
                 payload["name"], _("Power profile activated")],
                env=self.environment, capture_output=True, text=True, timeout=2, check=True)
            if result.stdout.strip().isdecimal():
                self.identifier = result.stdout.strip()
        except (OSError, subprocess.SubprocessError) as error:
            print(_("Could not display the power profile notification:") + " " + str(error), file=sys.stderr)


class MonitorPerfil:
    def __init__(self, ruta=Path("/sys/firmware/acpi/platform_profile")):
        self.ruta = ruta
        self.estado = self.leer()

    def leer(self):
        try:
            return self.ruta.read_text().strip() or None
        except OSError:
            return None

    def comprobar(self):
        nuevo = self.leer()
        if nuevo is not None and nuevo != self.estado:
            self.estado = nuevo
            return True
        return False
