"""
logger.py
Configurazione centralizzata del logging: file rotante in logs/ per il
dettaglio completo (DEBUG) e console solo per avvisi ed errori, così da
non duplicare i messaggi già stampati a video dai tool CLI.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "netplan.log")

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False

def get_logger(name: str = "netplan") -> logging.Logger:
    """Restituisce un logger configurato (file rotante + console).

    Il file logs/netplan.log raccoglie tutto a livello DEBUG, con rotazione
    (max ~1 MB per file, 3 backup). La console mostra solo WARNING ed errori.
    Chiamate successive restituiscono lo stesso logger senza duplicare handler.
    """
    global _configured
    logger = logging.getLogger(name)
    if _configured:
        return logger

    os.makedirs(LOG_DIR, exist_ok=True)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    _configured = True
    return logger
