#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render mock battery controls and OSDs offscreen; never call a privileged helper."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'src'))
from perfiles import mode_payload

output=ROOT/'build/previews'
output.mkdir(parents=True,exist_ok=True)
# Keep rendering independent of the Wayland compositor in the visual test only.
qml=(ROOT/'src/indicador.qml').read_text()
qml='\n'.join(line for line in qml.splitlines() if 'LayerShell' not in line)
preview=output/'indicator.qml'; preview.write_text(qml)
base=dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
          XDG_DATA_DIRS=str(ROOT/'build/share')+':/usr/local/share:/usr/share',
          LENOVO_MODES_LOCALE_DIR=str(ROOT/'build/share/locale'), LC_ALL='en_US.UTF-8')
for language in ('en','es','es_CO','fr_FR'):
    env=dict(base,LANGUAGE=language)
    expected='Limitar carga al 80 %' if language.startswith('es') else 'Limit charge to 80%'
    subprocess.run([str(ROOT/'build/panel-bateria/preview_panel'),
                    str(ROOT/'panel-bateria/preview.qml'),str(output/f'battery-{language}.png'),expected],
                   env=env,check=True,timeout=25)
    print(f'Battery popup: {language}',flush=True)
for language in ('en','es'):
    env=dict(base,LANGUAGE=language)
    os.environ['LANGUAGE']=language
    os.environ['LC_ALL']='en_US.UTF-8'
    for mode in ('low-power','balanced','performance'):
        payload=mode_payload(mode)
        subprocess.run([str(ROOT/'build/panel-bateria/preview_panel'),str(preview),
                        str(output/f'osd-{language}-{mode}.png'),payload['name'],json.dumps(payload,ensure_ascii=False)],
                       env=env,check=True,timeout=15)
        print(f'OSD: {language}/{mode}',flush=True)
print('10 offscreen visual checks passed. Images: build/previews/',flush=True)
