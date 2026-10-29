from tooldock.core.textnorm import clean_text, normalize, strip_accents


def test_accents():
    assert strip_accents("Εξερεύνηση") == "Εξερευνηση"
    assert strip_accents("ΐ") == "ι"


def test_normalize():
    assert normalize("  Εξερεύνηση   ΑΡΧΕΊΩΝ ") == "εξερευνηση αρχειων"
    assert normalize("Δίκτυο") == normalize("δικτυο")
    assert normalize("όλος") == normalize("ΟΛΟΣ")


def test_clean_text():
    assert clean_text("  a\r\nb\r\n ") == "a\nb"
