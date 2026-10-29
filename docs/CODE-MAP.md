# CODE-MAP v0.1.1
- `tooldock.pyw` / `__main__.py` → `app.main()`: logging, single instance, plugins, tray, Shell.
- `core/config.py` DEFAULTS + Config (load/save/get/set, migrate v2). `core/geometry.py` (καθαρή γεωμετρία dock/clamp/πάχος). `core/storage.py`, `core/textnorm.py`, `core/system.py`, `core/events.py`.
- `tools/base.py` Plugin/Action. `tools/<name>/plugin.py` με `create(ctx)`· φορτώνεται μόνο αν `plugins.<name>` = true.
- `ui/shell.py` modes, dock, οθόνη, λαβή (Grip). `ui/settings.py` φόρμα ρυθμίσεων.
- Νέο κουμπί: Action στο plugin + εγγραφή `{id, enabled}` στο `ui.buttons`.
