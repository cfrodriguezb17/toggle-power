// SPDX-License-Identifier: GPL-3.0-or-later
#include <KPluginFactory>
#include <Plasma/Applet>
#include "conservationcontrol.h"

class LenovoBatteryApplet : public Plasma::Applet {
    Q_OBJECT
    Q_PROPERTY(QObject *conservation READ conservation CONSTANT)
public:
    LenovoBatteryApplet(QObject *parent, const KPluginMetaData &data, const QVariantList &args)
        : Plasma::Applet(parent, data, args), m_conservation(this) {}
    QObject *conservation() { return &m_conservation; }
private:
    ConservationControl m_conservation;
};
K_PLUGIN_CLASS_WITH_JSON(LenovoBatteryApplet, "metadata.json")
#include "batteryapplet.moc"
