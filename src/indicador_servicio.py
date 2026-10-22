# SPDX-License-Identifier: GPL-3.0-or-later
#!/usr/bin/env python3
"""Indicador de cambios de perfil para la sesión gráfica, sin leer teclas."""

import fcntl
import os
from pathlib import Path
import signal
import time

from perfiles import IndicadorModo, MonitorPerfil


def main():
    # Una sola instancia por sesión, incluso al reiniciar el servicio.
    ruta = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    with (ruta / "lenovo-mode-indicator.lock").open("a") as bloqueo:
        try:
            fcntl.flock(bloqueo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        detener = False

        def terminar(*_):
            nonlocal detener
            detener = True

        signal.signal(signal.SIGTERM, terminar)
        signal.signal(signal.SIGINT, terminar)
        indicador = IndicadorModo()
        perfil = MonitorPerfil()
        try:
            print("Power profile indicator ready.", flush=True)
            while not detener:
                if perfil.comprobar():
                    indicador.mostrar(perfil.estado)
                time.sleep(0.2)
        finally:
            indicador.cerrar()


if __name__ == "__main__":
    main()
