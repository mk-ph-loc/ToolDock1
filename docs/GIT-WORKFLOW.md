# Συνεργασία στο git (εσύ + AI)
- `main` = μόνο δοκιμασμένος κώδικας· εκεί κάνεις release (`scripts/release.ps1`) και μπαίνουν τα tags.
- Το AI δουλεύει **μόνο** σε branch `ai/vX.Y.Z` (π.χ. `ai/v0.2.0`) και ανοίγει Pull Request προς `main`. Δεν κάνει push στο main, δεν βάζει tags.
- Εσύ: `git fetch; git switch ai/vX.Y.Z; pytest; python -m tooldock` → αν ΟΚ: merge (PR ή τοπικά) → `git switch main; git pull` → `release.ps1`.
- Αν βρεις bug: διόρθωσέ το στο ίδιο branch ή ζήτα v0.X.1· ένα branch ανά έκδοση.
- Δικές σου αλλαγές (π.χ. config.example.json, docs/TESTS.md ✅/❌): commit απευθείας στο main ΜΟΝΟ μεταξύ sessions· πριν ξεκινήσει νέα session κάνε `git push`.
- Κάθε session ξεκινά με τον SHA/ημερομηνία του main που βλέπει το AI (διαβάζει από το GitHub).
- Το Gitea ενημερώνεται μόνο από το release.ps1 (push και στα δύο remotes).
