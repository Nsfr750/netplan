"""
help.py
Testo della guida utente mostrato dal menu Help della GUI, disponibile in italiano e inglese.
"""

_HELP = {
    "it": """\
NETPLAN — GUIDA RAPIDA
======================

SCOPO
Analizza KPI aggregati e anonimizzati per cella per individuare
congestione e buchi di copertura, con raccomandazioni di pianificazione.
Non tratta dati di singoli utenti (MSISDN, IMSI...).

USO BASE
1. Seleziona il file KPI di input (CSV o Excel, una riga per cella
   per intervallo temporale).
2. Scegli la cartella di output.
3. (Opzionale) indica un file di soglie personalizzate.
4. Premi "Avvia analisi".

RISULTATI
- Riepilogo: descrizione del dataset e conteggio severità.
- Per cella / Per sito: tabelle del report (severità colorata).
- Grafici: mappa celle, scatter copertura, distribuzione PRB,
  trend temporali delle celle peggiori.

FILE PRODOTTI (nella cartella output)
- report_per_cella.csv / report_per_sito.csv
- report_pianificazione_copertura.xlsx / .html / .pdf
- prb_distribution.png, coverage_scatter.png, cell_map.png,
  trend_celle.png

SOGLIE
Le soglie di allarme sono configurabili da file (JSON o chiave=valore);
vedi docs/SOGLIE.md per l'elenco delle chiavi e i valori di default.

DA LINEA DI COMANDO
  python main.py --input FILE [--outdir DIR] [--thresholds F] [--strict]
  python congestion_check.py --input FILE [--site ID] [--only-critical]
""",
    "en": """\
NETPLAN — QUICK GUIDE
=====================

PURPOSE
Analyzes aggregated, anonymized per-cell KPIs to detect congestion and
coverage holes, with planning recommendations. It does not process
per-user data (MSISDN, IMSI...).

BASIC USAGE
1. Select the input KPI file (CSV or Excel, one row per cell per
   time interval).
2. Choose the output folder.
3. (Optional) pick a custom thresholds file.
4. Press "Run analysis".

RESULTS
- Summary: dataset description and severity counts.
- Per cell / Per site: report tables (colored severity).
- Charts: cell map, coverage scatter, PRB distribution,
  time trends of the worst cells.

OUTPUT FILES (in the output folder)
- report_per_cella.csv / report_per_sito.csv
- report_pianificazione_copertura.xlsx / .html / .pdf
- prb_distribution.png, coverage_scatter.png, cell_map.png,
  trend_celle.png

THRESHOLDS
Alarm thresholds can be customized via file (JSON or key=value);
see docs/SOGLIE.md for the key list and default values.

COMMAND LINE
  python main.py --input FILE [--outdir DIR] [--thresholds F] [--strict]
  python congestion_check.py --input FILE [--site ID] [--only-critical]
""",
}


def get_help_text(lang: str = "it") -> str:
    """Testo della guida nella lingua richiesta (fallback: italiano)."""
    return _HELP.get(lang, _HELP["it"])
