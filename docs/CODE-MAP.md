# CODE-MAP v0.2.0
- `tooldock.pyw` / `__main__.py` → `app.main()`: logging, single instance, plugins, tray, Shell.
- `core/config.py` DEFAULTS + Config (load/save/get/set, migrate v3). `core/geometry.py` (καθαρή γεωμετρία dock/clamp/πάχος). `core/storage.py`, `core/textnorm.py`, `core/system.py`, `core/events.py`.
- `speech/`: `base.py` (Audio, Provider, SttError, γλώσσες), `vad.py` (RMS/σιωπή), `registry.py` (SpeechService + fallback), `google.py` (Web Speech), `whisper_local.py` (faster-whisper, lazy), `recorder.py` (sounddevice).
- `tools/base.py` Plugin/Action. `tools/<name>/plugin.py` με `create(ctx)`· φορτώνεται μόνο αν `plugins.<name>` = true.
- `tools/dictation/plugin.py`: κουμπί 🎤, worker thread (ηχογράφηση+STT), κείμενο στο πλαίσιο.
- `ui/shell.py` modes, dock, οθόνη, λαβή (Grip). `ui/settings.py` φόρμα ρυθμίσεων.
- Νέο κουμπί: Action στο plugin + εγγραφή `{id, enabled}` στο `ui.buttons`.
