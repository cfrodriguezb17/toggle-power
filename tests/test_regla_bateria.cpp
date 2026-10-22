#include <QCoreApplication>
#include <QFile>
#include <QJSEngine>
#include <cstdio>

int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    if (argc != 2) return 1;
    QFile rule(QString::fromLocal8Bit(argv[1]));
    if (!rule.open(QIODevice::ReadOnly)) return 1;
    QJSEngine engine;
    engine.evaluate("var polkit = {Result: {YES: 'yes'}, addRule: function(fn) {this.rule = fn;}};");
    const auto result = engine.evaluate(QString::fromUtf8(rule.readAll()));
    if (result.isError()) { fprintf(stderr, "%s\n", qPrintable(result.toString())); return 1; }
    auto callback = engine.globalObject().property("polkit").property("rule");
    struct Case { const char *action; const char *user; bool local, active, allowed; };
    const Case cases[] = {
        {"org.local.lenovo-modes.battery", "demo", true, true, true},
        {"org.local.lenovo-modes.battery", "another-user", true, true, false},
        {"org.local.lenovo-modes.battery", "demo", true, false, false},
        {"org.local.lenovo-modes.battery", "demo", false, true, false},
        {"org.local.lenovo-modes.battery", "demo", false, false, false},
        {"org.freedesktop.policykit.exec", "demo", true, true, false},
        {"org.local.lenovo-modes.battery.other", "demo", true, true, false},
    };
    for (const auto &test : cases) {
        auto action = engine.newObject(); action.setProperty("id", test.action);
        auto subject = engine.newObject();
        subject.setProperty("user", test.user); subject.setProperty("local", test.local); subject.setProperty("active", test.active);
        const auto answer = callback.call({action, subject});
        if (answer.isError() || (test.allowed ? answer.toString() != "yes" : !answer.isUndefined())) {
            fprintf(stderr, "Incorrect authorization for %s/%s, local=%d active=%d\n", test.action, test.user, test.local, test.active);
            return 1;
        }
    }
    puts("7 authorization cases passed.");
}
