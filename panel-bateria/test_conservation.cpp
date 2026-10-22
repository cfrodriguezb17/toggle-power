// SPDX-License-Identifier: GPL-3.0-or-later
#include <QtTest>
#include <KLocalizedString>
#include <QFile>
#include <QTemporaryDir>
#include "conservationcontrol.h"
class TestConservation : public QObject {
    Q_OBJECT
private slots:
    void messagesFollowSessionLanguage() {
        if (qEnvironmentVariable("LANGUAGE") == "es") {
            QCOMPARE(i18nd("lenovo-modes", "Battery conservation"), QString::fromUtf8("Conservación de batería"));
            QCOMPARE(i18nd("lenovo-modes", "Could not confirm the charge limit change."),
                     QString::fromUtf8("No se pudo confirmar el cambio del límite de carga."));
        }
    }
    void applyAndExternalChange() {
        QTemporaryDir dir;
        const auto path = dir.filePath("state");
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write("0\n"); file.close();
        ConservationControl control(nullptr, path, "/bin/sh", {"-c", "printf '%s\\n' \"$1\" > \"$0\"", path});
        QCOMPARE(control.state(), 0);
        control.setEnabled(true);
        QVERIFY(control.pending());
        QTRY_VERIFY(!control.pending());
        QCOMPARE(control.state(), 1);
        QVERIFY(control.error().isEmpty());
        QVERIFY(file.open(QIODevice::WriteOnly|QIODevice::Truncate)); file.write("0\n"); file.close();
        control.refresh();
        QCOMPARE(control.state(), 0);
    }
    void cancellationAndFailedConfirmation() {
        QTemporaryDir dir;
        const auto path = dir.filePath("state");
        QFile file(path); QVERIFY(file.open(QIODevice::WriteOnly)); file.write("0\n"); file.close();
        ConservationControl cancelled(nullptr, path, "/bin/sh", {"-c", "exit 126"});
        cancelled.setEnabled(true);
        QTRY_VERIFY(!cancelled.pending());
        QCOMPARE(cancelled.state(), 0);
        QCOMPARE(cancelled.error(), i18nd("lenovo-modes", "Authorization cancelled. The charge limit was not changed."));
        ConservationControl unchanged(nullptr, path, "/bin/true", {});
        unchanged.setEnabled(true);
        QTRY_VERIFY(!unchanged.pending());
        QCOMPARE(unchanged.state(), 0);
        QVERIFY(!unchanged.error().isEmpty());
    }
    void unavailable() {
        ConservationControl control(nullptr, "/missing/conservation", "/bin/true", {});
        QCOMPARE(control.state(), -1);
        control.setEnabled(true);
        QVERIFY(!control.pending());
        QVERIFY(!control.error().isEmpty());
    }
};
QTEST_GUILESS_MAIN(TestConservation)
#include "test_conservation.moc"
