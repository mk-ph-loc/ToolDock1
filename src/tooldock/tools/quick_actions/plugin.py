"""Γρήγορες ενέργειες: Downloads, Browser (ρυθμίζονται στο config quick_actions)."""
from __future__ import annotations

from tooldock.core import system
from tooldock.tools.base import Action, Plugin


class QuickActionsPlugin(Plugin):
    name, icon = "quick_actions", "⚡"

    def actions(self) -> list[Action]:
        cfg = self.ctx.cfg
        return [
            Action("downloads", "Downloads", "📥",
                   lambda: system.open_folder(system.downloads_dir(cfg))),
            Action("browser", "Browser", "🌐",
                   lambda: system.open_urls(cfg.get("quick_actions.browser_urls", []),
                                            cfg.get("quick_actions.browser_exe", ""))),
        ]


def create(ctx) -> QuickActionsPlugin:
    return QuickActionsPlugin(ctx)
