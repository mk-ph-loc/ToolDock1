"""Καθαρή γεωμετρία (χωρίς Qt): dock, clamp σε οθόνη, πάχος/μέγεθος ανά mode."""
from __future__ import annotations

from typing import Any

Rect = tuple[int, int, int, int]  # x, y, πλάτος, ύψος
MIN_THICKNESS = 60
DEFAULT_THICKNESS = 360


def clamp_rect(rect: Rect, area: Rect) -> Rect:
    """Μικραίνει/μετακινεί το rect ώστε να χωράει ολόκληρο μέσα στην area (μία οθόνη)."""
    x, y, w, h = rect
    ax, ay, aw, ah = area
    w, h = min(w, aw), min(h, ah)
    return (max(ax, min(x, ax + aw - w)), max(ay, min(y, ay + ah - h)), w, h)


def dock_rect(area: Rect, side: str, thickness: int, margin_start: int = 0, margin_end: int = 0) -> Rect:
    """Rect για dock σε πλευρά. area = availableGeometry της οθόνης που επιλέχθηκε."""
    ax, ay, aw, ah = area
    t = max(MIN_THICKNESS, int(thickness))
    ms, me = max(0, int(margin_start)), max(0, int(margin_end))
    if side == "left":
        r = (ax, ay + ms, t, ah - ms - me)
    elif side == "right":
        r = (ax + aw - t, ay + ms, t, ah - ms - me)
    elif side == "top":
        r = (ax + ms, ay, aw - ms - me, t)
    elif side == "bottom":
        r = (ax + ms, ay + ah - t, aw - ms - me, t)
    else:
        raise ValueError(f"άγνωστη πλευρά: {side}")
    x, y, w, h = r
    return clamp_rect((x, y, max(MIN_THICKNESS, w), max(MIN_THICKNESS, h)), area)


def thickness_for(value: Any, mode: str, default: int = DEFAULT_THICKNESS) -> int:
    """Πάχος dock για το mode. Δέχεται αριθμό (παλιό config) ή dict {mode: πάχος}."""
    if isinstance(value, dict):
        v = value.get(mode, value.get("compact", default))
        return int(v) if isinstance(v, (int, float)) else default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return default


def with_thickness(value: Any, mode: str, t: int) -> dict:
    """Νέο dict πάχους με την τιμή του mode αλλαγμένη (μετατρέπει παλιό αριθμό σε dict)."""
    base = dict(value) if isinstance(value, dict) else {
        "compact": thickness_for(value, "compact"), "full": thickness_for(value, "full")}
    base[mode] = max(MIN_THICKNESS, int(t))
    return base


def float_size(float_cfg: dict, mode: str) -> tuple[int, int]:
    """Μέγεθος float για το mode· fallback: compact, μετά παλιά κλειδιά w/h."""
    sizes = float_cfg.get("sizes", {}) or {}
    s = sizes.get(mode) or sizes.get("compact")
    if isinstance(s, dict) and "w" in s and "h" in s:
        return int(s["w"]), int(s["h"])
    return int(float_cfg.get("w", 380)), int(float_cfg.get("h", 260))
