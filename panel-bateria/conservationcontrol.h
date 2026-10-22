// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <QObject>
#include <QProcess>
#include <QStringList>
#include <QTimer>

class ConservationControl : public QObject {
    Q_OBJECT
    Q_PROPERTY(int state READ state NOTIFY changed)
    Q_PROPERTY(bool pending READ pending NOTIFY changed)
    Q_PROPERTY(QString error READ error NOTIFY changed)
public:
    explicit ConservationControl(QObject *parent = nullptr,
        QString path = QStringLiteral("/sys/bus/platform/devices/VPC2004:00/conservation_mode"),
        QString program = QStringLiteral("/usr/bin/pkexec"),
        QStringList arguments = {QStringLiteral("/usr/local/lib/lenovo-modes/bateria-control")});
    int state() const { return m_state; }
    bool pending() const { return m_pending; }
    QString error() const { return m_error; }
    Q_INVOKABLE void setEnabled(bool enabled);
    Q_INVOKABLE void refresh();
signals:
    void changed();
private:
    int readState() const;
    void finish(int code, QProcess::ExitStatus status);
    QString m_path, m_program;
    QStringList m_arguments;
    QProcess m_process;
    QTimer m_poll;
    int m_state = -1, m_requested = -1;
    bool m_pending = false;
    QString m_error;
};
