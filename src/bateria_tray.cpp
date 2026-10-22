// SPDX-License-Identifier: GPL-3.0-or-later
#include <QApplication>
#include <QDBusConnection>
#include <QDBusInterface>
#include <QLabel>
#include <QMenu>
#include <QPainter>
#include <QPushButton>
#include <QSystemTrayIcon>
#include <QVBoxLayout>
#include <KLocalizedString>
#include <QTemporaryDir>
#include <QTimer>
#include <QFile>
#include <cstdio>
#include "conservationcontrol.h"

static QString message(const char *text) { return i18nd("lenovo-modes", text); }
static constexpr auto busName = "org.local.LenovoBattery";

static QIcon batteryIcon(int state) {
    QPixmap image(64,64); image.fill(Qt::transparent);
    QPainter painter(&image); painter.setRenderHint(QPainter::Antialiasing);
    const QColor color(state == 1 ? "#6bd5a5" : state == 0 ? "#80bdff" : "#b5bdc8");
    painter.setPen(QPen(color,4)); painter.setBrush(QColor("#1b2430"));
    painter.drawRoundedRect(QRectF(4,13,51,38),7,7);
    painter.fillRect(QRect(57,25,5,14),color); painter.setPen(color);
    auto font=painter.font(); font.setPixelSize(state == 0 ? 21 : 26); font.setBold(true);
    painter.setFont(font);
    painter.drawText(QRect(4,13,51,38),Qt::AlignCenter,state == 1 ? "80" : state == 0 ? "100" : "?");
    return QIcon(image);
}

class BatteryApp : public QObject {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.local.LenovoBattery")
public:
    BatteryApp(const QString &path = QStringLiteral("/sys/bus/platform/devices/VPC2004:00/conservation_mode"), bool preview = false)
        : control(nullptr, path, preview ? "/bin/false" : "/usr/bin/pkexec",
                  preview ? QStringList{} : QStringList{"/usr/local/lib/lenovo-modes/bateria-control"}) {
        window.setWindowTitle(message("Battery conservation")); window.resize(440,280);
        auto *layout=new QVBoxLayout(&window); layout->setContentsMargins(24,24,24,24);
        auto *title=new QLabel(message("Battery conservation"));
        auto font=title->font(); font.setPointSize(18); font.setBold(true); title->setFont(font);
        layout->addWidget(title);
        stateLabel=new QLabel; stateLabel->setWordWrap(true); layout->addWidget(stateLabel);
        auto *description=new QLabel(message("Limit charging to 80% to conserve your battery, or allow a full charge when needed."));
        description->setWordWrap(true); layout->addWidget(description);
        errorLabel=new QLabel; errorLabel->setWordWrap(true); layout->addWidget(errorLabel);
        button=new QPushButton; button->setMinimumHeight(40); layout->addWidget(button);
        connect(button,&QPushButton::clicked,this,[this]{ control.setEnabled(control.state()!=1); });
        status=menu.addAction(""); status->setEnabled(false); menu.addSeparator();
        limit=menu.addAction(message("Limit charge to 80%")); limit->setCheckable(true);
        full=menu.addAction(message("Allow charging to 100%")); full->setCheckable(true);
        connect(limit,&QAction::triggered,this,[this]{control.setEnabled(true);});
        connect(full,&QAction::triggered,this,[this]{control.setEnabled(false);});
        menu.addSeparator();
        connect(menu.addAction(message("Open controls")),&QAction::triggered,this,&BatteryApp::Present);
        quit=menu.addAction(message("Quit")); connect(quit,&QAction::triggered,qApp,&QApplication::quit);
        tray.setContextMenu(&menu);
        connect(&tray,&QSystemTrayIcon::activated,this,[this](QSystemTrayIcon::ActivationReason reason){
            if(reason==QSystemTrayIcon::Trigger || reason==QSystemTrayIcon::DoubleClick) Present();
        });
        connect(&control,&ConservationControl::changed,this,[this]{
            update();
            if (!control.error().isEmpty()) Present();
        });
        update(); if (!preview) tray.show();
    }
    bool savePreview(const QString &path) {
        if (button->text() != message("Limit charge to 80%")) return false;
        fprintf(stdout, "%s\n", qPrintable(button->text()));
        return window.grab().save(path);
    }
public slots:
    void Present() { control.refresh(); update(); window.show(); window.raise(); window.activateWindow(); }
private:
    void update() {
        const int state=control.state(); const bool pending=control.pending();
        const auto text=state==1 ? message("Battery conservation enabled")
            : state==0 ? message("Off · Charging to 100% allowed") : message("Battery conservation is unavailable");
        const auto icon=batteryIcon(state); tray.setIcon(icon); window.setWindowIcon(icon);
        tray.setToolTip(message("Battery conservation")+"\n"+text); status->setText(text);
        stateLabel->setText(pending ? message("Applying charge limit…") : text);
        errorLabel->setText(control.error()); errorLabel->setVisible(!control.error().isEmpty());
        limit->setChecked(state==1); full->setChecked(state==0);
        limit->setEnabled(!pending && state>=0); full->setEnabled(!pending && state>=0);
        button->setText(state==1 ? message("Allow charging to 100%") : message("Limit charge to 80%"));
        button->setEnabled(!pending && state>=0); quit->setEnabled(!pending);
    }
    ConservationControl control;
    QWidget window;
    QSystemTrayIcon tray;
    QMenu menu;
    QLabel *stateLabel, *errorLabel;
    QPushButton *button;
    QAction *status, *limit, *full, *quit;
};
int main(int argc,char **argv) {
    QApplication app(argc,argv);
    app.setApplicationName("Toggle Power"); app.setDesktopFileName("lenovo-bateria");
    app.setQuitOnLastWindowClosed(false);
    if (app.arguments().size()==3 && app.arguments().at(1)=="--preview") {
        QTemporaryDir directory;
        QFile mock(directory.filePath("state"));
        if (!mock.open(QIODevice::WriteOnly)) return 1;
        mock.write("0\n"); mock.close();
        BatteryApp controller(mock.fileName(), true);
        controller.Present();
        QTimer::singleShot(500,&app,[&]{ app.exit(controller.savePreview(app.arguments().at(2)) ? 0 : 2); });
        return app.exec();
    }
    auto bus=QDBusConnection::sessionBus(); if(!bus.isConnected()) return 1;
    if(!bus.registerService(busName)) {
        if(app.arguments().contains("--background")) return 0;
        QDBusInterface existing(busName,"/Battery",busName,bus);
        return existing.call("Present").type()==QDBusMessage::ErrorMessage ? 1 : 0;
    }
    BatteryApp controller;
    bus.registerObject("/Battery",&controller,QDBusConnection::ExportAllSlots);
    if(!app.arguments().contains("--background")) controller.Present();
    return app.exec();
}
#include "bateria_tray.moc"
