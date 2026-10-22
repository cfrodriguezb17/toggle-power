// SPDX-License-Identifier: LGPL-2.0-or-later
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

PlasmaComponents3.ItemDelegate {
    id: root
    required property var control
    readonly property int state: control?.state ?? -1
    readonly property bool pending: control?.pending ?? false
    readonly property string error: control?.error ?? ""
    readonly property alias toggle: limitSwitch
    background.visible: highlighted
    highlighted: activeFocus
    hoverEnabled: false
    contentItem: RowLayout {
        spacing: Kirigami.Units.gridUnit
        Kirigami.Icon {
            source: "battery"
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            PlasmaComponents3.Switch {
                id: limitSwitch
                objectName: "lenovoChargeLimitSwitch"
                Layout.fillWidth: true
                text: i18nd("lenovo-modes", "Limit charge to 80%")
                enabled: root.state >= 0 && !root.pending
                // Include pending so a cancelled authorization restores the visual state.
                Binding on checked {
                    value: {
                        const pending = root.pending;
                        return root.state === 1;
                    }
                    restoreMode: Binding.RestoreNone
                }
                onToggled: root.control?.setEnabled(checked)
                Keys.onReturnPressed: click()
                Keys.onEnterPressed: click()
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                opacity: 0.7
                text: root.pending ? i18nd("lenovo-modes", "Applying charge limit…")
                    : root.state === 1 ? i18nd("lenovo-modes", "Battery conservation enabled")
                    : root.state === 0 ? i18nd("lenovo-modes", "Off · Charging to 100% allowed")
                    : i18nd("lenovo-modes", "Battery conservation is unavailable")
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: text.length > 0
                wrapMode: Text.Wrap
                color: Kirigami.Theme.negativeTextColor
                text: root.error
            }
        }
    }
}
