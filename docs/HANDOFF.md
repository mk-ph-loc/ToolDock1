# HANDOFF — ToolDock v0.2.0
Ημερομηνία: 2026-10-30. Branch ai/v0.2.0, PR #1. Δεν έγινε merge/tag/release.

## Επιβεβαιωμένα
- Χρήστης: Google online, Whisper και αυτόματο offline fallback λειτουργούν.
- Χρήστης: στο commit 6199700, pytest -q → 54 passed in 0.50s.
- Το αποτέλεσμα αυτό δεν καλύπτει τη νεότερη διόρθωση ύψους.

## Υλοποίηση
Μικρόφωνα ανά όνομα + host API (speech.device ως dict), τρέχον index κατά την έναρξη, κοινό πεδίο notes/υπαγόρευσης με OK/Enter, διατήρηση προχείρου μεταξύ modes, buttons→compact με speech.expand_on_record (προεπιλογή true).
Η περιοχή χειριστηρίων έχει πλέον Maximum κατακόρυφη πολιτική όταν notes=true. Αν notes=false, το δικό της πλαίσιο κειμένου παραμένει επεκτάσιμο.

## Εκκρεμή
1. Πλήρες pytest -q στο Windows venv μετά τη διόρθωση (προστέθηκαν 2 layout tests· δεν εκτελέστηκαν από το AI επειδή λείπει PySide6).
2. Οπτικός επανέλεγχος compact/full/dock και buttons→🎤→κείμενο→OK.
3. Ενοποίηση docs/TESTS-v0.2.0-FINAL.md στο docs/TESTS.md, τελική ενημέρωση CHANGELOG/CODE-MAP/DECISIONS και πλήρες zip μέσω release.ps1 μετά τον έλεγχο.
4. Αντίγραφα docs στα Project files παραμένουν εκκρεμή· τα υπάρχοντα εκεί είναι παλιότερα.

Μη ξεκινήσεις S3 πριν κλείσει το S2. Δεν απαιτείται Opus για το τρέχον scope. Αν βαραίνει η συνομιλία, χρησιμοποίησε το NEXT-CHAT-PROMPT.
