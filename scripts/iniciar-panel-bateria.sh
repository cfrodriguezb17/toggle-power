#!/usr/bin/env bash
set -euo pipefail
base=$(cd -- "$(dirname -- "$0")" && pwd)
if source "$base/versiones-panel-bateria.sh" && versiones_panel_comprobar "$base/kde-version.txt"; then
    export QT_PLUGIN_PATH="$base/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
else
    echo 'Toggle Power: KDE/Qt changed version; using the original battery panel.' >&2
    systemctl --user --no-block start lenovo-battery-tray.service || true
fi
exec /usr/bin/plasmashell --no-respawn
