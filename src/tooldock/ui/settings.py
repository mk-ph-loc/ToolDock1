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

SEP = ";"  # διαχωριστής φράσεων και ορισμάτων στον πίνακα εντολών


def _spin(lo: int, hi: int, val: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(lo, hi)
    spin.setValue(val)
    return spin


def _check_item(checked: bool) -> QTableWidgetItem:
    """Κελί πίνακα με checkbox."""
    item = QTableWidgetItem()
    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
    item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
    return item


class SettingsDialog(QDialog):
    def __init__(self, ctx, shell) -> None:
        super().__init__(shell)
        self.ctx, self.shell = ctx, shell
        cfg = ctx.cfg
        self.setWindowTitle("ToolDock — Ρυθμίσεις")
        lay = QVBoxLayout(self)

        # --- Παράθυρο ---
        g1, f1 = QGroupBox("Παράθυρο"), QFormLayout()
        self.mode = QComboBox(); self.mode.addItems(MODES)
        self.mode.setCurrentText(cfg.get("ui.mode"))
        self.state = QComboBox(); self.state.addItems(["compact"] + SIDES)
        self.state.setCurrentText(cfg.get("ui.dock.state"))
        self.screen = QComboBox()
        self.screen.addItem("Αυτόματη (όπου βρίσκεται)", "auto")
        for index, screen in enumerate(QGuiApplication.screens()):
            self.screen.addItem(f"{index}: {screen.name()} ({screen.geometry().width()}x{screen.geometry().height()})", index)
        idx = self.screen.findData(cfg.get("ui.screen", "auto"))
        self.screen.setCurrentIndex(max(0, idx))
        self.ontop = QCheckBox("Always on top"); self.ontop.setChecked(cfg.get("ui.always_on_top"))
        f1.addRow("Mode", self.mode)
        f1.addRow("Θέση (compact / dock)", self.state)
        f1.addRow("Οθόνη", self.screen)
        f1.addRow(self.ontop)
        g1.setLayout(f1); lay.addWidget(g1)

        # --- Float ---
        fl = cfg.get("ui.float")
        g2, f2 = QGroupBox("Float: θέση και μέγεθος (το μέγεθος ισχύει για το επιλεγμένο mode)"), QFormLayout()
        self.fx, self.fy = _spin(0, 10000, 360), _spin(0, 10000, 260)
        current = QPushButton("Πάρε τρέχουσα θέση/μέγεθος"); current.clicked.connect(self._take_current)
        f2.addRow(current); g2.setLayout(f2); lay.addWidget(g2)

        # --- Dock ---
        dock = cfg.get("ui.dock")
        g3, f3 = QGroupBox("Dock (το πάχος αλλάζει και σέρνει τη λαβή στην εσωτερική άκρη)"), QFormLayout()
        self.th = _spin(0, 3000, 360)
        self.ms, self.me = _spin(0, 5000, 0), _spin(0, 5000, 0)
        f3.addRow("Πάχος (το πάχος αλλάζει και σέρνει τη λαβή στην εσωτερική άκρη)", self.th)
        f3.addRow("Περιθώριο αρχής (το πάχος αλλάζει και σέρνει τη λαβή στην εσωτερική άκρη)", self.ms)
        f3.addRow("Περιθώριο τέλους (το πάχος αλλάζει και σέρνει τη λαβή στην εσωτερική άκρη)", self.me)
        self.auto_note = QLabel("Mode buttons: το μέγεθος προσαρμόζεται αυτόματα στα κουμπιά.")
        f3.addRow(self.auto_note)
        g3.setLayout(f3); lay.addWidget(g3)
        self.mode.currentTextChanged.connect(self._refresh_mode_fields)
        self._refresh_mode_fields(self.mode.currentText())

        # --- Κουμπιά ---
        g4, layout4 = QGroupBox("Κουμπιά λωρίδας"), QHBoxLayout()
        self.btn_checks: dict[str, QCheckBox] = {}
        for button in cfg.get("ui.buttons"):
            check = QCheckBox(button["id"])
            check.setChecked(button.get("enabled", True))
            self.btn_checks[button["id"]] = check
            layout4.addWidget(check)
        self.sysbtn = QCheckBox("📌 ◧ ⚙"); self.sysbtn.setChecked(cfg.get("ui.show_system_buttons"))
        layout4.addWidget(self.sysbtn)
        g4.setLayout(layout4); lay.addWidget(g4)

        # --- Γρήγορες ενέργειες / Windows ---
        g5, f5 = QGroupBox("Γρήγορες ενέργειες & Windows"), QFormLayout()
        self.dl = QLineEdit(cfg.get("quick_actions.downloads_path"))
        self.urls = QLineEdit(" ".join(cfg.get("quick_actions.browser_urls")))
        self.auto = QCheckBox("Εκκίνηση με τα Windows"); self.auto.setChecked(cfg.get("ui.always_on_top"))
        f5.addRow("Φάκελος Downloads (κενό=προεπιλογή)", self.dl)
        f5.addRow("Σελίδες browser (με κενό=προεπιλογή)", self.urls)
        f5.addRow(self.auto)
        shortcut = QPushButton("Δημιουργία συντόμευσης επιφάνειας εργασίας")
        shortcut.clicked.connect(self._shortcut)
        f5.addRow(shortcut)
        g5.setLayout(f5); lay.addWidget(g5)

        # --- Φωνητικές εντολές ---
        g6, layout6 = QGroupBox("Φωνητικές εντολές"), QVBoxLayout()
        command_row = QHBoxLayout()
        self.cmd_enabled = QCheckBox("Ενεργές")
        self.cmd_enabled.setChecked(cfg.get("commands.enabled", True))
        self.cmd_mode = QComboBox()
        for value, label_text in (("compact", "Ενεργές"), ("text_only", "Μόνο κείμενο"), ("commands_only", "Μόνο εντολές")):
            self.cmd_mode.addItem(label_text, value)
        idx = self.cmd_mode.findData(cfg.get("commands.mode", "compact"))
        self.cmd_mode.setCurrentIndex(max(0, idx))
        self.cmd_threshold = _spin(0, 100, cfg.get("commands.threshold", 80))
        command_row.addWidget(self.cmd_enabled)
        command_row.addWidget(QLabel("Λειτουργία:"))
        command_row.addWidget(self.cmd_mode)
        command_row.addWidget(QLabel("Κατώφλι:"))
        command_row.addWidget(self.cmd_threshold)
        command_row.addStretch(1)
        layout6.addLayout(command_row)
        if not CommandEngine(cfg).available():
            warning = QLabel("Το rapidfuzz λείπει: pip install -r requirements-commands.txt")
            warning.setStyleSheet("color: #b00020;")
            layout6.addWidget(warning)

        self.cmd_table = QTableWidget(0, 6)
        self.cmd_table.setHorizontalHeaderLabels(
            ["Ενεργή", "Εντολή", f"Φράσεις ({SEP})", f"Ενέργεια ({SEP})", "Άμεση", "Ήχος"])
        self.cmd_table.horizontalHeaderItem(3).setToolTip(
            "Λίστα ορισμάτων, π.χ. explorer.exe;{downloads}. Placeholders: {downloads} {base} {browser}")
        self.cmd_table.horizontalHeaderItem(4).setToolTip(
            "Άμεση: εκτελείται μόλις αναγνωριστεί. Αλλιώς περιμένει OK.")
        self.cmd_table.horizontalHeaderItem(5).setToolTip("Ήχος πριν την εκτέλεση")
        layout6.addWidget(self.cmd_table)
        self._fill_commands()

        edit_row = QHBoxLayout()
        add_button = QPushButton("Προσθήκη εντολής")
        add_button.clicked.connect(self._add_command)
        delete_button = QPushButton("Διαγραφή επιλεγμένης")
        delete_button.clicked.connect(self._delete_command)
        edit_row.addWidget(add_button); edit_row.addWidget(delete_button); edit_row.addStretch(1)
        layout6.addLayout(edit_row)

        test_row = QHBoxLayout()
        self.cmd_test = QLineEdit()
        self.cmd_test.setPlaceholderText("Γράψε φράση για δοκιμή ταύτισης…")
        test_button = QPushButton("Δοκιμή")
        test_button.clicked.connect(self._test_command)
        test_row.addWidget(self.cmd_test); test_row.addWidget(test_button)
        layout6.addLayout(test_row)
        g6.setLayout(layout6); lay.addWidget(g6)

        self.msg = QLabel("")
        apply_button = QPushButton("Εφαρμογή & αποθήκευση")
        apply_button.clicked.connect(self._apply)
        lay.addWidget(apply_button); lay.addWidget(self.msg)
