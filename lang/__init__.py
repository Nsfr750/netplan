"""
lang
Sistema di localizzazione di netplan.

Uso:
    from lang.language_manager import tr
    label = tr("run_analysis")
"""

from lang.language_manager import (  # noqa: F401
    LanguageManager,
    get_language,
    set_language,
    tr,
)
