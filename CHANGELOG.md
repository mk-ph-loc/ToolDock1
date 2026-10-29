# Changelog
## [v0.2.0] — 2026-10-30
### Νέα
- Υπαγόρευση (plugin `dictation`, on/off): ένα κουμπί 🎤 στη λωρίδα, έναρξη και χειροκίνητο στοπ.
- Ηχογράφηση με `sounddevice` (16 kHz mono) και αυτόματο στοπ σε σιωπή (RMS, ρυθμιζόμενο κατώφλι/διάρκεια).
- Interface STT με προτεραιότητα και fallback: Google Web Speech + faster-whisper τοπικά, lazy φόρτωση.
- Γλώσσες el/en με επιλογέα και αντιστοίχιση κωδικών ανά πάροχο.
- Κοινό επεξεργάσιμο πεδίο υπαγόρευσης/σημειώσεων με OK/Enter, clipboard, Base.txt και προαιρετικό θέμα.
- Επιλογέας εισόδων ανά όνομα + host API. Αποθήκευση σταθερής ταυτότητας, επίλυση σε τρέχον index κατά την ηχογράφηση.
- Αυτόματο buttons→compact με το 🎤 (`speech.expand_on_record`, προεπιλογή true).
- Προαιρετικές εξαρτήσεις στο `requirements-speech.txt`. Ρυθμίσεις φωνής στο `speech.*`.
### Αλλαγές / διορθώσεις
- config v3: `speech`, plugin `dictation`, migration κουμπιού `mic` από v2.
- Προστέθηκε και εκπέμπεται πάντα worker.finished, σωστή ολοκλήρωση thread και διαχείριση σφαλμάτων.
- Αφαιρέθηκαν διπλό κουμπί και ξεχωριστό ασύνδετο πλαίσιο αναγνώρισης.
- Διατήρηση προχείρου μεταξύ modes, επαναχρησιμοποίηση μοντέλου μεταξύ υπαγορεύσεων.
- Έγκυρος index συσκευής 0 δεν μετατρέπεται σε default. Αμφίσημη/απούσα είσοδος εμφανίζει οδηγία νέας επιλογής.
- Συμπαγές ύψος χειριστηρίων με notes=true· επεκτάσιμο πεδίο με notes=false.
### Έλεγχοι
- Χρήστης, Windows: d6bfe88 → 56 passed in 0.52s και οπτική επιβεβαίωση διόρθωσης ύψους.
- Επιβεβαιώθηκαν Google online, Whisper και αυτόματο offline fallback. Δεν θεωρούνται ολοκληρωμένα όλα τα προαιρετικά hardware/UI checklist items.
### Γνωστά θέματα
- Πρώτη λήψη Whisper απαιτεί internet και χώρο δίσκου. Η προειδοποίηση symlinks στα Windows δεν είναι αποτυχία αναγνώρισης.
- Google Web Speech: ανεπίσημο online API. Offline fallback προϋποθέτει ήδη διαθέσιμο μοντέλο Whisper.
- Δεν εγγυάται κάθε host API υποστήριξη του ίδιου sample rate. Global hotkeys στο S4.

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
