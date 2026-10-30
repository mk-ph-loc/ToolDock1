# Επόμενη συνομιλία — v0.3.0 έλεγχος/release
Repo: mk-ph-loc/ToolDock1. Branch: `ai/v0.3.0`.

- Διάβασε `docs/HANDOFF.md`, `docs/TESTS.md`, `docs/reports/v0.3.0-REPORT.md` και το diff του τελευταίου commit.
- Ζήτα από τον χρήστη αποτελέσματα: `pytest tests/test_config_v3.py tests/test_commands.py -q` και `pytest -q`.
- Αν περάσουν, ενημέρωσε τα ✅ στο `docs/TESTS.md` μόνο με ρητή αναφορά χρήστη.
- Μην κάνεις νέο revert, merge, tag ή αλλαγή στο `main`.
- Release/zip μόνο με ρητή εντολή χρήστη, μέσω `scripts/release.ps1` από τοπικό main μετά το merge.
