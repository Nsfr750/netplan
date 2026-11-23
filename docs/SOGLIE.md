# Configurazione delle soglie

Le soglie di allarme sono definite in `analysis.py` nel dizionario
`THRESHOLDS`:

| Chiave | Default | Significato |
| --- | --- | --- |
| `prb_congestion_warning` | 70.0 | % PRB oltre cui la cella è "a rischio" |
| `prb_congestion_critical` | 85.0 | % PRB di picco oltre cui la cella è critica |
| `drop_rate_warning` | 2.0 | % drop rate medio anomalo |
| `drop_rate_critical` | 4.0 | % drop rate di picco critico |
| `ho_success_warning` | 95.0 | % handover success sotto cui si segnala |
| `weak_signal_warning` | 15.0 | % campioni deboli: copertura debole |
| `weak_signal_critical` | 30.0 | % campioni deboli: probabile buco di copertura |

## Sovrascrivere le soglie da file

Senza modificare il codice, si può passare un file con `--thresholds`
(sia in `main.py` che in `congestion_check.py`):

```bash
python main.py --input data/sample_kpis.csv --thresholds mie_soglie.json
```

### Formato JSON

```json
{
  "prb_congestion_warning": 65,
  "prb_congestion_critical": 90,
  "weak_signal_critical": 25
}
```

### Formato chiave=valore

```text
# mie_soglie.txt — una soglia per riga, commenti con '#'
prb_congestion_warning = 65
prb_congestion_critical = 90
weak_signal_critical = 25
```

Le chiavi non presenti nel file mantengono il valore di default; le
chiavi sconosciute vengono ignorate con un avviso nel log.

## Validazione dei dati in input

`data_reader.read_cell_data` verifica automaticamente:

- **colonne proibite** a livello abbonato (msisdn, imsi, ...) → errore;
- **colonne obbligatorie** (`site_id`, `cell_id`, `prb_utilization_pct`)
  → errore con elenco degli alias accettati;
- **range percentuali** (0-100), RSRP plausibile, righe duplicate,
  timestamp non riconosciuti, alias ambigui → avvisi nel log.

Con `--strict` anche gli avvisi diventano errori bloccanti.
