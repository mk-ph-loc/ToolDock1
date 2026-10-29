# Changelog
## [v0.1.0] — 2026-10-29
### Νέα
- Σκελετός: plugins (notes, quick_actions), tray, 3 modes (buttons/compact/full), float/dock (4 πλευρές) με ρυθμιζόμενο πάχος και περιθώρια, always-on-top, single instance.
- config.json με defaults + config.example.json· data/ με Base.txt και notes/<ΘΕΜΑ>.txt στην πρώτη εκτέλεση.
- Πλαίσιο κειμένου + OK/Enter: clipboard + Base.txt + αρχείο θέματος (μορφή §5).
- Κουμπιά Notepad, Downloads, Browser· Εκκίνηση με Windows· συντόμευση επιφάνειας εργασίας.
- scripts/release.ps1, run.bat, 19 tests (config, storage, textnorm).
### Γνωστά θέματα
- Το dock δεν δεσμεύει χώρο στην οθόνη (όχι AppBar)· παράθυρα μπορεί να μπαίνουν από κάτω του. Βλ. DECISIONS #7.
- Το UI δεν δοκιμάστηκε σε Windows από το AI — δες docs/TESTS.md.
