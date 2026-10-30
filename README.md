# ToolDock
Καθημερινή εργαλειοθήκη για Windows (tray, dock, σημειώσεις, γρήγορες ενέργειες, φωνητικές εντολές).
## Εγκατάσταση (PowerShell)
```powershell
git clone https://github.com/mk-ph-loc/ToolDock1.git; cd ToolDock1
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m tooldock          # ή scripts\run.bat
```
Ρυθμίσεις: αντίγραψε/επεξεργάσου `config.json` (δημιουργείται από `config.example.json` στην πρώτη εκτέλεση).
Δεδομένα: `data/` (Base.txt, notes/, logs/). Τεκμηρίωση: `docs/`.

## Φωνητικές εντολές (v0.3.0)
- Οι εντολές ρυθμίζονται στο ⚙ → «Φωνητικές εντολές».
- Φράσεις και ορίσματα χωρίζονται με `;`.
- Ειδικά ορίσματα: `{downloads}`, `{browser}`, `{base}`.
- «Άμεση» εκτελεί την εντολή μόλις ταυτιστεί· αλλιώς απαιτείται επιβεβαίωση με OK.
- Προαιρετική εξάρτηση: `pip install -r requirements-commands.txt` (rapidfuzz).
