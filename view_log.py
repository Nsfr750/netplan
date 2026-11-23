"""
view_log.py
Lettura e filtraggio del file di log applicativo (logs/netplan.log).
"""

import os
import re

from logger import LOG_FILE

LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:[.,]\d{3,6})?) "
    r"\[(?P<level>[A-Z]+)\] (?P<logger>[\w.]+): (?P<message>.*)$"
)

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def parse_log_line(line: str) -> dict | None:
    """Analizza una riga di log; None se non corrisponde al formato."""
    m = LOG_LINE_RE.match(line.rstrip("\n"))
    if not m:
        return None
    return {
        "timestamp": m.group("timestamp"),
        "level": m.group("level"),
        "logger": m.group("logger"),
        "message": m.group("message"),
        "raw": line.rstrip("\n"),
    }


def read_log(
    path: str = LOG_FILE,
    level: str | None = None,
    text: str | None = None,
    max_lines: int | None = 2000,
) -> list[dict]:
    """Legge il file di log applicando i filtri.

    Args:
        path: percorso del file di log.
        level: livello esatto da tenere ('INFO', 'ERROR'...); None = tutti.
        text: sottostringa da cercare nel messaggio (case-insensitive).
        max_lines: restituisce al massimo le ultime N righe filtrate.

    Returns:
        Lista di dict {timestamp, level, logger, message, raw}; le righe
        non parsabili restano con level='' e raw=linea originale.
    """
    if not os.path.exists(path):
        return []

    entries = []
    text_l = text.lower() if text else None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed is None:
                parsed = {
                    "timestamp": "",
                    "level": "",
                    "logger": "",
                    "message": line.rstrip("\n"),
                    "raw": line.rstrip("\n"),
                }
            if level and parsed["level"] != level:
                continue
            if text_l and text_l not in parsed["raw"].lower():
                continue
            entries.append(parsed)

    if max_lines is not None and len(entries) > max_lines:
        entries = entries[-max_lines:]
    return entries
