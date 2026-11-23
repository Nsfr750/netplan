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

Questo strumento è progettato per lavorare su **KPI aggregati e anonimizzati
a livello di cella**. I file con dati a livello di singolo utente (numeri,
IMSI, identificativi personali) sono **rifiutati per default**.

È possibile abilitare la modalità subscriber (`--subscriber` da CLI o
l'opzione corrispondente nella GUI) **solo per analisi autorizzate su dati
di propria competenza** e nel rispetto delle norme sulla protezione dei
dati personali (GDPR): in tal caso il tool produce un riepilogo aggregato
per abbonato (`report_per_abbonato.csv`). La responsabilità del trattamento
resta dell'utente che abilita la modalità.

## Misure di protezione integrate

- `data_reader.py` rifiuta automaticamente i file che contengono colonne a
  livello di singolo abbonato (`msisdn`, `imsi`, `imei`, numero di telefono,
  indirizzo IP...): l'elaborazione si interrompe con un errore esplicito,
  salvo attivazione esplicita della modalità subscriber.
- I valori di input sono validati (range percentuali, RSRP plausibile,
  duplicati); con `--strict` gli avvisi diventano errori bloccanti.
- I log applicativi (`logs/netplan.log`) non contengono dati dei KPI,
  solo metadati di esecuzione.
