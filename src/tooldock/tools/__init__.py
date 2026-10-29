"""Φόρτωση plugins: κάθε φάκελος tools/<name>/ με module plugin.py που ορίζει create(ctx)."""
from __future__ import annotations

import importlib
import logging
import pkgutil

from tooldock.tools.base import Plugin

log = logging.getLogger("tooldock.tools")


def load_plugins(ctx) -> list[Plugin]:
    """Φορτώνει ΜΟΝΟ όσα είναι enabled στο config (βαριές εξαρτήσεις δεν φορτώνονται)."""
    import tooldock.tools as pkg
    out: list[Plugin] = []
    for m in pkgutil.iter_modules(pkg.__path__):
        if not m.ispkg or not ctx.cfg.get(f"plugins.{m.name}", False):
            continue
        try:
            mod = importlib.import_module(f"tooldock.tools.{m.name}.plugin")
            out.append(mod.create(ctx))
        except Exception:  # ένα χαλασμένο plugin δεν ρίχνει την εφαρμογή
            log.exception("Αποτυχία φόρτωσης plugin %s", m.name)
    return out
