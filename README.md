# ToolDock
Καθημερινή εργαλειοθήκη για Windows (tray, dock, σημειώσεις, γρήγορες ενέργειες).
## Εγκατάσταση (PowerShell)
```powershell
git clone https://github.com/mk-ph-loc/ToolDock1.git; cd ToolDock1
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m tooldock          # ή scripts\run.bat
```
Ρυθμίσεις: αντίγραψε/επεξεργάσου `config.json` (δημιουργείται από `config.example.json` στην πρώτη εκτέλεση).
Δεδομένα: `data/` (Base.txt, notes/, logs/). Τεκμηρίωση: `docs/`.
