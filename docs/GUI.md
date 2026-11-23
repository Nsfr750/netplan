# Interfaccia grafica (gui.py)

GUI desktop basata su **PySide6** che espone le stesse funzioni della CLI
tramite la pipeline condivisa (`pipeline.run_analysis`).

## Avvio

```bash
python -m pip install -r requirements.txt
python gui.py
```

## Funzioni

- Selezione del file KPI di input (`.csv`, `.xlsx`, `.xls`)
- Scelta della cartella di output
- File di soglie personalizzato opzionale (vedi `docs/SOGLIE.md`)
- Opzioni: report HTML, report PDF, validazione strict, numero di celle
  nei grafici di trend
- Esecuzione in thread separato (la finestra resta reattiva)
- Interfaccia in **italiano e inglese** (Impostazioni → Lingua)

## Menu

La barra dei menu ha tre voci separate:

- **Log** → *Visualizza log*: finestra con il contenuto di
  `logs/netplan.log`, filtrabile per livello (DEBUG..CRITICAL) e per
  testo; *Apri cartella log*: apre la cartella dei log nel file manager.
- **Impostazioni** → *Preferenze*: lingua interfaccia e cartella di
  output predefinita (persistite con QSettings); *Lingua*: sottomenu
  Italiano/English con applicazione immediata.
- **Help** → *Guida* (IT/EN), *Controlla aggiornamenti* (confronto con
  l'ultima release GitHub), *Sostieni il progetto* (PayPal, Monero con
  QR code, GitHub), *Informazioni su Netplan*.

## Schede dei risultati

- **Riepilogo**: descrizione del dataset, conteggio severità, file prodotti
- **Per cella**: tabella del report con la colonna `severity` colorata
- **Per sito**: vista aggregata per sito
- **Grafici**: tutti i PNG generati (mappa, scatter, distribuzione, trend)
