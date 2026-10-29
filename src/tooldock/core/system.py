"""Ενέργειες συστήματος Windows: άνοιγμα φακέλων/browser/Notepad, autostart, συντομεύσεις."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from tooldock.core.config import Config

log = logging.getLogger("tooldock.system")
LNK_NAME = "ToolDock.lnk"


def open_folder(path: str | Path) -> None:
    p = Path(path).expanduser()
    if os.name == "nt":
        os.startfile(str(p))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(p)])


def open_notepad(file: Path | None = None) -> None:
    args = ["notepad.exe"] + ([str(file)] if file else [])
    subprocess.Popen(args)


def open_urls(urls: list[str], exe: str = "") -> None:
    """Ανοίγει σελίδες· exe κενό = προεπιλεγμένος browser."""
    for u in urls:
        if exe:
            subprocess.Popen([exe, u])
        else:
            webbrowser.open(u)


def downloads_dir(cfg: Config) -> Path:
    custom = cfg.get("quick_actions.downloads_path", "")
    return Path(custom) if custom else Path.home() / "Downloads"


def launch_command(root: Path) -> tuple[str, str]:
    """(πρόγραμμα, παράμετροι) για συντομεύσεις. Προτιμά pythonw από το .venv (χωρίς κονσόλα)."""
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    return str(exe), f'"{root / "tooldock.pyw"}"'


def create_shortcut(lnk: Path, root: Path) -> bool:
    """Δημιουργεί .lnk μέσω PowerShell/WScript.Shell. Επιστρέφει επιτυχία."""
    if os.name != "nt":
        log.warning("Συντομεύσεις μόνο σε Windows")
        return False
    target, args = launch_command(root)
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
        "$s.TargetPath='{t}';$s.Arguments='{a}';$s.WorkingDirectory='{w}';$s.Save()"
    ).format(lnk=lnk, t=target, a=args, w=root)
    # ΠΡΟΣΟΧΗ: το tooldock.pyw προσθέτει το src στο sys.path (δεν χρειάζεται εγκατάσταση)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    return r.returncode == 0 and lnk.exists()


def startup_lnk() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup" / LNK_NAME


def desktop_lnk() -> Path:
    return Path.home() / "Desktop" / LNK_NAME


def set_autostart(enabled: bool, root: Path) -> bool:
    lnk = startup_lnk()
    if enabled:
        return create_shortcut(lnk, root)
    lnk.unlink(missing_ok=True)
    return True


def create_desktop_shortcut(root: Path) -> bool:
    return create_shortcut(desktop_lnk(), root)
