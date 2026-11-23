"""
congestion_check.py
Tool rapido per leggere i dati di una o più celle e verificare lo stato
di congestione del traffico (utilizzo risorse radio, traffico, utenze
medie connesse). Pensato per un controllo puntuale/quotidiano, più
snello del report completo di pianificazione (vedi main.py).

Uso:
    python congestion_check.py --input data/sample_kpis.csv
    python congestion_check.py --input data/sample_kpis.csv --site SITE_002
    python congestion_check.py --input data/sample_kpis.csv --only-critical
    python congestion_check.py --input data/sample_kpis.csv --thresholds soglie.json
"""

import argparse
import sys

import pandas as pd

from analysis import THRESHOLDS, load_thresholds
from data_reader import read_cell_data, describe_dataset, DataValidationError
from logger import get_logger

log = get_logger(__name__)

def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Se ci sono più timestamp, prende l'ultima rilevazione per ciascuna cella.
    Altrimenti assume che il file sia già uno snapshot puntuale."""
    if "timestamp_hour" in df.columns and df["timestamp_hour"].notna().any():
        df = df.sort_values("timestamp_hour")
        df = df.groupby("cell_id", as_index=False).tail(1)
    return df


def congestion_level(prb_pct: float, thresholds: dict | None = None) -> str:
    """Classifica una cella OK/ATTENZIONE/CRITICO in base al solo PRB%."""
    th = thresholds or THRESHOLDS
    if pd.isna(prb_pct):
        return "N/D"
    if prb_pct >= th["prb_congestion_critical"]:
        return "CRITICO"
    if prb_pct >= th["prb_congestion_warning"]:
        return "ATTENZIONE"
    return "OK"


def check_congestion(df: pd.DataFrame, thresholds: dict | None = None) -> pd.DataFrame:
    """Snapshot per cella con livello di congestione, ordinato per gravità."""
    snap = latest_snapshot(df)

    cols = ["site_id", "cell_id", "prb_utilization_pct"]
    for optional in [
        "technology",
        "band",
        "traffic_erlang",
        "connected_users_avg",
        "timestamp_hour",
    ]:
        if optional in snap.columns:
            cols.append(optional)

    result = snap[cols].copy()
    result["congestion_level"] = result["prb_utilization_pct"].apply(
        congestion_level, thresholds=thresholds
    )

    sev_order = {"CRITICO": 0, "ATTENZIONE": 1, "OK": 2, "N/D": 3}
    result["_rank"] = result["congestion_level"].map(sev_order)
    result = result.sort_values(
        ["_rank", "prb_utilization_pct"], ascending=[True, False]
    ).drop(columns="_rank")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Verifica rapida della congestione di traffico per cella"
    )
    parser.add_argument(
        "--input", required=True, help="File CSV/XLSX con KPI aggregati per cella"
    )
    parser.add_argument("--site", help="Filtra per un singolo site_id")
    parser.add_argument(
        "--only-critical",
        action="store_true",
        help="Mostra solo le celle in stato CRITICO",
    )
    parser.add_argument(
        "--export", help="Percorso CSV opzionale dove salvare il risultato"
    )
    parser.add_argument(
        "--thresholds", help="File JSON o chiave=valore con soglie personalizzate"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Considera errori anche gli avvisi di validazione dei dati",
    )
    parser.add_argument(
        "--subscriber",
        action="store_true",
        help="Accetta dati a livello singolo abbonato (MSISDN/IMSI)",
    )
    args = parser.parse_args()

    try:
        thresholds = load_thresholds(args.thresholds) if args.thresholds else None
        df = read_cell_data(
            args.input,
            require_congestion_fields=True,
            strict=args.strict,
            allow_subscriber_data=args.subscriber,
        )
    except (FileNotFoundError, DataValidationError, ValueError) as e:
        print(f"Errore nella lettura dei dati: {e}", file=sys.stderr)
        log.error("Lettura fallita: %s", e)
        sys.exit(1)

    print(describe_dataset(df))
    print("-" * 60)

    if args.site:
        df = df[df["site_id"] == args.site]
        if df.empty:
            print(f"Nessuna cella trovata per site_id='{args.site}'.")
            sys.exit(0)

    result = check_congestion(df, thresholds=thresholds)

    if args.only_critical:
        result = result[result["congestion_level"] == "CRITICO"]

    if result.empty:
        print("Nessuna cella corrisponde ai filtri indicati.")
        sys.exit(0)

    with pd.option_context("display.max_rows", None, "display.width", 140):
        print(result.to_string(index=False))

    n_crit = (result["congestion_level"] == "CRITICO").sum()
    n_warn = (result["congestion_level"] == "ATTENZIONE").sum()
    print("-" * 60)
    print(
        f"Celle analizzate: {len(result)} | Critiche: {n_crit} | Attenzione: {n_warn}"
    )
    log.info("Controllo congestione: %d celle (%d critiche).", len(result), n_crit)

    if args.export:
        result.to_csv(args.export, index=False)
        print(f"Risultato esportato in: {args.export}")


if __name__ == "__main__":
    main()
