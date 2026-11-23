"""
pipeline.py
Flusso di analisi completo condiviso da main.py (CLI) e gui.py (GUI):
lettura/validazione input -> report per cella/sito -> export CSV/Excel
-> grafici -> export HTML/PDF.
"""

import os

import pandas as pd

from analysis import THRESHOLDS, build_report, site_level_summary
from charts import make_charts, make_trend_charts
from data_reader import describe_dataset, read_cell_data
from logger import get_logger
from report_export import write_html_report, write_pdf_report

log = get_logger(__name__)


def run_analysis(
    input_path: str,
    outdir: str,
    thresholds: dict | None = None,
    trend_cells: int = 6,
    html_report: bool = True,
    pdf_report: bool = True,
    strict: bool = False,
) -> dict:
    """Esegue l'intera pipeline di pianificazione.

    Args:
        input_path: file CSV/XLSX con KPI aggregati per cella.
        outdir: cartella di output per report e grafici.
        thresholds: soglie personalizzate (default: analysis.THRESHOLDS).
        trend_cells: numero massimo di celle nel grafico dei trend.
        html_report / pdf_report: attiva/disattiva i rispettivi export.
        strict: validazione input rigorosa (avvisi -> errori).

    Returns:
        Dizionario con i DataFrame prodotti e i percorsi dei file creati:
        {"df", "cell_summary", "site_summary", "csv_cell", "csv_site",
         "xlsx", "charts", "html", "pdf", "description"}
    """
    th = thresholds or THRESHOLDS
    os.makedirs(outdir, exist_ok=True)

    log.info("Avvio analisi: input=%s outdir=%s", input_path, outdir)
    df = read_cell_data(input_path, strict=strict)
    description = describe_dataset(df)

    cell_summary = build_report(df, thresholds=th)
    site_summary = site_level_summary(cell_summary)

    csv_cell = os.path.join(outdir, "report_per_cella.csv")
    csv_site = os.path.join(outdir, "report_per_sito.csv")
    cell_summary.to_csv(csv_cell, index=False)
    site_summary.to_csv(csv_site, index=False)
    log.info("Report CSV scritti in %s", outdir)

    xlsx_path = os.path.join(outdir, "report_pianificazione_copertura.xlsx")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            cell_summary.to_excel(writer, sheet_name="Per Cella", index=False)
            site_summary.to_excel(writer, sheet_name="Per Sito", index=False)
    except Exception as e:
        log.warning("Export Excel saltato: %s", e)
        xlsx_path = None

    chart_paths = make_charts(cell_summary, outdir, th)
    chart_paths += make_trend_charts(df, cell_summary, outdir, th, top_n=trend_cells)

    html_path = (
        write_html_report(cell_summary, site_summary, chart_paths, outdir)
        if html_report
        else None
    )

    pdf_path = None
    if pdf_report:
        try:
            pdf_path = write_pdf_report(cell_summary, site_summary, chart_paths, outdir)
        except Exception as e:
            log.warning("Export PDF saltato: %s", e)

    return {
        "df": df,
        "cell_summary": cell_summary,
        "site_summary": site_summary,
        "csv_cell": csv_cell,
        "csv_site": csv_site,
        "xlsx": xlsx_path,
        "charts": chart_paths,
        "html": html_path,
        "pdf": pdf_path,
        "description": description,
    }
