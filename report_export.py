"""
report_export.py
Esportazione del report di pianificazione in formato HTML (autonomo,
con grafici incorporati in base64) e PDF (multi-pagina, via matplotlib).
"""

import base64
import datetime as dt
import html
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from logger import get_logger

log = get_logger(__name__)

SEVERITY_CSS = {
    "CRITICO": "#c44e52",
    "ATTENZIONE": "#dd8452",
    "OK": "#55a868",
}


def _img_base64(path: str) -> str:
    """Codifica base64 di un'immagine per incorporarla nell'HTML."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _severity_cell(value) -> str:
    color = SEVERITY_CSS.get(value, "#999")
    return f'<td style="background-color:{color};color:#fff;font-weight:bold">{html.escape(str(value))}</td>'


def _df_to_html_table(df: pd.DataFrame) -> str:
    """Tabella HTML con la colonna severity evidenziata a colori."""
    rows = ["<table><thead><tr>"]
    rows += [f"<th>{html.escape(str(c))}</th>" for c in df.columns]
    rows.append("</tr></thead><tbody>")
    for _, r in df.iterrows():
        rows.append("<tr>")
        for c in df.columns:
            if c == "severity":
                rows.append(_severity_cell(r[c]))
            else:
                v = r[c]
                rows.append(
                    f"<td>{html.escape(f'{v:.2f}' if isinstance(v, float) else str(v))}</td>"
                )
        rows.append("</tr>")
    rows.append("</tbody></table>")
    return "".join(rows)


def write_html_report(
    cell_summary: pd.DataFrame,
    site_summary: pd.DataFrame,
    chart_paths: list[str],
    outdir: str,
    extra_sections: list[tuple[str, pd.DataFrame]] | None = None,
) -> str:
    """Genera report_pianificazione_copertura.html e ne restituisce il percorso."""
    n_crit = int((cell_summary["severity"] == "CRITICO").sum())
    n_warn = int((cell_summary["severity"] == "ATTENZIONE").sum())
    n_ok = int((cell_summary["severity"] == "OK").sum())
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    img_tags = "".join(
        f"<h3>{html.escape(os.path.basename(p))}</h3>"
        f'<img src="data:image/png;base64,{_img_base64(p)}" style="max-width:100%">'
        for p in chart_paths
        if os.path.exists(p)
    )

    page = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>Report pianificazione copertura</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 2em; color: #222; }}
h1 {{ border-bottom: 3px solid #4c72b0; padding-bottom: .3em; }}
table {{ border-collapse: collapse; font-size: 12px; margin: 1em 0; }}
th {{ background: #4c72b0; color: #fff; padding: 5px 8px; text-align: left; }}
td {{ border: 1px solid #ccc; padding: 4px 8px; }}
tr:nth-child(even) td {{ background: #f4f6f9; }}
.badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; color: #fff; margin-right: 8px; }}
</style>
</head>
<body>
<h1>Report di pianificazione copertura</h1>
<p>Generato il {now} — dati aggregati e anonimizzati a livello di cella.</p>
<p>
<span class="badge" style="background:#c44e52">Critiche: {n_crit}</span>
<span class="badge" style="background:#dd8452">Attenzione: {n_warn}</span>
<span class="badge" style="background:#55a868">OK: {n_ok}</span>
<span class="badge" style="background:#4c72b0">Celle totali: {len(cell_summary)}</span>
</p>
<h2>Report per cella</h2>
{_df_to_html_table(cell_summary)}
<h2>Report per sito</h2>
{_df_to_html_table(site_summary)}
{"".join(f"<h2>{html.escape(titolo)}</h2>{_df_to_html_table(sec)}" for titolo, sec in (extra_sections or []))}
<h2>Grafici</h2>
{img_tags}
</body>
</html>"""

    path = os.path.join(outdir, "report_pianificazione_copertura.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    log.info("Report HTML: %s", path)
    return path


def _add_table_page(pdf: PdfPages, title: str, df: pd.DataFrame, max_rows: int = 25):
    """Aggiunge una pagina PDF con una tabella pandas (prime max_rows righe)."""
    show = df.head(max_rows)
    fig, ax = plt.subplots(figsize=(11.7, 8.3))  # A4 landscape
    ax.axis("off")
    ax.set_title(f"{title} ({len(show)}/{len(df)} righe)", fontsize=13, pad=18)
    cell_text = [
        [f"{v:.2f}" if isinstance(v, float) else str(v) for v in row]
        for row in show.itertuples(index=False)
    ]
    table = ax.table(
        cellText=cell_text, colLabels=list(show.columns), loc="center", cellLoc="left"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.2)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def write_pdf_report(
    cell_summary: pd.DataFrame,
    site_summary: pd.DataFrame,
    chart_paths: list[str],
    outdir: str,
    extra_sections: list[tuple[str, pd.DataFrame]] | None = None,
) -> str:
    """Genera report_pianificazione_copertura.pdf e ne restituisce il percorso."""
    path = os.path.join(outdir, "report_pianificazione_copertura.pdf")
    n_crit = int((cell_summary["severity"] == "CRITICO").sum())
    n_warn = int((cell_summary["severity"] == "ATTENZIONE").sum())
    n_ok = int((cell_summary["severity"] == "OK").sum())

    with PdfPages(path) as pdf:
        # Pagina di copertina con riepilogo
        fig, ax = plt.subplots(figsize=(8.3, 11.7))
        ax.axis("off")
        ax.text(
            0.5,
            0.80,
            "Report di pianificazione copertura",
            ha="center",
            fontsize=20,
            weight="bold",
        )
        ax.text(
            0.5,
            0.74,
            f"Generato il {dt.datetime.now():%Y-%m-%d %H:%M}",
            ha="center",
            fontsize=11,
        )
        riepilogo = (
            f"Celle analizzate: {len(cell_summary)}\n\n"
            f"  Critiche:   {n_crit}\n"
            f"  Attenzione: {n_warn}\n"
            f"  OK:         {n_ok}"
        )
        ax.text(
            0.5,
            0.55,
            riepilogo,
            ha="center",
            fontsize=13,
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="#f4f6f9", edgecolor="#4c72b0"),
        )
        ax.text(
            0.5,
            0.30,
            "Dati aggregati e anonimizzati a livello di cella.",
            ha="center",
            fontsize=9,
            style="italic",
        )
        pdf.savefig(fig)
        plt.close(fig)

        _add_table_page(pdf, "Report per cella", cell_summary)

        top = cell_summary[cell_summary["severity"] != "OK"]
        if not top.empty:
            _add_table_page(pdf, "Celle con anomalie", top)

        _add_table_page(pdf, "Report per sito", site_summary)

        for titolo, sec in extra_sections or []:
            _add_table_page(pdf, titolo, sec)

        # Una pagina per grafico
        for chart in chart_paths:
            if not os.path.exists(chart):
                continue
            img = plt.imread(chart)
            fig, ax = plt.subplots(figsize=(11.7, 8.3))
            ax.axis("off")
            ax.imshow(img)
            ax.set_title(os.path.basename(chart), fontsize=11)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

    log.info("Report PDF: %s", path)
    return path
