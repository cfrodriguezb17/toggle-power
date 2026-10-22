// SPDX-License-Identifier: GPL-3.0-or-later
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickWindow>
#include <QTimer>
#include <cstdio>
#include <KLocalizedQmlContext>
#include <KLocalizedString>
#include <QQmlContext>
int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    KLocalizedString::setApplicationDomain("plasma_applet_org.kde.plasma.battery");
    QQmlApplicationEngine engine;
    KLocalization::setupLocalizedContext(&engine);
    QObject::connect(&engine, &QQmlApplicationEngine::warnings, &app, [](const QList<QQmlError>& errors) {
        for (const auto &error: errors) fprintf(stderr,"%s\n",qPrintable(error.toString()));
    });
    engine.load(QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    if (engine.rootObjects().isEmpty()) return 1;
    QTimer::singleShot(1500, &app, [&] {
        auto *toggle = engine.rootObjects().first()->findChild<QObject*>("lenovoChargeLimitSwitch");
        if (!toggle) {
            auto *label = engine.rootObjects().first()->findChild<QObject*>("powerModeName");
            if (!label || argc < 4 || label->property("text").toString() != QString::fromLocal8Bit(argv[3])) {
                fprintf(stderr,"Incorrect OSD text.\n"); app.exit(7); return;
            }
        } else {
        if (toggle->property("checked").toBool()) { app.exit(3); return; }
        if (argc > 3 && toggle->property("text").toString() != QString::fromLocal8Bit(argv[3])) {
            fprintf(stderr,"Wrong locale: %s\n",qPrintable(toggle->property("text").toString())); app.exit(6); return;
        }
        QMetaObject::invokeMethod(toggle, "click");
        if (!toggle->property("checked").toBool()) { app.exit(4); return; }
        QMetaObject::invokeMethod(toggle, "click");
        if (toggle->property("checked").toBool()) { app.exit(5); return; }
        fprintf(stdout, "Switch: activation and deactivation verified (mock).\n");
        }
        auto *window = qobject_cast<QQuickWindow*>(engine.rootObjects().first());
        if (!window || !window->grabWindow().save(QString::fromLocal8Bit(argv[2]))) app.exit(2);
        else app.quit();
    });
    return app.exec();
}
