"""
settings.py
Persistenza delle preferenze dell'applicazione tramite QSettings
(su Windows finiscono nel registro: HKCU\\Software\\Tuxxle\\Netplan).
"""

from PySide6.QtCore import QSettings

ORG = "Tuxxle"
APP = "Netplan"

DEFAULTS = {
    "language": "it",
    "outdir": "output",
    "thresholds": "",
    "trend_cells": 6,
    "html_report": True,
    "pdf_report": True,
    "strict": False,
}


def _store() -> QSettings:
    """Istanza QSettings dell'applicazione."""
    return QSettings(ORG, APP)


def get_setting(key: str):
    """Legge una preferenza; se assente restituisce il default noto."""
    store = _store()
    default = DEFAULTS.get(key)
    if isinstance(default, bool):
        value = store.value(key, default)
        return value if isinstance(value, bool) else str(value).lower() == "true"
    if isinstance(default, int):
        return int(store.value(key, default))
    return store.value(key, default)


def set_setting(key: str, value):
    """Salva una preferenza."""
    _store().setValue(key, value)
