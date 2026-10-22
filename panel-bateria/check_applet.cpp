// SPDX-License-Identifier: GPL-3.0-or-later
#include <QGuiApplication>
#include <KPluginMetaData>
#include <Plasma/PluginLoader>
#include <Plasma/Applet>
#include <cstdio>
int main(int argc, char**argv) {
    QGuiApplication app(argc,argv);
    KPluginMetaData metadata(QStringLiteral("plasma/applets/org.kde.plasma.battery"));
    auto battery = Plasma::PluginLoader::self()->loadApplet(QStringLiteral("org.kde.plasma.battery"));
    if (!battery) return 1;
    auto *control = battery->property("conservation").value<QObject*>();
    fprintf(stdout, "Plugin: %s\nControl: %s\n", qPrintable(metadata.fileName()), control ? "available" : "missing");
    if (!control) return 2;
    fprintf(stdout, "State: %d\n",control->property("state").toInt());
    return 0;
}
