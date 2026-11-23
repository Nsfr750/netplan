"""
main.py
Strumento di supporto alla pianificazione della copertura radio per
operatori di rete, basato su KPI aggregati e anonimizzati per cella.

Uso:
    python main.py --input data/sample_kpis.csv --outdir output
    python main.py --input data/sample_kpis.csv --thresholds soglie.json
    python main.py --input data/sample_kpis.csv --strict --no-pdf

Il formato CSV atteso (una riga per cella per ora) è descritto in
sample_data.py e nel README.
"""

import argparse
import sys

from analysis import load_thresholds
from data_reader import DataValidationError
from logger import get_logger
from pipeline import run_analysis
from version import __version__

log = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Analisi KPI aggregati di rete per pianificazione copertura"
    )
    parser.add_argument(
        "--input", required=True, help="CSV/XLSX con KPI aggregati per cella"
    )
    parser.add_argument(
        "--outdir", default="output", help="Cartella di output per report e grafici"
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
        "--no-html", action="store_true", help="Non generare il report HTML"
    )
    parser.add_argument(
        "--no-pdf", action="store_true", help="Non generare il report PDF"
    )
    parser.add_argument(
        "--trend-cells",
        type=int,
        default=6,
        help="Numero di celle nei grafici di trend (default: 6)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args = parser.parse_args()

    try:
        thresholds = load_thresholds(args.thresholds) if args.thresholds else None
        result = run_analysis(
            args.input,
            args.outdir,
            thresholds=thresholds,
            trend_cells=args.trend_cells,
            html_report=not args.no_html,
            pdf_report=not args.no_pdf,
            strict=args.strict,
        )
    except (FileNotFoundError, DataValidationError, ValueError) as e:
        print(f"Errore: {e}", file=sys.stderr)
        log.error("Analisi fallita: %s", e)
        sys.exit(1)

    cell_summary = result["cell_summary"]
    n_critiche = (cell_summary["severity"] == "CRITICO").sum()
    n_attenzione = (cell_summary["severity"] == "ATTENZIONE").sum()
    n_ok = (cell_summary["severity"] == "OK").sum()

    print("=" * 60)
    print("REPORT DI PIANIFICAZIONE COPERTURA")
    print("=" * 60)
    print(result["description"])
    print("-" * 60)
    print(f"Celle totali analizzate: {len(cell_summary)}")
    print(f"  - Critiche:   {n_critiche}")
    print(f"  - Attenzione: {n_attenzione}")
    print(f"  - OK:         {n_ok}")
    print()
    print(f"Report dettagliato per cella: {result['csv_cell']}")
    print(f"Report aggregato per sito:    {result['csv_site']}")
    if result["xlsx"]:
        print(f"Report Excel:                 {result['xlsx']}")
    if result["html"]:
        print(f"Report HTML:                  {result['html']}")
    if result["pdf"]:
        print(f"Report PDF:                   {result['pdf']}")
    print(f"Grafici salvati in:           {args.outdir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
