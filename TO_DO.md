# To Do

## In corso

## Pianificato

- [ ] Import diretto da formati OSS/NMS specifici (Nokia, Ericsson, Huawei)

## Idee / backlog

- [ ] Firma digitale degli eseguibili compilati (certificato code signing)
- [ ] Installer Windows per la versione compilata (es. Inno Setup)
- [ ] Aggiornamento automatico versione/release (`update.py`)

## Completato (v0.2.0)

- [x] Aggiungere test con pytest nella cartella `tests/`
- [x] Aggiungere `version.py` (Semantic Versioning 2.0.0)
- [x] Validazione più rigorosa delle colonne di input con messaggi d'errore
      dettagliati (range valori, duplicati, alias ambigui, modalità strict)
- [x] Supporto per soglie configurabili da file/CLI (senza modificare
      `THRESHOLDS` nel codice)
- [x] Esportazione del report anche in formato HTML/PDF
- [x] Grafici aggiuntivi: trend temporale per cella quando il file contiene
      più rilevazioni
- [x] Gestione di più tecnologie/bande (4G/5G) nel medesimo export
- [x] Interfaccia grafica (GUI) con PySide6
- [x] Documentazione estesa nella cartella `docs/` (incluso `STRUCT.md`)
- [x] Logging su file tramite `logger.py`
- [x] Script di compilazione Nuitka (`COMPILER/comp.py`)
- [x] Icona dell'applicazione (`assets/icon.png` + `assets/icon.ico`)
- [x] Licenza proprietaria (`LICENSE`)
- [x] Sistema di lingue IT/EN (`lang/language_manager.py` + `translations.py`)
- [x] Menu GUI con voci separate: Log, Impostazioni, Help
- [x] Visualizzatore log con filtri (livello + testo)
- [x] Impostazioni persistenti (QSettings)
- [x] Controllo aggiornamenti da GitHub Releases (`update.py`)
- [x] Finestre Help, Sponsor (con QR) e About
