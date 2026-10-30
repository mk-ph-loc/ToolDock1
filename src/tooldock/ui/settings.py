"""Παράθυρο ρυθμίσεων: παράθυρο, dock, κουμπιά, Windows και φωνητικές εντολές."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from tooldock.core import system
from tooldock.core.commands import CommandEngine
from tooldock.core.geometry import float_size, thickness_for, with_thickness
from tooldock.ui.shell import MODES, SIDES


def _spin(lo: int, hi: int, val: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(lo, hi)
    spin.setValue(int(val))
    return spin


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
        self.screen = QComboBox()
        self.screen.addItem("Αυτόματη (όπου βρίσκεται)", "auto")
        for index, screen in enumerate(QGuiApplication.screens()):
            self.screen.addItem(f"{index}: {screen.name()} ({screen.geometry().width()}x{screen.geometry().height()})", index)
        idx = self.screen.findData(cfg.get("ui.screen", "auto"))
        self.screen.setCurrentIndex(max(0, idx))
        self.ontop = QCheckBox("Always on top"); self.ontop.setChecked(cfg.get("ui.always_on_top"))
        f1.addRow("Mode", self.mode); f1.addRow("Θέση (float / dock)", self.state)
        f1.addRow("Οθόνη", self.screen); f1.addRow(self.ontop)
        g1.setLayout(f1); lay.addWidget(g1)

        # --- Float ---
        fl = cfg.get("ui.float")
        g2, f2 = QGroupBox("Float: θέση και μέγεθος (το μέγεθος ισχύει για το επιλεγμένο mode)"), QFormLayout()
        self.fx, self.fy = _spin(-10000, 20000, fl.get("x", 100)), _spin(-10000, 20000, fl.get("y", 100))
        self.fw, self.fh = _spin(120, 5000, 380), _spin(40, 5000, 260)
        f2.addRow("x", self.fx); f2.addRow("y", self.fy); f2.addRow("πλάτος", self.fw); f2.addRow("ύψος", self.fh)
        current = QPushButton("Πάρε τρέχουσα θέση/μέγεθος"); current.clicked.connect(self._take_current)
        f2.addRow(current); g2.setLayout(f2); lay.addWidget(g2)

        # --- Dock ---
        dock = cfg.get("ui.dock")
        g3, f3 = QGroupBox("Dock (το πάχος αλλάζει και σέρνοντας τη λαβή στην εσωτερική άκρη)"), QFormLayout()
        self.th = _spin(60, 3000, 360)
        self.ms, self.me = _spin(0, 5000, dock["margin_start"]), _spin(0, 5000, dock["margin_end"])
        f3.addRow("Πάχος (πλάτος αν αριστ./δεξιά, ύψος αν πάνω/κάτω)", self.th)
        f3.addRow("Περιθώριο αρχής (πάνω ή αριστερά)", self.ms)
        f3.addRow("Περιθώριο τέλους (κάτω ή δεξιά)", self.me)
        self.auto_note = QLabel("Mode buttons: το μέγεθος προσαρμόζεται αυτόματα στα κουμπιά.")
        f3.addRow(self.auto_note)
        g3.setLayout(f3); lay.addWidget(g3)
        self.mode.currentTextChanged.connect(self._refresh_mode_fields)
        self._refresh_mode_fields(self.mode.currentText())

        # --- Κουμπιά ---
        g4, layout4 = QGroupBox("Κουμπιά λωρίδας"), QHBoxLayout()
        self.btn_checks: dict[str, QCheckBox] = {}
        for button in cfg.get("ui.buttons"):
            check = QCheckBox(button["id"]); check.setChecked(button.get("enabled", True))
            self.btn_checks[button["id"]] = check; layout4.addWidget(check)
        self.sysbtn = QCheckBox("📌 ◧ ⚙"); self.sysbtn.setChecked(cfg.get("ui.show_system_buttons"))
        layout4.addWidget(self.sysbtn); g4.setLayout(layout4); lay.addWidget(g4)

        # --- Γρήγορες ενέργειες / Windows ---
        g5, f5 = QGroupBox("Γρήγορες ενέργειες & Windows"), QFormLayout()
        self.dl = QLineEdit(cfg.get("quick_actions.downloads_path"))
        self.urls = QLineEdit(" ".join(cfg.get("quick_actions.browser_urls")))
        self.auto = QCheckBox("Εκκίνηση με τα Windows"); self.auto.setChecked(cfg.get("autostart"))
        f5.addRow("Φάκελος Downloads (κενό=προεπιλογή)", self.dl)
        f5.addRow("Σελίδες browser (με κενό)", self.urls); f5.addRow(self.auto)
        shortcut = QPushButton("Δημιουργία συντόμευσης επιφάνειας εργασίας")
        shortcut.clicked.connect(self._shortcut)
        f5.addRow(shortcut); g5.setLayout(f5); lay.addWidget(g5)

        # --- Φωνητικές εντολές ---
        g6, layout6 = QGroupBox("Φωνητικές εντολές"), QVBoxLayout()
        command_row = QHBoxLayout()
        self.cmd_enabled = QCheckBox("Ενεργές")
        self.cmd_enabled.setChecked(cfg.get("commands.enabled", True))
        self.cmd_mode = QComboBox()
        for value, label_text in (("auto", "Αυτόματο"), ("text_only", "Μόνο κείμενο"),
                                  ("commands_only", "Μόνο εντολές")):
            self.cmd_mode.addItem(label_text, value)
        self.cmd_mode.setCurrentIndex(max(0, self.cmd_mode.findData(cfg.get("commands.mode", "auto"))))
        self.cmd_threshold = _spin(50, 100, int(cfg.get("commands.threshold", 80)))
        command_row.addWidget(self.cmd_enabled); command_row.addWidget(QLabel("Λειτουργία:"))
        command_row.addWidget(self.cmd_mode); command_row.addWidget(QLabel("Κατώφλι:"))
        command_row.addWidget(self.cmd_threshold); command_row.addStretch(1)
        layout6.addLayout(command_row)

        self.cmd_table = QTableWidget(0, 6)
        self.cmd_table.setHorizontalHeaderLabels(
            ["Ενεργή", "Εντολή", "Φράσεις (;)", "Ενέργειες (;)", "Άμεση", "Ήχος"])
        self.cmd_table.horizontalHeader().setStretchLastSection(True)
        layout6.addWidget(self.cmd_table)
        self._fill_commands()

        command_buttons = QHBoxLayout()
        add_command = QPushButton("Προσθήκη εντολής")
        add_command.clicked.connect(self._add_command)
        delete_command = QPushButton("Διαγραφή επιλεγμένης")
        delete_command.clicked.connect(self._delete_command)
        command_buttons.addWidget(add_command)
        command_buttons.addWidget(delete_command)
        command_buttons.addStretch(1)
        layout6.addLayout(command_buttons)

        test_row = QHBoxLayout()
        self.cmd_test = QLineEdit()
        self.cmd_test.setPlaceholderText("Γράψε φράση για δοκιμή ταύτισης…")
        test_button = QPushButton("Δοκιμή")
        test_button.clicked.connect(self._test_command)
        test_row.addWidget(self.cmd_test, 1); test_row.addWidget(test_button)
        layout6.addLayout(test_row)
        g6.setLayout(layout6); lay.addWidget(g6, 1)

        if not CommandEngine(cfg).available():
            warning = QLabel("Προειδοποίηση: το rapidfuzz δεν είναι εγκατεστημένο. "
                             "Εγκατάσταση: pip install -r requirements-commands.txt")
            warning.setWordWrap(True)
            lay.addWidget(warning)

        self.msg = QLabel("")
        apply_button = QPushButton("Εφαρμογή & αποθήκευση")
        apply_button.clicked.connect(self._apply)
        lay.addWidget(apply_button); lay.addWidget(self.msg)

    def _fill_commands(self) -> None:
        """Γεμίζει τον πίνακα εντολών από το config."""
        items = self.ctx.cfg.get("commands.items", [])
        self.cmd_table.setRowCount(len(items))
        for row, item in enumerate(items):
            enabled = QTableWidgetItem()
            enabled.setCheckState(Qt.CheckState.Checked if item.get("enabled", True) else Qt.CheckState.Unchecked)
            immediate = QTableWidgetItem()
            immediate.setCheckState(Qt.CheckState.Checked if item.get("immediate", False) else Qt.CheckState.Unchecked)
            immediate.setToolTip("Αν ενεργό, η εντολή εκτελείται αμέσως μετά την ταύτιση, χωρίς OK.")
            sound = QTableWidgetItem()
            sound.setCheckState(Qt.CheckState.Checked if item.get("sound", False) else Qt.CheckState.Unchecked)
            values = [
                enabled,
                QTableWidgetItem(str(item.get("id", ""))),
                QTableWidgetItem(";".join(item.get("phrases", []))),
                QTableWidgetItem(";".join(str(argument) for argument in item.get("args", []))),
                immediate,
                sound,
            ]
            for column, cell in enumerate(values):
                self.cmd_table.setItem(row, column, cell)

    def _commands_from_table(self) -> list[dict]:
        """Διαβάζει τις εντολές από τον πίνακα."""
        items: list[dict] = []
        for row in range(self.cmd_table.rowCount()):
            command_id = self.cmd_table.item(row, 1).text().strip()
            if not command_id:
                continue
            phrases = [phrase.strip() for phrase in self.cmd_table.item(row, 2).text().split(";") if phrase.strip()]
            args = [argument.strip() for argument in self.cmd_table.item(row, 3).text().split(";") if argument.strip()]
            items.append({
                "id": command_id,
                "enabled": self.cmd_table.item(row, 0).checkState() == Qt.CheckState.Checked,
                "phrases": phrases,
                "args": args,
                "immediate": self.cmd_table.item(row, 4).checkState() == Qt.CheckState.Checked,
                "sound": self.cmd_table.item(row, 5).checkState() == Qt.CheckState.Checked,
                "confirm": not self.cmd_table.item(row, 4).checkState() == Qt.CheckState.Checked,
            })
        return items

    def _add_command(self) -> None:
        """Προσθέτει κενή εγγραφή εντολής στον πίνακα."""
        row = self.cmd_table.rowCount()
        self.cmd_table.insertRow(row)
        enabled = QTableWidgetItem()
        enabled.setCheckState(Qt.CheckState.Checked)
        immediate = QTableWidgetItem()
        immediate.setCheckState(Qt.CheckState.Unchecked)
        immediate.setToolTip("Αν ενεργό, η εντολή εκτελείται αμέσως μετά την ταύτιση, χωρίς OK.")
        sound = QTableWidgetItem()
        sound.setCheckState(Qt.CheckState.Unchecked)
        values = [enabled, QTableWidgetItem(f"command_{row + 1}"), QTableWidgetItem(),
                  QTableWidgetItem(), immediate, sound]
        for column, cell in enumerate(values):
            self.cmd_table.setItem(row, column, cell)
        self.cmd_table.setCurrentCell(row, 1)

    def _delete_command(self) -> None:
        """Διαγράφει την επιλεγμένη εγγραφή εντολής."""
        row = self.cmd_table.currentRow()
        if row >= 0:
            self.cmd_table.removeRow(row)

    def _test_command(self) -> None:
        """Δοκιμή ταύτισης χωρίς εκτέλεση."""
        try:
            match = CommandEngine(self.ctx.cfg).match(self.cmd_test.text())
        except RuntimeError as exc:
            self.msg.setText(str(exc))
            return
        if match is None:
            self.msg.setText("Δεν βρέθηκε εντολή πάνω από το κατώφλι.")
        else:
            self.msg.setText(f"Εντολή: {match.command.get('id', '')} · φράση: {match.phrase} · {match.score:.0f}%")

    def _refresh_mode_fields(self, mode: str) -> None:
        """Γεμίζει μέγεθος/πάχος του επιλεγμένου mode· στο buttons είναι αυτόματα."""
        cfg = self.ctx.cfg
        automatic = mode == "buttons"
        for widget in (self.fw, self.fh, self.th):
            widget.setEnabled(not automatic)
        self.auto_note.setVisible(automatic)
        if not automatic:
            width, height = float_size(cfg.get("ui.float", {}), mode)
            self.fw.setValue(width); self.fh.setValue(height)
            self.th.setValue(thickness_for(cfg.get("ui.dock.thickness"), mode))

    def _take_current(self) -> None:
        geometry = self.shell.geometry()
        self.fx.setValue(geometry.x()); self.fy.setValue(geometry.y())
        if self.mode.currentText() != "buttons":
            self.fw.setValue(geometry.width()); self.fh.setValue(geometry.height())

    def _shortcut(self) -> None:
        ok = system.create_desktop_shortcut(self.ctx.cfg.root)
        self.msg.setText("Η συντόμευση δημιουργήθηκε." if ok else "Αποτυχία δημιουργίας συντόμευσης (δες logs).")

    def _apply(self) -> None:
        cfg = self.ctx.cfg
        mode = self.mode.currentText()
        cfg.set("ui.mode", mode); cfg.set("ui.dock.state", self.state.currentText())
        cfg.set("ui.screen", self.screen.currentData())
        cfg.set("ui.always_on_top", self.ontop.isChecked())
        float_config = dict(cfg.get("ui.float", {}))
        float_config["x"], float_config["y"] = self.fx.value(), self.fy.value()
        if mode != "buttons":
            sizes = dict(float_config.get("sizes", {}))
            sizes[mode] = {"w": self.fw.value(), "h": self.fh.value()}
            float_config["sizes"] = sizes
            cfg.set("ui.dock.thickness", with_thickness(cfg.get("ui.dock.thickness"), mode, self.th.value()))
        cfg.set("ui.float", float_config)
        cfg.set("ui.dock.margin_start", self.ms.value()); cfg.set("ui.dock.margin_end", self.me.value())
        cfg.set("ui.buttons", [{"id": key, "enabled": check.isChecked()} for key, check in self.btn_checks.items()])
        cfg.set("ui.show_system_buttons", self.sysbtn.isChecked())
        cfg.set("quick_actions.downloads_path", self.dl.text().strip())
        cfg.set("quick_actions.browser_urls", self.urls.text().split())
        cfg.set("commands.enabled", self.cmd_enabled.isChecked())
        cfg.set("commands.mode", self.cmd_mode.currentData())
        cfg.set("commands.threshold", self.cmd_threshold.value())
        cfg.set("commands.items", self._commands_from_table())
        if self.auto.isChecked() != cfg.get("autostart"):
            ok = system.set_autostart(self.auto.isChecked(), cfg.root)
            if ok:
                cfg.set("autostart", self.auto.isChecked())
            else:
                self.msg.setText("Αποτυχία autostart."); self.auto.setChecked(cfg.get("autostart"))
        cfg.save()
        self.shell.rebuild()
        self.msg.setText("Αποθηκεύτηκε.")
