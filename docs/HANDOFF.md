# HANDOFF — ToolDock v0.3.0
Ενημέρωση: 2026-10-30. Branch: `ai/v0.3.0`. Στόχος: μικρό commit με τις εγκριμένες διορθώσεις review.

## Κατάσταση
- Διορθώθηκε το migration config v3→v4: κενή λίστα `commands.items` διατηρείται.
- Tests: `CONFIG_VERSION == 4` και skip όταν λείπει `rapidfuzz`.
- UI εντολών: κουμπιά «Προσθήκη εντολής»/«Διαγραφή επιλεγμένης», διαχωριστής `;`, tooltip άμεσης εκτέλεσης, προειδοποίηση για λείπον `rapidfuzz`.
- Ενημερώθηκαν README, CODE-MAP, VERSION, CHANGELOG, TESTS, HANDOFF και NEXT-CHAT-PROMPT.

## Εκκρεμείς έλεγχοι χρήστη
1. `pytest tests/test_config_v3.py tests/test_commands.py -q`
2. `pytest -q`
3. Χειροκίνητα βήματα ενότητας «v0.3.0» στο `docs/TESTS.md`.

## Επόμενα βήματα
- Έλεγχος diff/PR και merge στο main από τον χρήστη.
- Release/zip μέσω `scripts/release.ps1` μόνο αν ο χρήστης το ζητήσει.
- Καμία αλλαγή σε `main`, κανένα tag και κανένα merge από το AI.
