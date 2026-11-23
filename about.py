"""
about.py
Testo "Informazioni su" dell'applicazione.
"""

from version import __version__

APP_NAME = "Netplan"
AUTHOR = "Nsfr750"
ORGANIZATION = "Tuxxle"
WEBSITE = "https://www.tuxxle.org"
GITHUB = "https://github.com/Nsfr750"
COPYRIGHT = "© Copyright 2024-2026 Nsfr750 - All rights reserved."
LICENSE_NAME = "Licenza proprietaria (vedi LICENSE)"

def get_about_text() -> str:
    """Testo della finestra Informazioni."""
    return (
        f"{APP_NAME} v{__version__}\n"
        f"Strumento di pianificazione copertura radio (KPI aggregati)\n\n"
        f"{COPYRIGHT}\n"
        f"{ORGANIZATION} — {WEBSITE}\n"
        f"GitHub: {GITHUB}\n"
        f"Licenza: {LICENSE_NAME}"
    )
