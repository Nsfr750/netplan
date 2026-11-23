"""Test per i moduli di supporto GUI: lingue, update, log viewer, sponsor, help."""

import pytest

from lang.language_manager import LanguageManager, get_language, set_language, tr
from lang.translations import TRANSLATIONS


def test_language_switch():
    set_language("en")
    assert get_language() == "en"
    assert tr("run_analysis") == "Run analysis"
    set_language("it")
    assert tr("run_analysis") == "Avvia analisi"


def test_tr_fallback_unknown_key():
    assert tr("chiave_che_non_esiste") == "chiave_che_non_esiste"


def test_tr_format_kwargs():
    set_language("it")
    text = tr("app_title", version="9.9")
    assert "9.9" in text


def test_translations_parity_it_en():
    """Le due lingue devono coprire le stesse chiavi."""
    missing_en = set(TRANSLATIONS["it"]) - set(TRANSLATIONS["en"])
    missing_it = set(TRANSLATIONS["en"]) - set(TRANSLATIONS["it"])
    assert not missing_en, f"chiavi mancanti in 'en': {missing_en}"
    assert not missing_it, f"chiavi mancanti in 'it': {missing_it}"


def test_set_language_ignores_unknown():
    set_language("xx")
    assert get_language() == "it"
    set_language("it")


def test_version_tuple_comparison():
    from update import _version_tuple

    assert _version_tuple("v0.2.1") > _version_tuple("0.2.0")
    assert _version_tuple("1.0.0") > _version_tuple("0.9.9")
    assert _version_tuple("0.2.0") == _version_tuple("v0.2.0")


def test_view_log_parsing_and_filters(tmp_path):
    from view_log import parse_log_line, read_log

    log = tmp_path / "netplan.log"
    log.write_text(
        "2026-11-23 10:00:00,123 [INFO] netplan: avvio analisi\n"
        "2026-11-23 10:00:01,456 [WARNING] netplan: colonna ambigua\n"
        "2026-11-23 10:00:02,789 [ERROR] netplan: file non trovato\n"
        "riga non formattata\n",
        encoding="utf-8",
    )

    parsed = parse_log_line("2026-11-23 10:00:00 [INFO] netplan: ok")
    assert parsed["level"] == "INFO"
    assert parse_log_line("non un log") is None

    assert len(read_log(str(log))) == 4
    assert len(read_log(str(log), level="ERROR")) == 1
    assert len(read_log(str(log), text="ambigua")) == 1
    assert len(read_log(str(log), level="INFO", text="avvio")) == 1
    assert len(read_log(str(log), max_lines=2)) == 2
    assert read_log(str(tmp_path / "mancante.log")) == []


def test_sponsor_info_and_qr():
    from sponsor import get_sponsor_info, make_qr_png

    info = get_sponsor_info()
    assert info["paypal"].startswith("https://paypal.me/")
    assert info["monero"].startswith("47")

    png = make_qr_png(info["paypal"])
    if png is not None:  # qrcode opzionale
        assert png.startswith(b"\x89PNG")


def test_help_and_about_texts():
    from about import get_about_text
    from help import get_help_text

    assert get_help_text("en") != get_help_text("it")
    assert "NETPLAN" in get_help_text("en").upper()
    assert "Nsfr750" in get_about_text()
    assert "©" in get_about_text()


def test_gui_modules_importable():
    """I moduli GUI devono importarsi senza display (nessun QApplication)."""
    import gui  # noqa: F401
    import gui_dialogs  # noqa: F401
    import menu  # noqa: F401

    assert callable(gui.app_title)
