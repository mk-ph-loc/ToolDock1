"""Παράθυρο ρυθμίσεων: dock/θέση/διαστάσεις, κουμπιά, autostart, συντόμευση."""
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout)

from tooldock.core import system
from tooldock.ui.shell import MODES, SIDES


def _spin(lo: int, hi: int, val: int) -> QSpinBox:
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setValue(int(val))
    return s


class SettingsDialog(QDialog):
    def __init__(self, ctx, shell) -> None:
        super().__init__(shell)
        self.ctx, self.shell = ctx, shell
        cfg = ctx.cfg
        self.setWindowTitle("ToolDock — Ρυθμίσεις")
        lay = QVBoxLayout(self)

        # --- Παράθυρο ---
        g1, f1 = QGroupBox("Παράθυρο"), QFormLayout()
        self.mode = QComboBox(); self.mode.addItems(MODES); self.mode.setCurrentText(cfg.get("ui.mode"))
        self.state = QComboBox(); self.state.addItems(["float"] + SIDES)
        self.state.setCurrentText(cfg.get("ui.dock.state"))
        self.ontop = QCheckBox("Always on top"); self.ontop.setChecked(cfg.get("ui.always_on_top"))
        f1.addRow("Mode", self.mode); f1.addRow("Θέση (float / dock)", self.state); f1.addRow(self.ontop)
        g1.setLayout(f1); lay.addWidget(g1)

        # --- Float ---
        g2, f2 = QGroupBox("Float: θέση και διαστάσεις"), QFormLayout()
        fl = cfg.get("ui.float")
        self.fx, self.fy = _spin(-5000, 10000, fl["x"]), _spin(-5000, 10000, fl["y"])
        self.fw, self.fh = _spin(120, 5000, fl["w"]), _spin(40, 5000, fl["h"])
        f2.addRow("x", self.fx); f2.addRow("y", self.fy); f2.addRow("πλάτος", self.fw); f2.addRow("ύψος", self.fh)
        cur = QPushButton("Πάρε τρέχουσα θέση/μέγεθος"); cur.clicked.connect(self._take_current)
        f2.addRow(cur); g2.setLayout(f2); lay.addWidget(g2)

        # --- Dock ---
        g3, f3 = QGroupBox("Dock: πάχος και περιθώρια"), QFormLayout()
        d = cfg.get("ui.dock")
        self.th = _spin(60, 3000, d["thickness"])
        self.ms, self.me = _spin(0, 5000, d["margin_start"]), _spin(0, 5000, d["margin_end"])
        f3.addRow("Πάχος (πλάτος αν αριστ./δεξιά, ύψος αν πάνω/κάτω)", self.th)
        f3.addRow("Περιθώριο αρχής (πάνω ή αριστερά)", self.ms)
        f3.addRow("Περιθώριο τέλους (κάτω ή δεξιά)", self.me)
        g3.setLayout(f3); lay.addWidget(g3)

        # --- Κουμπιά ---
        g4, l4 = QGroupBox("Κουμπιά λωρίδας"), QHBoxLayout()
        self.btn_checks: dict[str, QCheckBox] = {}
        for b in cfg.get("ui.buttons"):
            c = QCheckBox(b["id"]); c.setChecked(b.get("enabled", True))
            self.btn_checks[b["id"]] = c; l4.addWidget(c)
        self.sysbtn = QCheckBox("📌 ◧ ⚙"); self.sysbtn.setChecked(cfg.get("ui.show_system_buttons"))
        l4.addWidget(self.sysbtn); g4.setLayout(l4); lay.addWidget(g4)

        # --- Quick actions / Windows ---
        g5, f5 = QGroupBox("Γρήγορες ενέργειες & Windows"), QFormLayout()
        self.dl = QLineEdit(cfg.get("quick_actions.downloads_path"))
        self.urls = QLineEdit(" ".join(cfg.get("quick_actions.browser_urls")))
        self.auto = QCheckBox("Εκκίνηση με τα Windows"); self.auto.setChecked(cfg.get("autostart"))
        f5.addRow("Φάκελος Downloads (κενό=προεπιλογή)", self.dl)
        f5.addRow("Σελίδες browser (με κενό)", self.urls); f5.addRow(self.auto)
        sc = QPushButton("Δημιουργία συντόμευσης επιφάνειας εργασίας"); sc.clicked.connect(self._shortcut)
        f5.addRow(sc); g5.setLayout(f5); lay.addWidget(g5)

        self.msg = QLabel("")
        apply_ = QPushButton("Εφαρμογή & αποθήκευση"); apply_.clicked.connect(self._apply)
        lay.addWidget(apply_); lay.addWidget(self.msg)

    def _take_current(self) -> None:
        g = self.shell.geometry()
        self.fx.setValue(g.x()); self.fy.setValue(g.y()); self.fw.setValue(g.width()); self.fh.setValue(g.height())

    def _shortcut(self) -> None:
        ok = system.create_desktop_shortcut(self.ctx.cfg.root)
        self.msg.setText("Η συντόμευση δημιουργήθηκε." if ok else "Αποτυχία δημιουργίας συντόμευσης (δες logs).")

    def _apply(self) -> None:
        c = self.ctx.cfg
        c.set("ui.mode", self.mode.currentText()); c.set("ui.dock.state", self.state.currentText())
        c.set("ui.always_on_top", self.ontop.isChecked())
        c.set("ui.float", {"x": self.fx.value(), "y": self.fy.value(), "w": self.fw.value(), "h": self.fh.value()})
        c.set("ui.dock.thickness", self.th.value()); c.set("ui.dock.margin_start", self.ms.value())
        c.set("ui.dock.margin_end", self.me.value())
        c.set("ui.buttons", [{"id": k, "enabled": v.isChecked()} for k, v in self.btn_checks.items()])
        c.set("ui.show_system_buttons", self.sysbtn.isChecked())
        c.set("quick_actions.downloads_path", self.dl.text().strip())
        c.set("quick_actions.browser_urls", self.urls.text().split())
        if self.auto.isChecked() != c.get("autostart"):
            ok = system.set_autostart(self.auto.isChecked(), c.root)
            if ok:
                c.set("autostart", self.auto.isChecked())
            else:
                self.msg.setText("Αποτυχία autostart."); self.auto.setChecked(c.get("autostart"))
        c.save()
        self.shell.rebuild()
        self.msg.setText("Αποθηκεύτηκε.")
