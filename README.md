# Strumento di pianificazione copertura radio (KPI aggregati)

Analizza KPI **aggregati e anonimizzati a livello di cella** (traffico,
utilizzo risorse radio, drop rate, handover, statistiche di potenza del
segnale) per individuare celle congestionate e probabili buchi di
copertura, con raccomandazioni di pianificazione.

**Cosa NON fa, volutamente:** non tratta né richiede dati a livello di
singolo utente/numero/IMSI. Tutti gli indicatori sono medie o percentuali
calcolate su tutta la cella in una finestra temporale, come normalmente
esportati dai sistemi OSS/NMS (Nokia, Ericsson, Huawei, ecc.) o da un
data warehouse di rete.

## Struttura del progetto

```text
netplan/
├── main.py                 # CLI: pipeline completa (report + grafici)
├── gui.py                  # interfaccia grafica PySide6
├── pipeline.py             # flusso di analisi condiviso da CLI e GUI
├── analysis.py             # classificazione, raccomandazioni, soglie
├── data_reader.py          # lettura/normalizzazione export (CSV/Excel, alias)
├── congestion_check.py     # verifica rapida della sola congestione traffico
├── charts.py               # grafici (PRB, copertura, mappa, trend temporali)
├── report_export.py        # export report HTML e PDF
├── sample_data.py          # genera un CSV di esempio (dati sintetici)
├── version.py              # versione (SemVer)
├── logger.py               # logging su file (logs/netplan.log)
├── tests/                  # test pytest
├── docs/                   # documentazione estesa (STRUCT, SOGLIE, GUI)
├── data/                   # CSV di input
└── output/                 # report e grafici generati
```

## Utilizzo

```bash
pip install -r requirements.txt

# 1. (opzionale) genera un dataset di esempio
python sample_data.py

# 2. esegui l'analisi sul tuo CSV reale (o su quello di esempio)
python main.py --input data/sample_kpis.csv --outdir output
```

Opzioni utili di `main.py`:

```bash
# soglie personalizzate da file (JSON o chiave=valore)
python main.py --input data/sample_kpis.csv --thresholds mie_soglie.json

# validazione rigorosa: anche gli avvisi sui dati bloccano l'analisi
python main.py --input data/sample_kpis.csv --strict

# disattivare i singoli export
python main.py --input data/sample_kpis.csv --no-pdf --no-html
```

## Interfaccia grafica

```bash
python gui.py
```

Finestra PySide6 con selezione file/cartelle, opzioni di export e
visualizzazione di riepilogo, tabelle e grafici. Menu con voci separate:
**Log** (visualizzatore con filtri), **Impostazioni** (preferenze e
lingua IT/EN) e **Help** (guida, controllo aggiornamenti, sponsor,
about). Vedi `docs/GUI.md`.

## Verifica rapida della congestione

Per un controllo puntuale (es. quotidiano) dello stato di congestione,
senza generare l'intero report di pianificazione, usa `congestion_check.py`.
Legge CSV o Excel, riconosce automaticamente molti nomi di colonna
alternativi (vedi `COLUMN_ALIASES` in `data_reader.py`) e, se nel file ci
sono più rilevazioni nel tempo, usa l'ultima disponibile per cella.

```bash
# Stato di congestione di tutte le celle, ordinate per gravità
python congestion_check.py --input data/sample_kpis.csv

# Solo un sito specifico
python congestion_check.py --input data/sample_kpis.csv --site SITE_002

# Solo le celle in stato critico, esportando il risultato
python congestion_check.py --input data/sample_kpis.csv --only-critical --export output/congestione_critiche.csv
```

Questo modulo **rifiuta automaticamente** qualunque file che contenga
colonne a livello di singolo abbonato (es. `msisdn`, `imsi`, `imei`,
numero di telefono): se individuate, l'elaborazione si interrompe con un
errore esplicito invece di procedere.

## Formato CSV atteso in input

Una riga per cella per intervallo temporale (es. per ora), con queste colonne:

| Colonna | Descrizione |
| --- | --- |
| `timestamp_hour` | Timestamp dell'intervallo aggregato |
| `site_id` | Identificativo del sito/ponte radio |
| `cell_id` | Identificativo della cella/settore |
| `technology` | LTE / NR / UMTS ecc. |
| `band` | Banda di frequenza (es. B3, n78) — opzionale |
| `latitude`, `longitude` | Posizione del sito |
| `azimuth_deg` | Orientamento del settore |
| `traffic_erlang` | Traffico voce in Erlang |
| `data_volume_gb` | Volume dati trasportato |
| `prb_utilization_pct` | % utilizzo risorse radio (PRB) |
| `connected_users_avg` | Numero medio di utenze contemporanee (solo conteggio, non identificativi) |
| `call_drop_rate_pct` | % chiamate cadute |
| `handover_success_rate_pct` | % handover riusciti |
| `avg_rsrp_dbm` | Potenza media ricevuta |
| `weak_signal_sample_pct` | % di campioni con segnale sotto soglia (proxy di buco di copertura) |

Questi dati tipicamente provengono da export OSS/PM (Performance
Management) dell'operatore, già aggregati dal sistema di rete stesso.
Se lo stesso file contiene più tecnologie o bande per cella, ognuna
produce una riga separata nel report.

## Output

- `output/report_per_cella.csv` / `.xlsx` — stato e raccomandazione per ogni cella
- `output/report_per_sito.csv` — vista aggregata per sito (utile per decidere upgrade vs nuovo sito)
- `output/report_pianificazione_copertura.html` — report completo autonomo
- `output/report_pianificazione_copertura.pdf` — report PDF multi-pagina
- `output/prb_distribution.png` — istogramma congestione
- `output/coverage_scatter.png` — qualità del segnale per cella
- `output/cell_map.png` — mappa geografica con stato (verde/arancio/rosso)
- `output/trend_celle.png` — trend temporale delle celle peggiori (se ci sono più rilevazioni)

## Personalizzazione soglie

Le soglie di congestione/copertura sono in `analysis.py`, dizionario
`THRESHOLDS`. Si possono sovrascrivere senza toccare il codice con
`--thresholds file.json` (o formato chiave=valore). Dettagli in
`docs/SOGLIE.md`.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Licenza

Licenza proprietaria — vedi `LICENSE`.
© Copyright 2024-2026 Nsfr750 - All rights reserved.
