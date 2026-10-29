"""Εκκίνηση: logging, config, single instance, plugins, tray, shell."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from tooldock import __version__
from tooldock.core.config import Config
from tooldock.core.events import EventBus
from tooldock.core.storage import Storage

SERVER_NAME = "ToolDock1-single-instance"


def make_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#2d6cdf")); p.setPen(Qt.NoPen); p.drawRoundedRect(4, 4, 56, 56, 12, 12)
    p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 28, QFont.Bold)); p.drawText(pm.rect(), Qt.AlignCenter, "T")
    p.end()
    return QIcon(pm)


def setup_logging(cfg: Config) -> None:
    logdir = cfg.data_dir / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    h = RotatingFileHandler(logdir / "tooldock.log", maxBytes=500_000, backupCount=3, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[h])


def already_running() -> bool:
    """Αν τρέχει άλλη εκτέλεση: της στέλνει «show» και επιστρέφει True."""
    s = QLocalSocket()
    s.connectToServer(SERVER_NAME)
    if s.waitForConnected(300):
        s.write(b"show"); s.flush(); s.waitForBytesWritten(300)
        return True
    return False


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ToolDock")
    if already_running():
        return 0
    QLocalServer.removeServer(SERVER_NAME)  # ΠΡΟΣΟΧΗ: καθαρισμός «κολλημένου» server μετά από crash
    server = QLocalServer()
    server.listen(SERVER_NAME)

    cfg = Config().load()
    setup_logging(cfg)
    log = logging.getLogger("tooldock")
    log.info("Εκκίνηση ToolDock v%s", __version__)
    storage = Storage(cfg)
    storage.ensure_files()
    ctx = SimpleNamespace(cfg=cfg, storage=storage, events=EventBus())

    from tooldock.tools import load_plugins
    from tooldock.ui.shell import MODES, Shell
    plugins = load_plugins(ctx)
    shell = Shell(ctx, plugins)
    app.setWindowIcon(make_icon())

    def on_conn() -> None:
        c = server.nextPendingConnection()
        if c:
            c.waitForReadyRead(200)
            shell.bring_front()
    server.newConnection.connect(on_conn)

    tray = QSystemTrayIcon(make_icon(), app)
    tray.setToolTip(f"ToolDock v{__version__}")
    menu = QMenu()
    menu.addAction("Εμφάνιση", shell.bring_front)
    mm = menu.addMenu("Mode")
    for m in MODES:
        mm.addAction(m, lambda m=m: shell.set_mode(m))
    dm = menu.addMenu("Θέση")
    for s in ["float", "left", "right", "top", "bottom"]:
        dm.addAction(s, lambda s=s: shell.set_dock(s))
    menu.addAction("Ρυθμίσεις", shell.open_settings)
    menu.addSeparator()
    menu.addAction("Έξοδος", app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda r: shell.bring_front() if r == QSystemTrayIcon.Trigger else None)
    tray.show()
    app._keep = (tray, menu, server)  # αποφυγή garbage collection
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
