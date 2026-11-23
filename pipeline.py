"""
pipeline.py
Flusso di analisi completo condiviso da main.py (CLI) e gui.py (GUI):
lettura/validazione input -> report per cella/sito -> export CSV/Excel
-> grafici -> export HTML/PDF.
"""

import os

import pandas as pd

from analysis import (
    THRESHOLDS,
    build_report,
    site_level_summary,
    subscriber_summary,
    technology_summary,
)
from charts import make_charts, make_technology_chart, make_trend_charts
from data_reader import describe_dataset, read_cell_data, subscriber_id_column
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
    allow_subscriber_data: bool = False,
) -> dict:
    """Esegue l'intera pipeline di pianificazione.

    Args:
        input_path: file CSV/XLSX con KPI aggregati per cella.
        outdir: cartella di output per report e grafici.
        thresholds: soglie personalizzate (default: analysis.THRESHOLDS).
        trend_cells: numero massimo di celle nel grafico dei trend.
        html_report / pdf_report: attiva/disattiva i rispettivi export.
        strict: validazione input rigorosa (avvisi -> errori).
        allow_subscriber_data: accetta dati a livello singolo abbonato
            e produce anche il report per-abbonato.

    Returns:
        Dizionario con i DataFrame prodotti e i percorsi dei file creati:
        {"df", "cell_summary", "site_summary", "tech_summary",
         "subscriber_summary", "csv_cell", "csv_site", "csv_tech",
         "csv_subscriber", "xlsx", "charts", "html", "pdf", "description"}
    """
    th = thresholds or THRESHOLDS
    os.makedirs(outdir, exist_ok=True)

    log.info("Avvio analisi: input=%s outdir=%s", input_path, outdir)
    df = read_cell_data(
        input_path, strict=strict, allow_subscriber_data=allow_subscriber_data
    )
    description = describe_dataset(df)

    cell_summary = build_report(df, thresholds=th)
    site_summary = site_level_summary(cell_summary)
    tech_summary = technology_summary(df)

    subscriber_df = None
    if allow_subscriber_data and subscriber_id_column(df) is not None:
        subscriber_df = subscriber_summary(df)

    csv_cell = os.path.join(outdir, "report_per_cella.csv")
    csv_site = os.path.join(outdir, "report_per_sito.csv")
    cell_summary.to_csv(csv_cell, index=False)
    site_summary.to_csv(csv_site, index=False)

    csv_tech = None
    if not tech_summary.empty:
        csv_tech = os.path.join(outdir, "report_per_tecnologia.csv")
        tech_summary.to_csv(csv_tech, index=False)

    csv_subscriber = None
    if subscriber_df is not None and not subscriber_df.empty:
        csv_subscriber = os.path.join(outdir, "report_per_abbonato.csv")
        subscriber_df.to_csv(csv_subscriber, index=False)

    log.info("Report CSV scritti in %s", outdir)

    xlsx_path = os.path.join(outdir, "report_pianificazione_copertura.xlsx")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            cell_summary.to_excel(writer, sheet_name="Per Cella", index=False)
            site_summary.to_excel(writer, sheet_name="Per Sito", index=False)
            if not tech_summary.empty:
                tech_summary.to_excel(writer, sheet_name="Per Tecnologia", index=False)
            if subscriber_df is not None and not subscriber_df.empty:
                subscriber_df.to_excel(writer, sheet_name="Per Abbonato", index=False)
    except Exception as e:
        log.warning("Export Excel saltato: %s", e)
        xlsx_path = None

    chart_paths = make_charts(cell_summary, outdir, th)
    chart_paths += make_technology_chart(df, outdir)
    chart_paths += make_trend_charts(df, cell_summary, outdir, th, top_n=trend_cells)

    extra_sections = []
    if not tech_summary.empty:
        extra_sections.append(("Report per tecnologia", tech_summary))
    if subscriber_df is not None and not subscriber_df.empty:
        extra_sections.append(("Report per abbonato", subscriber_df))

    html_path = (
        write_html_report(
            cell_summary, site_summary, chart_paths, outdir, extra_sections
        )
        if html_report
        else None
    )

    pdf_path = None
    if pdf_report:
        try:
            pdf_path = write_pdf_report(
                cell_summary, site_summary, chart_paths, outdir, extra_sections
            )
        except Exception as e:
            log.warning("Export PDF saltato: %s", e)

    return {
        "df": df,
        "cell_summary": cell_summary,
        "site_summary": site_summary,
        "tech_summary": tech_summary,
        "subscriber_summary": subscriber_df,
        "csv_cell": csv_cell,
        "csv_site": csv_site,
        "csv_tech": csv_tech,
        "csv_subscriber": csv_subscriber,
        "xlsx": xlsx_path,
        "charts": chart_paths,
        "html": html_path,
        "pdf": pdf_path,
        "description": description,
    }
