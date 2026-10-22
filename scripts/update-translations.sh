#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
tmp=$(mktemp)
trap 'rm -f -- "$tmp"' EXIT
metadata=(--package-name="Toggle Power" --package-version=1.0 --copyright-holder="Toggle Power contributors")
xgettext "${metadata[@]}" --from-code=UTF-8 --language=Python --keyword=_ --keyword=N_ \
    --package-name='Toggle Power' --package-version=1.0 --output="$tmp" src/perfiles.py scripts/install.py scripts/recompilar-panel.py
xgettext "${metadata[@]}" --from-code=UTF-8 --language=C++ --keyword=message --keyword=i18nd:2 --join-existing \
    --output="$tmp" panel-bateria/conservationcontrol.cpp
xgettext "${metadata[@]}" --from-code=UTF-8 --language=JavaScript --keyword=i18nd:2 --join-existing \
    --output="$tmp" panel-bateria/LimiteCargaItem.qml
mv -- "$tmp" po/lenovo-modes.pot
msgmerge --update --backup=none po/es.po po/lenovo-modes.pot
