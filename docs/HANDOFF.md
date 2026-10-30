# HANDOFF — ToolDock v0.2.1
Ενημέρωση: 2026-10-30. Branch ai/v0.2.1, PR προς main. Βάση: main `1d2a0d5d70fe74e095d95ba9309c707d4cf6b781` (2026-10-29 23:18 UTC).

## Κατάσταση
- Το PR #1 (v0.2.0) έγινε merge. Το tag `v0.2.0` δείχνει στο `1d2a0d5`.
- Το zip `dist\tooldock-v0.2.0.zip` (70.980 bytes) αναφέρθηκε από τον χρήστη· δεν επαληθεύτηκε από το AI (το dist/ δεν είναι στο repo).
- Το Gitea/`origin` αφαιρέθηκε από τις απαιτήσεις. Απαιτούμενο remote πλέον μόνο `github`, ρυθμιζόμενο στο `release.required_remotes`.

## Τι έγινε στο v0.2.1
- Θωράκιση του `scripts/release.ps1`: μόνο καθαρό και ενημερωμένο main, έλεγχος SHA με `github/main`, `git add -u`, αποτυχία σε untracked, έλεγχος zip, idempotent tag, push και επαλήθευση tag ανά remote, σωστό exit code.
- `config.example.json`: νέα ενότητα `release.required_remotes` = `["github"]`.
- VERSION → 0.2.1, CHANGELOG, DECISIONS (Δ27–Δ29), report, TESTS, HANDOFF, NEXT-CHAT-PROMPT.

## Επόμενα βήματα χρήστη
1. Έλεγξε το PR και κάνε merge.
2. `git switch main; git pull github main`
3. `./scripts/release.ps1 -Message "θωράκιση release"` χωρίς bump (το VERSION είναι ήδη 0.2.1).
4. Επιβεβαίωσε: tests πέρασαν, zip δημιουργήθηκε, tag `v0.2.1` εμφανίζεται στο GitHub.
5. Συμπλήρωσε τα χειροκίνητα items 6–10 του TESTS.md (v0.2.0) όταν τα ελέγξεις.

## Επόμενη συνεδρία
S3/v0.3.0: rapidfuzz, τρεις εντολές, άμεση/επιβεβαίωση/ήχος, επεξεργαστής. Branch `ai/v0.3.0` + PR. Καμία αλλαγή main ή tags από AI. Δεν απαιτείται Opus.
