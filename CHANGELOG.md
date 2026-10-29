# Changelog
## [v0.1.1] — 2026-10-29
### Νέα
- Επιλογή οθόνης (`ui.screen`: auto | 0 | 1 …) για float και dock· το dock υπολογίζεται στην availableGeometry της οθόνης-στόχου.
- Λαβή στην εσωτερική άκρη του dock: σύρσιμο αλλάζει το πάχος (dock δεξιά -> επηρεάζεις την αριστερή πλευρά)· περιθώρια πάνω/κάτω από ρυθμίσεις.
- Πάχος dock και μέγεθος float ανά mode. Το mode buttons προσαρμόζεται αυτόματα στα κουμπιά.
- Το float θυμάται θέση/μέγεθος αυτόματα (και στην Έξοδο από το tray).
### Αλλαγές
- Status «Αποθηκεύτηκε: <αρχεία> · ΕΕΕΕ-ΜΜ-ΗΗ ΩΩ:ΛΛ».
- config v2: `ui.dock.thickness` = dict ανά mode, `ui.float.sizes` ανά mode (αυτόματο migration από v1).
- release.ps1: δεν αποτυγχάνει όταν δεν υπάρχουν αλλαγές για commit (μετά από merge).
### Διορθώσεις
- Το παράθυρο δεν «περνά» στην άλλη οθόνη: δεύτερο πέρασμα θέσης μετά το show + clamp στην οθόνη.
### Γνωστά θέματα
- Το dock δεν δεσμεύει χώρο (όχι AppBar).

## [v0.1.0] — 2026-10-29
### Νέα
- Σκελετός: plugins (notes, quick_actions), tray, 3 modes, float/dock, always-on-top, single instance.
- config.json, data/ (Base.txt, notes/), OK/Enter, Notepad, Downloads, Browser, autostart, συντόμευση, release.ps1, 19 tests.
