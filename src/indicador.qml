// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

Window {
    id: ventana
    width: 380
    height: 164
    visible: true
    color: "transparent"
    title: payload.title
    flags: Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput

    // Sin anclajes: el compositor centra el aviso en la pantalla activa.
    LayerShell.Window.anchors: LayerShell.Window.AnchorNone
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
    LayerShell.Window.activateOnShow: false
    LayerShell.Window.wantsToBeOnActiveScreen: true
    LayerShell.Window.scope: "lenovo-mode-osd"

    property var payload: JSON.parse(Qt.application.arguments[Qt.application.arguments.length - 1])
    property string modo: payload.mode
    property var modos: ({
        "low-power": { color: "#65d6a4", simbolo: "↓" },
        "balanced": { color: "#7cb9ff", simbolo: "=" },
        "performance": { color: "#ffbb70", simbolo: "↑" }
    })
    property var actual: modos[modo] || { color: "#7cb9ff", simbolo: "•" }

    Rectangle {
        id: tarjeta
        anchors.fill: parent
        anchors.margins: 8
        radius: 24
        color: "#f018202c"
        border.color: "#445165"
        border.width: 1
        opacity: 0

        Row {
            anchors.centerIn: parent
            spacing: 20

            Rectangle {
                width: 60
                height: 60
                radius: 20
                color: "#273747"
                Text {
                    anchors.centerIn: parent
                    text: ventana.actual.simbolo
                    color: ventana.actual.color
                    font.pixelSize: 38
                    font.weight: Font.DemiBold
                }
            }

            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 7
                Text {
                    text: ventana.payload.heading
                    color: "#aebacc"
                    font.pixelSize: 11
                    font.letterSpacing: 1.5
                }
                Text {
                    objectName: "powerModeName"
                    text: ventana.payload.name
                    color: "#f5f7fb"
                    font.pixelSize: 23
                    font.weight: Font.DemiBold
                }
            }
        }
    }

    SequentialAnimation {
        running: true
        NumberAnimation { target: tarjeta; property: "opacity"; to: 1; duration: 140 }
        PauseAnimation { duration: 1900 }
        NumberAnimation { target: tarjeta; property: "opacity"; to: 0; duration: 160 }
        ScriptAction { script: Qt.quit() }
    }
}
