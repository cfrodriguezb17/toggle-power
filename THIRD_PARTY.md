# Third-party code

The battery popup QML and metadata in `panel-bateria/` were extracted from the
installed KDE PowerDevil 6.8.0 applet, originally under
`applets/batterymonitor/` in https://invent.kde.org/plasma/powerdevil .

Original KDE files: `BatteryItem.qml`, `CompactRepresentation.qml`,
`InhibitionHint.qml`, `InhibitionItem.qml`, `PowerProfileItem.qml`, `main.xml`,
`metadata.json`, plus the adapted `main.qml` and `PopupDialog.qml`.

Their original authors, SPDX notices and localized metadata are retained.
QML notices specify **LGPL-2.0-or-later**. The upstream applet metadata declares
**GPL-2.0+** (GPL-2.0-or-later). License texts are included in `LICENSES/`.
The added `LimiteCargaItem.qml` keeps its LGPL-2.0-or-later notice.

Changes to the KDE QML connect the existing popup to a local charge-limit
controller and add the conservation switch after the inhibition controls.
KDE's original translation domain remains intact; added UI uses the separate
`lenovo-modes` translation domain.

The other added Python, C++, shell, build, translation and test files are
GPL-3.0-or-later unless an individual file says otherwise.
