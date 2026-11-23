# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.1.0/),
e il progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [Non rilasciato]

### Aggiunto

- `COMPILER/comp.py`: script di compilazione Nuitka per gli eseguibili
  standalone (GUI, CLI principale, congestion check) in `dist/`.
- `assets/icon.png` + `assets/icon.ico`: icona dell'applicazione, usata
  come icona della finestra GUI e degli eseguibili compilati
  (`--windows-icon-from-ico`, assets inclusi nel pacchetto).
- `LICENSE`: licenza proprietaria
- `lang/`: sistema di localizzazione IT/EN (`language_manager.py` con
  `tr()`, `translations.py` con il dizionario delle stringhe).
- `menu.py`: barra dei menu GUI con voci separate **Log**,
  **Impostazioni** e **Help**.
- `view_log.py` + dialogo GUI: visualizzatore di `logs/netplan.log` con
  filtri per livello e testo.
- `settings.py`: preferenze persistenti via QSettings (lingua, cartella
  output, soglie, opzioni di export).
- `update.py`: controllo aggiornamenti via API GitHub Releases con
  confronto SemVer, eseguito in thread dalla GUI.
- `help.py`, `about.py`, `sponsor.py`: finestre Guida (IT/EN),
  Informazioni e Sponsor (PayPal, Monero con QR code via qrcode+wand).
- Modalità subscriber opzionale (`--subscriber` / checkbox GUI): i file
  con MSISDN/IMSI restano rifiutati per default; se abilitata produce
  `report_per_abbonato.csv` con riepilogo per abbonato.
- `analysis.technology_summary` + `report_per_tecnologia.csv` +
  `technology_users.png`: analisi per tecnologia/generazione 2G/3G/4G/5G
  (`tech_generation`).
- Alias colonne per export OSS/PM Nokia/Ericsson/Huawei e
  `detect_vendor` per il riconoscimento automatico del formato.
- `--mingw64` nello script di compilazione (fix toolchain gcc di Nuitka).

## [0.2.0] - 2026-11-23

### Aggiunto (0.2.0)

- `gui.py`: interfaccia grafica PySide6 con selezione file/cartelle,
  esecuzione in thread separato, tabelle con severità colorata e
  visualizzazione dei grafici.
- `pipeline.py`: flusso di analisi completo condiviso da CLI e GUI.
- `charts.py`: grafici spostati da `main.py`; nuovo grafico di trend
  temporale delle celle peggiori (`trend_celle.png`) quando il file
  contiene più rilevazioni.
- `report_export.py`: report HTML autonomo (grafici incorporati) e
  report PDF multi-pagina.
- `version.py`: versione del progetto (0.2.0, Semantic Versioning).
- `logger.py`: logging su file rotante in `logs/netplan.log`.
- `tests/`: suite pytest (31 test) per reader, analisi, congestion check
  e pipeline end-to-end.
- `docs/`: `STRUCT.md` (struttura e flusso dati), `SOGLIE.md`
  (configurazione soglie e validazione), `GUI.md`.
- `requirements-dev.txt` per le dipendenze di sviluppo.
- Alias colonna `band` e supporto a più tecnologie/bande per cella nel
  medesimo export (una riga per combinazione cella/tecnologia/banda).
- Opzioni CLI `--thresholds`, `--strict`, `--no-html`, `--no-pdf`,
  `--trend-cells`, `--version` in `main.py`; `--thresholds` e `--strict`
  anche in `congestion_check.py`.

### Modificato

- `analysis.py`: `build_report` accetta DataFrame o percorso file;
  soglie passabili come parametro (`load_thresholds` per file
  JSON/chiave=valore); classificazione tollerante alle metriche assenti;
  riepilogo per sito con tecnologie e bande.
- `data_reader.py`: validazione più rigorosa — range percentuali, RSRP
  plausibile, righe duplicate, timestamp non riconosciuti, alias ambigui,
  file vuoto; modalità `strict` che trasforma gli avvisi in errori;
  messaggi d'errore con elenco degli alias accettati.
- `sample_data.py`: genera anche la colonna `band`; path di output
  relativo `data/sample_kpis.csv`.
- `requirements.txt`: aggiunte PySide6.

## [0.1.0] - 2026-11-23

### Aggiunto (0.1.0)

- `main.py`: CLI per l'analisi dei KPI aggregati di cella con generazione di
  report CSV/Excel e grafici (mappa celle, scatter copertura, distribuzione PRB).
- `analysis.py`: logica di classificazione di congestione e buchi di copertura
  con soglie configurabili (`THRESHOLDS`) e raccomandazioni di pianificazione.
- `data_reader.py`: lettura e normalizzazione di export reali CSV/Excel con
  riconoscimento automatico di nomi di colonna alternativi (`COLUMN_ALIASES`).
- `congestion_check.py`: verifica rapida dello stato di congestione traffico,
  ordinata per gravità, senza generare il report completo.
- `sample_data.py`: generatore di dataset sintetico di esempio.
- `requirements.txt`: dipendenze del progetto (pandas, numpy, matplotlib,
  openpyxl).
- Documentazione iniziale in `README.md`.
