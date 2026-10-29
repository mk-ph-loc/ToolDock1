"""Κύριο παράθυρο: 3 modes (buttons/compact/full), float ή dock σε πλευρά, always-on-top."""
from __future__ import annotations

import logging

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget)

log = logging.getLogger("tooldock.shell")
MODES = ["buttons", "compact", "full"]
SIDES = ["left", "right", "top", "bottom"]


class Shell(QWidget):
    def __init__(self, ctx, plugins) -> None:
        super().__init__()
        self.ctx, self.plugins = ctx, plugins
        self.setWindowTitle("ToolDock")
        self._settings = None
        ctx.events.status.connect(self._set_status)
        self.rebuild()

    # ---------- κατασκευή UI ----------
    def rebuild(self) -> None:
        """Ξαναχτίζει το περιεχόμενο (μετά από αλλαγή mode/ρυθμίσεων κουμπιών)."""
        cfg = self.ctx.cfg
        if self.layout() is not None:
            QWidget().setLayout(self.layout())  # αποδέσμευση παλιού layout
        mode = cfg.get("ui.mode", "compact")
        side = cfg.get("ui.dock.state", "float")
        vertical_strip = side in ("left", "right") or side == "float"
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        by_id = {a.id: a for p in self.plugins for a in p.actions()}

        strip = QHBoxLayout() if not (mode == "buttons" and side in ("left", "right")) else QVBoxLayout()
        for b in cfg.get("ui.buttons", []):
            a = by_id.get(b["id"])
            if a and b.get("enabled", True):
                btn = QPushButton(a.icon + ("" if mode == "buttons" else " " + a.label))
                btn.setToolTip(a.label)
                btn.clicked.connect(lambda _=False, f=a.run: f())
                strip.addWidget(btn)
        if cfg.get("ui.show_system_buttons", True):
            strip.addStretch(1)
            for icon, tip, fn in (
                ("📌", "Always on top", self.toggle_on_top),
                ("◧", "Αλλαγή mode", self.cycle_mode),
                ("⚙", "Ρυθμίσεις", self.open_settings),
            ):
                btn = QPushButton(icon)
                btn.setToolTip(tip)
                btn.setFixedWidth(34)
                btn.clicked.connect(lambda _=False, f=fn: f())
                strip.addWidget(btn)
        root.addLayout(strip)

        self.status = QLabel("")
        if mode != "buttons":
            for p in self.plugins:
                w = p.build_widget(mode)
                if w is not None:
                    root.addWidget(w, 1)
            root.addWidget(self.status)
        self.apply_window()

    # ---------- παράθυρο / dock ----------
    def apply_window(self) -> None:
        """Εφαρμόζει flags (on-top, frameless όταν docked) και γεωμετρία."""
        cfg = self.ctx.cfg
        d = cfg.get("ui.dock", {})
        docked = d.get("state", "float") in SIDES
        flags = Qt.Window
        if cfg.get("ui.always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        if docked:
            flags |= Qt.FramelessWindowHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        self.setGeometry(self.target_rect())
        if was_visible or not cfg.get("ui.start_hidden", False):
            self.show()

    def target_rect(self) -> QRect:
        cfg = self.ctx.cfg
        d = cfg.get("ui.dock", {})
        state = d.get("state", "float")
        if state not in SIDES:
            f = cfg.get("ui.float", {})
            return QRect(f["x"], f["y"], f["w"], f["h"])
        scr = (QGuiApplication.screenAt(self.geometry().center()) or QGuiApplication.primaryScreen())
        a = scr.availableGeometry()
        t, ms, me = int(d["thickness"]), int(d["margin_start"]), int(d["margin_end"])
        if state == "right":
            return QRect(a.right() + 1 - t, a.top() + ms, t, a.height() - ms - me)
        if state == "left":
            return QRect(a.left(), a.top() + ms, t, a.height() - ms - me)
        if state == "top":
            return QRect(a.left() + ms, a.top(), a.width() - ms - me, t)
        return QRect(a.left() + ms, a.bottom() + 1 - t, a.width() - ms - me, t)

    def save_float_geometry(self) -> None:
        g = self.geometry()
        self.ctx.cfg.set("ui.float", {"x": g.x(), "y": g.y(), "w": g.width(), "h": g.height()})

    def set_dock(self, state: str) -> None:
        if self.ctx.cfg.get("ui.dock.state") == "float":
            self.save_float_geometry()
        self.ctx.cfg.set("ui.dock.state", state)
        self.ctx.cfg.save()
        self.rebuild()

    # ---------- ενέργειες ----------
    def toggle_on_top(self) -> None:
        self.ctx.cfg.set("ui.always_on_top", not self.ctx.cfg.get("ui.always_on_top", True))
        self.ctx.cfg.save()
        self.apply_window()

    def set_mode(self, mode: str) -> None:
        self.ctx.cfg.set("ui.mode", mode)
        self.ctx.cfg.save()
        self.rebuild()

    def cycle_mode(self) -> None:
        cur = self.ctx.cfg.get("ui.mode", "compact")
        self.set_mode(MODES[(MODES.index(cur) + 1) % len(MODES)])

    def open_settings(self) -> None:
        from tooldock.ui.settings import SettingsDialog  # lazy
        self._settings = SettingsDialog(self.ctx, self)
        self._settings.show()

    def bring_front(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _set_status(self, msg: str) -> None:
        if self.status is not None:
            try:
                self.status.setText(msg)
            except RuntimeError:
                pass

    def closeEvent(self, e) -> None:
        """Κλείσιμο -> tray (η έξοδος γίνεται από το μενού του tray)."""
        if self.ctx.cfg.get("ui.dock.state", "float") == "float":
            self.save_float_geometry()
            self.ctx.cfg.save()
        e.ignore()
        self.hide()
