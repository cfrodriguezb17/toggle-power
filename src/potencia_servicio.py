#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Aplica PL1/PL2 según el perfil de Lenovo; servicio del sistema, sin GUI."""

import json
from pathlib import Path
import signal
import time


MODOS = {"low-power": (8, 17), "balanced": (24, 24), "performance": (37, 37)}
PERFIL = Path("/sys/firmware/acpi/platform_profile")
POWERCAP = Path("/sys/class/powercap")
ESTADO = Path("/run/lenovo-power-modes/status.json")


def aplicar(modo, raiz=POWERCAP):
    """Ajusta solo long_term y short_term del paquete, con lectura de verificación."""
    if modo not in MODOS:
        raise ValueError(f"Unconfigured profile: {modo}")
    pl1, pl2 = (vatios * 1_000_000 for vatios in MODOS[modo])
    resultados = []
    for interfaz in ("intel-rapl:0", "intel-rapl-mmio:0"):
        zona = raiz / interfaz
        if not zona.exists():
            continue
        try:
            archivos = {}
            for nombre in zona.glob("constraint_*_name"):
                tipo = nombre.read_text().strip()
                if tipo in ("long_term", "short_term"):
                    archivos[tipo] = nombre.with_name(nombre.name.replace("_name", "_power_limit_uw"))
            if set(archivos) != {"long_term", "short_term"}:
                raise OSError("both PL1/PL2 limits are required")
            if (zona / "enabled").read_text().strip() != "1":
                raise OSError("RAPL control is disabled")
            actuales = {tipo: int(ruta.read_text()) for tipo, ruta in archivos.items()}
            objetivos = {"long_term": pl1, "short_term": pl2}
            # Al subir PL1 por encima del PL2 anterior, sube primero PL2.
            orden = ("short_term", "long_term") if pl1 > actuales["short_term"] else ("long_term", "short_term")
            for tipo in orden:
                if actuales[tipo] != objetivos[tipo]:
                    archivos[tipo].write_text(f"{objetivos[tipo]}\n")
                leido = int(archivos[tipo].read_text())
                if leido != objetivos[tipo]:
                    raise OSError(f"{tipo}: requested {objetivos[tipo]} µW, read {leido} µW")
            if any(int(archivos[tipo].read_text()) != objetivo for tipo, objetivo in objetivos.items()):
                raise OSError("limits changed during verification")
            resultados.append({"interfaz": interfaz, "ok": True, "pl1_w": pl1 / 1_000_000, "pl2_w": pl2 / 1_000_000})
        except (OSError, ValueError) as error:
            resultados.append({"interfaz": interfaz, "ok": False, "error": str(error)})
    if not resultados:
        raise OSError("No CPU package RAPL interfaces found")
    return resultados


def main():
    detener = False

    def terminar(*_):
        nonlocal detener
        detener = True

    signal.signal(signal.SIGTERM, terminar)
    signal.signal(signal.SIGINT, terminar)
    ultimo_modo = None
    ultimo_resultado = None
    ultima_revision = 0
    while not detener:
        try:
            modo = PERFIL.read_text().strip()
            ahora = time.monotonic()
            if modo != ultimo_modo or ahora - ultima_revision >= 1:
                resultados = aplicar(modo)
                estado = {"perfil": modo, "resultados": resultados}
                # No publiques un resultado de un perfil que acaba de cambiar.
                if PERFIL.read_text().strip() != modo:
                    continue
                contenido = json.dumps(estado, ensure_ascii=False, sort_keys=True)
                if contenido != ultimo_resultado:
                    temporal = ESTADO.with_suffix(".tmp")
                    temporal.write_text(contenido + "\n")
                    temporal.replace(ESTADO)
                    print(contenido, flush=True)
                    ultimo_resultado = contenido
                ultimo_modo, ultima_revision = modo, ahora
        except (OSError, ValueError) as error:
            mensaje = f"Could not apply power limits: {error}"
            if mensaje != ultimo_resultado:
                print(mensaje, flush=True)
                ultimo_resultado = mensaje
            # Perfil desconocido: no aplicar límites de otro modo.
            time.sleep(1)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
