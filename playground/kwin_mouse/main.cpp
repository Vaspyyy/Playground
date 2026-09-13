// Read-only KWin input observation. Never grabs, filters, or reinjects input.
#include <effect/effect.h>
#include <effect/effecthandler.h>
#include <effect/effectwindow.h>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>

namespace KWin {
class PlaygroundMouse : public Effect {
    Q_OBJECT
    QTimer timer;
public:
    PlaygroundMouse() {
        connect(effects, &EffectsHandler::mouseChanged, this,
            [this](const auto &, const auto &, Qt::MouseButtons buttons,
                   Qt::MouseButtons oldButtons, auto, auto) {
                const int pressed = int(buttons & ~oldButtons);
                if (pressed) frame(pressed);
            });
        connect(&timer, &QTimer::timeout, this, [this] { frame(0); });
        timer.start(16);
    }
    // This bridge has no painting work and never occupies the effect chain.
    bool isActive() const override { return false; }
    void frame(int pressed) {
        const bool locked = effects->isScreenLocked();
        const auto pos = effects->cursorPos();
        QJsonObject data{{"x", locked ? 0. : pos.x()}, {"y", locked ? 0. : pos.y()},
                         {"pressed", locked ? 0 : pressed}, {"locked", locked}};
        const auto w = effects->activeWindow();
        if (w && w->isFullScreen()) {
            const auto g = w->frameGeometry();
            data["fullscreen"] = QJsonArray{g.x(),g.y(),g.width(),g.height()};
        }
        auto message = QDBusMessage::createMethodCall(QStringLiteral("io.github.edgeglow"),
            QStringLiteral("/io/github/Playground/Pointer"),
            QStringLiteral("io.github.Playground.Pointer"), QStringLiteral("Frame"));
        message.setAutoStartService(false);
        message << QString::fromUtf8(QJsonDocument(data).toJson(QJsonDocument::Compact));
        QDBusConnection::sessionBus().call(message, QDBus::NoBlock);
    }
};
KWIN_EFFECT_FACTORY(PlaygroundMouse, "metadata.json")
}
#include "main.moc"
