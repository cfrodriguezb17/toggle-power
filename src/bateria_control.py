#!/usr/bin/python3 -I
# SPDX-License-Identifier: GPL-3.0-or-later
"""Privileged helper: accepts only 0/1 and writes only conservation_mode."""

import os
from pathlib import Path
import sys

CONTROL = Path("/sys/bus/platform/devices/VPC2004:00/conservation_mode")


def cambiar(valor, ruta=CONTROL):
    if valor not in ("0", "1"):
        raise ValueError("Only 0 or 1 is allowed")
    ruta.write_text(valor + "\n")
    if ruta.read_text().strip() != valor:
        raise OSError("The driver did not confirm the change")


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2:
        print("Authorization and one state argument (0 or 1) are required.", file=sys.stderr)
        return 1
    try:
        cambiar(sys.argv[1])
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print("Battery conservation enabled" if sys.argv[1] == "1" else "Full charging allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
