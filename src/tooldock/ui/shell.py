"""Κύριο παράθυρο: 3 modes, float ή dock σε πλευρά/οθόνη, always-on-top, auto-fit, λαβή πάχους."""
from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QBoxLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget)

from tooldock.core.geometry import (MIN_THICKNESS, clamp_rect, dock_rect, float_size,
                                    thickness_for, with_thickness)

log = logging.getLogger("tooldock.shell")
MODES = ["buttons", "compact", "full"]
SIDES = ["left", "right", "top", "bottom"]
TITLEBAR = 32  # ΠΡΟΣΟΧΗ: περιθώριο τίτλου ώστε το float παράθυρο να μη βγαίνει πάνω από την οθόνη


class Grip(QWidget):
    """Λαβή στην εσωτερική άκρη του dock: σύρσιμο = αλλαγή πάχους (π.χ. dock δεξιά -> αριστερή πλευρά)."""
    SIZE = 6

    def __init__(self, shell: "Shell", side: str) -> None:
        super().__init__()
        self.shell = shell
        horiz = side in ("left", "right")
        self.setCursor(Qt.SizeHorCursor if horiz else Qt.SizeVerCursor)
        if horiz:
            self.setFixedWidth(self.SIZE)
        else:
            self.setFixedHeight(self.SIZE)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background:#8aa4d6;")
        self.setToolTip("Σύρε για αλλαγή πάχους")

    def mouseMoveEvent(self, e) -> None:
        self.shell.resize_dock_to(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e) -> None:
        self.shell.ctx.cfg.save()


class Shell(QWidget):
    def __init__(self, ctx, plugins) -> None:
        super().__init__()
        self.ctx, self.plugins = ctx, plugins
        self.setWindowTitle("ToolDock")
        self._settings = None
        self._applying = False
        self.status = QLabel("")
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._persist_float)
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
        docked = side in SIDES
        direction = QBoxLayout.TopToBottom if side in ("top", "bottom") else QBoxLayout.LeftToRight
        outer = QBoxLayout(direction, self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 4, 4)
        grip = Grip(self, side) if docked else None
        if grip and side in ("right", "bottom"):
            outer.addWidget(grip)
        outer.addWidget(content, 1)
        if grip and side in ("left", "top"):
            outer.addWidget(grip)

        by_id = {a.id: a for p in self.plugins for a in p.actions()}
        vertical = mode == "buttons" and side in ("left", "right")
        strip = QVBoxLayout() if vertical else QHBoxLayout()
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

    # ---------- οθόνη / γεωμετρία ----------
    def _target_screen(self):
        """Οθόνη-στόχος: ui.screen = αριθμός, ή «auto» = όπου βρίσκεται το παράθυρο."""
        cfg = self.ctx.cfg
        screens = QGuiApplication.screens()
        sel = cfg.get("ui.screen", "auto")
        if isinstance(sel, int) and not isinstance(sel, bool) and 0 <= sel < len(screens):
            return screens[sel]
        scr = None
        if self.isVisible():
            scr = self.screen()
        else:
            f = cfg.get("ui.float", {})
            scr = QGuiApplication.screenAt(QPoint(int(f.get("x", 100)) + 20, int(f.get("y", 100)) + 20))
        return scr or QGuiApplication.primaryScreen()

    def target_rect(self) -> QRect:
        cfg = self.ctx.cfg
        mode = cfg.get("ui.mode", "compact")
        d = cfg.get("ui.dock", {})
        state = d.get("state", "float")
        a = self._target_screen().availableGeometry()
        area = (a.x(), a.y(), a.width(), a.height())
        fit = self.layout().sizeHint() if (mode == "buttons" and self.layout() is not None) else None
        if state not in SIDES:
            f = cfg.get("ui.float", {})
            w, h = (fit.width(), fit.height()) if fit else float_size(f, mode)
            farea = (a.x(), a.y() + TITLEBAR, a.width(), a.height() - TITLEBAR)
            return QRect(*clamp_rect((int(f.get("x", 100)), int(f.get("y", 100)), w, h), farea))
        if fit:
            t = fit.width() if state in ("left", "right") else fit.height()
        else:
            t = thickness_for(d.get("thickness"), mode)
        return QRect(*dock_rect(area, state, t, int(d.get("margin_start", 0)), int(d.get("margin_end", 0))))

    def apply_window(self) -> None:
        """Εφαρμόζει flags (on-top, frameless όταν docked) και γεωμετρία στη σωστή οθόνη."""
        cfg = self.ctx.cfg
        docked = cfg.get("ui.dock.state", "float") in SIDES
        flags = Qt.Window
        if cfg.get("ui.always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        if docked:
            flags |= Qt.FramelessWindowHint
        was_visible = self.isVisible()
        self._applying = True
        self.setWindowFlags(flags)
        self.setGeometry(self.target_rect())
        if was_visible or not cfg.get("ui.start_hidden", False):
            self.show()
        QTimer.singleShot(0, self._place)

    def _place(self) -> None:
        """Δεύτερο πέρασμα μετά το show: σωστή οθόνη (DPI) και γεωμετρία. Λύνει το «περνά στην άλλη οθόνη»."""
        scr = self._target_screen()
        wh = self.windowHandle()
        if wh is not None and wh.screen() is not scr:
            wh.setScreen(scr)
        self.setGeometry(self.target_rect())
        self._applying = False

    def resize_dock_to(self, p: QPoint) -> None:
        """Καλείται από τη λαβή: νέο πάχος από τη θέση του ποντικιού (ανά mode)."""
        cfg = self.ctx.cfg
        mode, side = cfg.get("ui.mode", "compact"), cfg.get("ui.dock.state", "float")
        if mode == "buttons" or side not in SIDES:
            return
        a = self._target_screen().availableGeometry()
        t = {"right": a.right() + 1 - p.x(), "left": p.x() - a.x(),
             "top": p.y() - a.y(), "bottom": a.bottom() + 1 - p.y()}[side]
        cfg.set("ui.dock.thickness", with_thickness(cfg.get("ui.dock.thickness"), mode, max(MIN_THICKNESS, int(t))))
        self.setGeometry(self.target_rect())

    # ---------- αποθήκευση θέσης/μεγέθους float ----------
    def _remember_size(self) -> None:
        """Κρατά θέση και μέγεθος (ανά mode· το buttons δεν αποθηκεύει μέγεθος)."""
        cfg = self.ctx.cfg
        if cfg.get("ui.dock.state", "float") != "float" or not self.isVisible():
            return
        g = self.geometry()
        f = dict(cfg.get("ui.float", {}))
        f["x"], f["y"] = g.x(), g.y()
        mode = cfg.get("ui.mode", "compact")
        if mode != "buttons":
            sizes = dict(f.get("sizes", {}))
            sizes[mode] = {"w": g.width(), "h": g.height()}
            f["sizes"] = sizes
        cfg.set("ui.float", f)

    def _persist_float(self) -> None:
        self._remember_size()
        self.ctx.cfg.save()

    def _schedule_save(self) -> None:
        if not self._applying and self.isVisible():
            self._save_timer.start()

    def moveEvent(self, e) -> None:
        super().moveEvent(e)
        self._schedule_save()

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._schedule_save()

    # ---------- ενέργειες ----------
    def set_dock(self, state: str) -> None:
        self._remember_size()
        self.ctx.cfg.set("ui.dock.state", state)
        self.ctx.cfg.save()
        self.rebuild()

    def set_screen(self, sel) -> None:
        """sel: «auto» ή αριθμός οθόνης."""
        self.ctx.cfg.set("ui.screen", sel)
        self.ctx.cfg.save()
        self.apply_window()

    def toggle_on_top(self) -> None:
        self.ctx.cfg.set("ui.always_on_top", not self.ctx.cfg.get("ui.always_on_top", True))
        self.ctx.cfg.save()
        self.apply_window()

    def set_mode(self, mode: str) -> None:
        self._remember_size()
        self.ctx.cfg.set("ui.mode", mode)
        self.ctx.cfg.save()
        self.rebuild()

    def cycle_mode(self) -> None:
        cur = self.ctx.cfg.get("ui.mode", "compact")
        self.set_mode(MODES[(MODES.index(cur) + 1) % len(MODES)])

    def open_settings(self) -> None:
        from tooldock.ui.settings import SettingsDialog  # lazy
        if self._settings is not None:
            try:
                if self._settings.isVisible():
                    self._settings.raise_()
                    self._settings.activateWindow()
                    return
            except RuntimeError:  # το παράθυρο έχει ήδη καταστραφεί
                self._settings = None
        self._remember_size()
        self._settings = SettingsDialog(self.ctx, self)
        self._settings.setAttribute(Qt.WA_DeleteOnClose, True)
        self._settings.destroyed.connect(lambda *_: setattr(self, "_settings", None))
        self._settings.show()

    def bring_front(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _set_status(self, msg: str) -> None:
        try:
            self.status.setText(msg)
        except RuntimeError:
            pass

    def closeEvent(self, e) -> None:
        """Κλείσιμο -> tray (η έξοδος γίνεται από το μενού του tray)."""
        self._persist_float()
        e.ignore()
        self.hide()
