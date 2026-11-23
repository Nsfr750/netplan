# Politica di sicurezza

## Versioni supportate

| Versione | Supportata          |
| -------- | ------------------- |
| 0.2.x    | :white_check_mark:  |
| 0.1.x    | :x:                 |

## Segnalazione di una vulnerabilità

Per segnalare una vulnerabilità di sicurezza, invia un'email a [info@tuxxle.org](mailto:info@tuxxle.org) includendo:

- descrizione del problema e del suo impatto potenziale;
- passi per riprodurlo (se possibile con un file di input di esempio);
- versione del progetto e di Python utilizzate.

Non aprire issue pubbliche su GitHub per vulnerabilità di sicurezza.

Riceverai una risposta appena possibile. Se la segnalazione è confermata,
verrà preparata una correzione e pubblicato un avviso nel `CHANGELOG.md`.

## Note sui dati

Questo strumento è progettato per lavorare **esclusivamente su KPI aggregati
e anonimizzati a livello di cella**. Non inserire nei file di input dati a
livello di singolo utente (numeri, IMSI, identificativi personali): lo
strumento non li richiede e non li tratta.

## Misure di protezione integrate

- `data_reader.py` rifiuta automaticamente i file che contengono colonne a
  livello di singolo abbonato (`msisdn`, `imsi`, `imei`, numero di telefono,
  indirizzo IP...): l'elaborazione si interrompe con un errore esplicito.
- I valori di input sono validati (range percentuali, RSRP plausibile,
  duplicati); con `--strict` gli avvisi diventano errori bloccanti.
- I log applicativi (`logs/netplan.log`) non contengono dati dei KPI,
  solo metadati di esecuzione.
