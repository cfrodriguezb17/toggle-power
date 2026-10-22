#!/usr/bin/env bash
set -euo pipefail
base=$(cd -- "$(dirname -- "$0")" && pwd)
if /usr/bin/python3 -B "$base/recompilar-panel.py" && source "$base/versiones-panel-bateria.sh" && versiones_panel_comprobar "$base/kde-version.txt"; then
    export QT_PLUGIN_PATH="$base/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
else
    echo 'Toggle Power: battery panel rebuild unavailable; using the standard KDE panel.' >&2
fi
exec /usr/bin/plasmashell --no-respawn
