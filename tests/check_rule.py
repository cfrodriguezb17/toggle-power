# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluate a generated rule in Qt's JS engine, without asking Polkit."""
import pathlib
import subprocess
import sys
import tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scripts'))
from install import battery_rule

with tempfile.TemporaryDirectory() as directory:
    rule = pathlib.Path(directory) / 'battery.rules'
    rule.write_text(battery_rule('demo'))
    subprocess.run([sys.argv[1], str(rule)], check=True)
