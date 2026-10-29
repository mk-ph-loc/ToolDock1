"""Κανονικοποίηση κειμένου (πεζά, χωρίς τόνους, καθαρά κενά)."""
import re
import unicodedata

_WS = re.compile(r"\s+")


def strip_accents(text: str) -> str:
    """Αφαιρεί τόνους/διαλυτικά (NFD) και ξαναενώνει (NFC)."""
    nfd = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(c for c in nfd if not unicodedata.combining(c)))


def normalize(text: str) -> str:
    """Πεζά + χωρίς τόνους + ένα κενό ανάμεσα στις λέξεις. Το τελικό σίγμα γίνεται σ."""
    t = strip_accents(text).casefold().replace("ς", "σ")
    return _WS.sub(" ", t).strip()


def clean_text(text: str) -> str:
    """Καθαρισμός για αποθήκευση: \r\n -> \n, αφαίρεση κενών στα άκρα."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()
