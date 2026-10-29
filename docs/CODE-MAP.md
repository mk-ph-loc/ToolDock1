# CODE-MAP v0.1.0
- `tooldock.pyw` / `__main__.py` → `app.main()`: logging, single instance, plugins, tray, Shell.
- `core/config.py` DEFAULTS + Config (load/save/get/set, migrate). `core/storage.py` format_entry + Storage. `core/textnorm.py`. `core/system.py` (Notepad, φάκελοι, browser, .lnk). `core/events.py` bus.
- `tools/base.py` Plugin/Action. `tools/<name>/plugin.py` με `create(ctx)`· φορτώνεται μόνο αν `plugins.<name>` = true.
- `ui/shell.py` modes, dock, on-top. `ui/settings.py` φόρμα ρυθμίσεων.
- Νέο κουμπί: Action στο plugin + εγγραφή `{id, enabled}` στο `ui.buttons`.
