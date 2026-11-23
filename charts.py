"""
charts.py
Generazione dei grafici di pianificazione: distribuzione PRB, scatter
copertura, mappa celle e trend temporali per le celle peggiori quando il
file contiene più rilevazioni nel tempo.
"""

import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from analysis import SEVERITY_COLORS, SEVERITY_ORDER
from logger import get_logger

log = get_logger(__name__)


def make_charts(cell_summary: pd.DataFrame, outdir: str, thresholds: dict) -> list[str]:
    """Genera i grafici statici del report. Restituisce i percorsi dei PNG."""
    os.makedirs(outdir, exist_ok=True)
    paths = []

    colors = cell_summary["severity"].map(SEVERITY_COLORS)

    # 1. Istogramma utilizzo PRB medio per cella
    if cell_summary["avg_prb"].notna().any():
        path = os.path.join(outdir, "prb_distribution.png")
        plt.figure(figsize=(8, 5))
        plt.hist(
            cell_summary["avg_prb"].dropna(),
            bins=15,
            color="#4C72B0",
            edgecolor="white",
        )
        plt.axvline(
            thresholds["prb_congestion_warning"],
            color="orange",
            linestyle="--",
            label="Soglia attenzione",
        )
        plt.axvline(
            thresholds["prb_congestion_critical"],
            color="red",
            linestyle="--",
            label="Soglia critica",
        )
        plt.title("Distribuzione utilizzo medio PRB per cella")
        plt.xlabel("Utilizzo PRB medio (%)")
        plt.ylabel("Numero di celle")
        plt.legend()
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    # 2. Scatter copertura: RSRP medio vs % segnale debole
    if cell_summary[["avg_rsrp", "avg_weak_signal_pct"]].notna().all(axis=1).any():
        path = os.path.join(outdir, "coverage_scatter.png")
        plt.figure(figsize=(8, 5))
        plt.scatter(
            cell_summary["avg_rsrp"],
            cell_summary["avg_weak_signal_pct"],
            c=colors,
            s=60,
            edgecolor="k",
        )
        plt.xlabel("RSRP medio (dBm)")
        plt.ylabel("% campioni con segnale debole")
        plt.title("Qualità di copertura per cella (colore = severità)")
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    # 3. Mappa geografica semplice delle celle colorate per severità
    if cell_summary[["longitude", "latitude"]].notna().all(axis=1).any():
        path = os.path.join(outdir, "cell_map.png")
        plt.figure(figsize=(7, 7))
        plt.scatter(
            cell_summary["longitude"],
            cell_summary["latitude"],
            c=colors,
            s=120,
            edgecolor="k",
        )
        for _, r in cell_summary.iterrows():
            if pd.notna(r["longitude"]) and pd.notna(r["latitude"]):
                plt.annotate(
                    str(r["cell_id"]).replace("SITE_", "S"),
                    (r["longitude"], r["latitude"]),
                    fontsize=7,
                    xytext=(3, 3),
                    textcoords="offset points",
                )
        plt.xlabel("Longitudine")
        plt.ylabel("Latitudine")
        plt.title(
            "Mappa celle per stato di rete (verde=OK, arancio=attenzione, rosso=critico)"
        )
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)

    log.info("Grafici generati: %s", [os.path.basename(p) for p in paths])
    return paths


def make_trend_charts(
    df: pd.DataFrame,
    cell_summary: pd.DataFrame,
    outdir: str,
    thresholds: dict,
    top_n: int = 6,
) -> list[str]:
    """Trend temporale di PRB% e % segnale debole per le celle peggiori.

    Produce una figura a griglia `trend_celle.png` solo se nel dataset ci
    sono più rilevazioni temporali per cella. Restituisce i percorsi PNG
    (lista vuota se non applicabile).
    """
    if "timestamp_hour" not in df.columns or df["timestamp_hour"].nunique() < 2:
        log.info("Una sola rilevazione temporale: trend non generati.")
        return []

    ranked = cell_summary.copy()
    ranked["_rank"] = ranked["severity"].map(SEVERITY_ORDER)
    ranked = ranked.sort_values(["_rank", "avg_prb"], ascending=[True, False])
    top_cells = ranked["cell_id"].drop_duplicates().head(top_n).tolist()
    if not top_cells:
        return []

    ts = df[df["cell_id"].isin(top_cells)].sort_values("timestamp_hour")

    n = len(top_cells)
    ncols = 2 if n > 1 else 1
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(7 * ncols, 3.2 * nrows), squeeze=False
    )

    for i, cell_id in enumerate(top_cells):
        ax = axes[i // ncols][i % ncols]
        sub = ts[ts["cell_id"] == cell_id]
        sev = ranked.loc[ranked["cell_id"] == cell_id, "severity"].iloc[0]

        if sub["prb_utilization_pct"].notna().any():
            ax.plot(
                sub["timestamp_hour"],
                sub["prb_utilization_pct"],
                color="#4C72B0",
                marker="o",
                ms=3,
                label="PRB %",
            )
            ax.axhline(
                thresholds["prb_congestion_warning"],
                color="orange",
                linestyle="--",
                lw=1,
                label="Soglia attenzione",
            )
            ax.axhline(
                thresholds["prb_congestion_critical"],
                color="red",
                linestyle="--",
                lw=1,
                label="Soglia critica",
            )
        if sub["weak_signal_sample_pct"].notna().any():
            ax.plot(
                sub["timestamp_hour"],
                sub["weak_signal_sample_pct"],
                color="#8172B3",
                marker="s",
                ms=3,
                linestyle=":",
                label="Segnale debole %",
            )
        ax.set_title(f"{cell_id} — {sev}", fontsize=9)
        ax.tick_params(axis="x", labelrotation=45, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=7)

    for j in range(n, nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    fig.suptitle("Trend temporale delle celle peggiori", fontsize=12)
    fig.tight_layout()
    path = os.path.join(outdir, "trend_celle.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    log.info("Trend generato: %s", os.path.basename(path))
    return [path]
