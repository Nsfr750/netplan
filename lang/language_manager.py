"""
lang/language_manager.py
Gestore centralizzato delle traduzioni dell'interfaccia.

Le stringhe vivono in lang/translations.py (mai in file esterni):
tr(key, **kwargs) restituisce la stringa nella lingua corrente,
con fallback all'italiano e infine alla chiave stessa.
"""

from lang.translations import TRANSLATIONS

DEFAULT_LANGUAGE = "it"

LANGUAGES = {"it": "Italiano", "en": "English"}


class LanguageManager:
    """Singleton che mantiene la lingua corrente e risolve le chiavi."""

    _instance: "LanguageManager | None" = None

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self._language = language if language in TRANSLATIONS else DEFAULT_LANGUAGE

    @classmethod
    def instance(cls) -> "LanguageManager":
        """Restituisce l'istanza condivisa del gestore."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, code: str):
        """Imposta la lingua corrente (ignora codici non supportati)."""
        if code in TRANSLATIONS:
            self._language = code

    def available_languages(self) -> dict:
        """Codici lingua -> nome visualizzato."""
        return dict(LANGUAGES)

    def tr(self, key: str, **kwargs) -> str:
        """Traduce una chiave, formattando eventuali segnaposto {nome}."""
        text = TRANSLATIONS.get(self._language, {}).get(key)
        if text is None:
            text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
        return text.format(**kwargs) if kwargs else text


def get_language() -> str:
    """Codice della lingua attiva (es. 'it')."""
    return LanguageManager.instance().language


def set_language(code: str):
    """Imposta la lingua attiva a livello di applicazione."""
    LanguageManager.instance().set_language(code)


def tr(key: str, **kwargs) -> str:
    """Scorciatoia per LanguageManager.instance().tr(key, **kwargs)."""
    return LanguageManager.instance().tr(key, **kwargs)
