// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import org.kde.plasma.private.battery
Window {
    visible: true
    width: 650
    height: 600
    color: "#eeeeee"
    QtObject {
        id: control
        property int state: 0
        property bool pending: false
        property string error: ""
        function setEnabled(enabled) { state = enabled ? 1 : 0; }
    }
    PopupDialog {
        anchors.fill: parent
        conservationControl: control
        model: ListModel {
            ListElement {
                Percent: 93
                Capacity: 97
                Energy: 63.0
                PluggedIn: true
                IsPowerSupply: true
                ChargeState: 2
                PrettyName: "Battery"
                Type: 2
            }
        }
        pluggedIn: false
        chargeStopThreshold: 100
        remainingTime: 25920000
        profilesInstalled: true
        profiles: ["power-saver", "balanced", "performance"]
        activeProfile: "power-saver"
        profileHolds: []
        requestedInhibitions: []
        isManuallyInhibited: false
        isManuallyInhibitedError: false
        inhibitsLidAction: false
        isTlpInstalled: false
    }
}
