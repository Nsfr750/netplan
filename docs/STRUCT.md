# Struttura del progetto

```text
netplan/
├── main.py                 # CLI: esegue la pipeline completa (report + grafici)
├── gui.py                  # Interfaccia grafica PySide6 (python gui.py)
├── gui_dialogs.py          # Dialoghi GUI: log viewer, impostazioni, help, sponsor, about
├── menu.py                 # Barra dei menu GUI (Log / Impostazioni / Help)
├── settings.py             # Preferenze persistenti (QSettings)
├── update.py               # Controllo aggiornamenti via GitHub Releases
├── view_log.py             # Lettura/filtro del file di log
├── help.py                 # Testo della guida (IT/EN)
├── sponsor.py              # Info sponsor + QR code (qrcode + wand)
├── about.py                # Testo "Informazioni su"
├── lang/                   # Localizzazione interfaccia
│   ├── language_manager.py # Gestore lingua corrente, tr()
│   └── translations.py     # Dizionario traduzioni IT/EN
├── pipeline.py             # Flusso di analisi condiviso da CLI e GUI
├── analysis.py             # Classificazione celle, raccomandazioni, soglie (THRESHOLDS)
├── data_reader.py          # Lettura/normalizzazione export CSV/Excel, alias e validazione
├── congestion_check.py     # Verifica rapida della sola congestione traffico
├── charts.py               # Grafici: distribuzione PRB, scatter copertura, mappa, trend
├── report_export.py        # Export report HTML (autonomo) e PDF (multi-pagina)
├── sample_data.py          # Generatore di dataset sintetico di esempio
├── version.py              # Versione del progetto (SemVer)
├── logger.py               # Logging su file (logs/netplan.log) + console
├── requirements.txt        # Dipendenze runtime
├── requirements-dev.txt    # Dipendenze di sviluppo (test)
├── data/                   # CSV di input
│   └── sample_kpis.csv     # Dataset sintetico generato da sample_data.py
├── output/                 # Report e grafici generati
├── logs/                   # Log applicativo (rotating file)
├── tests/                  # Test pytest
│   ├── conftest.py         # Fixture: CSV sintetico + DataFrame
│   ├── test_analysis.py
│   ├── test_congestion_check.py
│   ├── test_data_reader.py
│   └── test_pipeline.py
├── COMPILER/               # Build eseguibili
│   ├── comp.py             # Script di compilazione Nuitka -> dist/
│   │                       # (Netplan.exe, Netplan-CLI.exe, congestion_check.exe)
│   └── clean_cache.py      # Pulizia __pycache__/.pyc (eseguita da comp.py)
├── docs/                   # Documentazione estesa
│   ├── STRUCT.md           # Questo file
│   ├── SOGLIE.md           # Configurazione delle soglie
│   └── GUI.md              # Uso dell'interfaccia grafica
├── README.md
├── CHANGELOG.md
├── TO_DO.md
├── SECURITY.md
└── LICENSE                 # Licenza proprietaria
```

## Flusso dei dati

```text
export CSV/XLSX (OSS/PM)
      │
      ▼
data_reader.read_cell_data ──► validazione + normalizzazione colonne
      │
      ▼
analysis.build_report ───────► per_cell_summary + classify_cell + recommendation
      │
      ├─► analysis.site_level_summary        (vista per sito)
      ├─► report_per_cella.csv / .xlsx        (export tabellari)
      ├─► charts.make_charts                  (PNG statici)
      ├─► charts.make_trend_charts            (PNG trend temporali)
      └─► report_export                       (HTML + PDF)
```

## Convenzioni

- **Versione**: `version.py`, Semantic Versioning 2.0.0.
- **Log**: `logger.get_logger(__name__)`; file rotante in `logs/netplan.log`.
- **Test**: `pytest tests/`; i fixture generano dati sintetici in tmp.
- **Soglie**: `analysis.THRESHOLDS` sono i default; sovrascrivibili da file
  (vedi `docs/SOGLIE.md`) o passando un dict a `build_report`/`run_analysis`.
