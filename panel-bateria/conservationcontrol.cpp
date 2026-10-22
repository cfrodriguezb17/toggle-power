// SPDX-License-Identifier: GPL-3.0-or-later
#include "conservationcontrol.h"
#include <QFile>
#include <KLocalizedString>

ConservationControl::ConservationControl(QObject *parent, QString path, QString program, QStringList arguments)
    : QObject(parent), m_path(std::move(path)), m_program(std::move(program)), m_arguments(std::move(arguments)) {
    connect(&m_poll, &QTimer::timeout, this, &ConservationControl::refresh);
    connect(&m_process, &QProcess::finished, this, &ConservationControl::finish);
    connect(&m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
        if (error != QProcess::FailedToStart) return;
        m_pending = false;
        m_state = readState();
        m_error = i18nd("lenovo-modes", "Could not start system authorization.");
        emit changed();
    });
    refresh();
    m_poll.start(2000);
}

int ConservationControl::readState() const {
    QFile file(m_path);
    if (!file.open(QIODevice::ReadOnly)) return -1;
    const auto value = file.readAll().trimmed();
    return value == "1" ? 1 : value == "0" ? 0 : -1;
}

void ConservationControl::refresh() {
    const int state = readState();
    if (state == m_state) return;
    m_state = state;
    emit changed();
}

void ConservationControl::setEnabled(bool enabled) {
    if (m_pending) return;
    refresh();
    m_error.clear();
    if (m_state < 0) {
        m_error = i18nd("lenovo-modes", "Battery conservation is unavailable");
        emit changed();
        return;
    }
    m_requested = enabled ? 1 : 0;
    if (m_state == m_requested) { emit changed(); return; }
    m_pending = true;
    emit changed();
    auto arguments = m_arguments;
    arguments.append(QString::number(m_requested));
    m_process.start(m_program, arguments);
}

void ConservationControl::finish(int code, QProcess::ExitStatus status) {
    m_pending = false;
    m_state = readState();
    if (status == QProcess::NormalExit && code == 0 && m_state == m_requested) {
        m_error.clear();
    } else if (code == 126) {
        m_error = i18nd("lenovo-modes", "Authorization cancelled. The charge limit was not changed.");
    } else {
        m_error = i18nd("lenovo-modes", "Could not confirm the charge limit change.");
    }
    emit changed();
}
