"""
analysis.py
Motore di analisi per la pianificazione della copertura radio.

Lavora esclusivamente su KPI aggregati per cella (traffico, utilizzo PRB,
drop rate, handover, statistiche di potenza del segnale). Non effettua
alcuna operazione su identificativi di singoli utenti/dispositivi.
"""

import json
import os

import numpy as np
import pandas as pd

from logger import get_logger

log = get_logger(__name__)

# Soglie di riferimento (valori tipici, regolabili secondo le policy dell'operatore)
THRESHOLDS = {
    "prb_congestion_warning": 70.0,  # % utilizzo PRB oltre cui si considera "a rischio"
    "prb_congestion_critical": 85.0,
    "drop_rate_warning": 2.0,  # % drop call oltre cui si considera anomalo
    "drop_rate_critical": 4.0,
    "ho_success_warning": 95.0,  # % handover sotto cui si considera anomalo
    "weak_signal_warning": 15.0,  # % campioni con segnale debole oltre cui si segnala buco di copertura
    "weak_signal_critical": 30.0,
}

SEVERITY_ORDER = {"CRITICO": 0, "ATTENZIONE": 1, "OK": 2}
SEVERITY_COLORS = {"OK": "#55A868", "ATTENZIONE": "#DD8452", "CRITICO": "#C44E52"}


def load_thresholds(path: str) -> dict:
    """Carica soglie personalizzate da file e le fonde sui valori di default.

    Formati accettati:
      - JSON: {"prb_congestion_critical": 90, ...}
      - testo chiave=valore, una soglia per riga (commenti con '#')

    Le chiavi sconosciute vengono ignorate con un avviso; i valori devono
    essere numerici. Restituisce un dizionario completo di tutte le soglie.
    """
    overrides = {}
    ext = os.path.splitext(path)[1].lower()
    with open(path, encoding="utf-8") as f:
        if ext == ".json":
            overrides = json.load(f)
        else:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, sep, value = line.partition("=")
                if not sep:
                    key, sep, value = line.partition(":")
                if sep:
                    overrides[key.strip()] = value.strip()

    if not isinstance(overrides, dict):
        raise ValueError(f"File soglie non valido: {path}")

    thresholds = dict(THRESHOLDS)
    for key, value in overrides.items():
        if key not in THRESHOLDS:
            log.warning("Soglia sconosciuta ignorata: '%s'", key)
            continue
        try:
            thresholds[key] = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Valore non numerico per la soglia '{key}': {value!r}")

    log.info(
        "Soglie caricate da '%s': %s",
        path,
        {k: v for k, v in thresholds.items() if k in overrides},
    )
    return thresholds


def load_kpis(csv_path: str) -> pd.DataFrame:
    """Legge i KPI da file, passando per la validazione di data_reader."""
    from data_reader import read_cell_data

    return read_cell_data(csv_path)


def _group_keys(df: pd.DataFrame) -> list[str]:
    """Chiavi di aggregazione presenti nel dataset (supporto multi-tech/banda)."""
    keys = ["site_id", "cell_id"]
    for optional in ("technology", "band"):
        if optional in df.columns:
            keys.append(optional)
    return keys


def per_cell_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggrega nel tempo, producendo una riga per cella con medie/picchi.

    Se il file contiene più tecnologie o bande per cella, ognuna produce
    una riga separata (raggruppamento per technology/band quando presenti).
    Le metriche assenti dal file vengono riportate come NaN.
    """
    metric_aggs = {
        "latitude": ("latitude", "mean"),
        "longitude": ("longitude", "mean"),
        "azimuth_deg": ("azimuth_deg", "first"),
        "avg_prb": ("prb_utilization_pct", "mean"),
        "peak_prb": ("prb_utilization_pct", "max"),
        "avg_drop_rate": ("call_drop_rate_pct", "mean"),
        "peak_drop_rate": ("call_drop_rate_pct", "max"),
        "avg_ho_success": ("handover_success_rate_pct", "mean"),
        "avg_rsrp": ("avg_rsrp_dbm", "mean"),
        "avg_weak_signal_pct": ("weak_signal_sample_pct", "mean"),
        "avg_connected_users": ("connected_users_avg", "mean"),
        "avg_data_volume_gb": ("data_volume_gb", "mean"),
    }
    available = {k: v for k, v in metric_aggs.items() if v[0] in df.columns}
    agg = df.groupby(_group_keys(df)).agg(**available).reset_index()
    for col in metric_aggs:
        if col not in agg.columns:
            agg[col] = np.nan
    agg["n_rilevazioni"] = df.groupby(_group_keys(df)).size().values
    return agg


def _val(row, key):
    """Valore di riga o NaN se la colonna non esiste nel dataset."""
    try:
        return row[key]
    except KeyError:
        return np.nan


def classify_cell(row, thresholds: dict | None = None) -> dict:
    """Assegna etichette di stato alla cella in base alle soglie definite.

    Le metriche assenti (NaN) non producono anomalie: la classificazione
    si basa solo sui dati effettivamente presenti nell'export.
    """
    th = thresholds or THRESHOLDS
    issues = []
    severity = "OK"

    peak_prb, avg_prb = _val(row, "peak_prb"), _val(row, "avg_prb")
    if pd.notna(peak_prb) and peak_prb >= th["prb_congestion_critical"]:
        issues.append("Congestione critica (PRB)")
        severity = "CRITICO"
    elif pd.notna(avg_prb) and avg_prb >= th["prb_congestion_warning"]:
        issues.append("Congestione in avvicinamento (PRB)")
        severity = max(severity, "ATTENZIONE", key=_sev_rank)

    peak_drop, avg_drop = _val(row, "peak_drop_rate"), _val(row, "avg_drop_rate")
    if pd.notna(peak_drop) and peak_drop >= th["drop_rate_critical"]:
        issues.append("Drop rate critico")
        severity = "CRITICO"
    elif pd.notna(avg_drop) and avg_drop >= th["drop_rate_warning"]:
        issues.append("Drop rate elevato")
        severity = max(severity, "ATTENZIONE", key=_sev_rank)

    ho = _val(row, "avg_ho_success")
    if pd.notna(ho) and ho < th["ho_success_warning"]:
        issues.append("Tasso di handover sotto soglia")
        severity = max(severity, "ATTENZIONE", key=_sev_rank)

    weak = _val(row, "avg_weak_signal_pct")
    if pd.notna(weak) and weak >= th["weak_signal_critical"]:
        issues.append("Probabile buco di copertura")
        severity = "CRITICO"
    elif pd.notna(weak) and weak >= th["weak_signal_warning"]:
        issues.append("Copertura debole")
        severity = max(severity, "ATTENZIONE", key=_sev_rank)

    if not issues:
        issues.append("Nessuna anomalia rilevata")

    return {"severity": severity, "issues": "; ".join(issues)}


def _sev_rank(s):
    return {"OK": 0, "ATTENZIONE": 1, "CRITICO": 2}.get(s, 0)


def recommend_action(row) -> str:
    """Raccomandazione sintetica di pianificazione per la cella."""
    recs = []
    if row["severity"] == "CRITICO" and "Congestione" in row["issues"]:
        recs.append(
            "Valutare espansione capacità (nuova portante / small cell / carrier aggregation)"
        )
    if (
        "buco di copertura" in row["issues"].lower()
        or "copertura debole" in row["issues"].lower()
    ):
        recs.append(
            "Verificare tilt antenna, potenza TX, o necessità di nuovo sito/ripetitore nell'area"
        )
    if "handover" in row["issues"].lower():
        recs.append("Rivedere parametri di vicinanza/handover con celle adiacenti")
    if "drop rate" in row["issues"].lower():
        recs.append("Indagare interferenze o problemi hardware sul settore")
    if not recs:
        recs.append("Monitoraggio ordinario")
    return " | ".join(recs)


def build_report(data, thresholds: dict | None = None) -> pd.DataFrame:
    """Costruisce il report di classificazione per cella.

    Args:
        data: DataFrame KPI già normalizzato, oppure percorso a un file
            CSV/Excel da leggere tramite data_reader.read_cell_data.
        thresholds: dizionario soglie personalizzato (vedi load_thresholds).
    """
    df = load_kpis(data) if isinstance(data, (str, os.PathLike)) else data
    summary = per_cell_summary(df)

    classifications = summary.apply(
        classify_cell, axis=1, result_type="expand", thresholds=thresholds
    )
    summary = pd.concat([summary, classifications], axis=1)
    summary["recommendation"] = summary.apply(recommend_action, axis=1)

    # Ordina mettendo prima le celle più critiche
    summary["_sev_rank"] = summary["severity"].map(SEVERITY_ORDER)
    summary = summary.sort_values(
        ["_sev_rank", "avg_prb"], ascending=[True, False]
    ).drop(columns="_sev_rank")

    log.info(
        "Report per cella: %d righe (%d critiche, %d attenzione).",
        len(summary),
        (summary["severity"] == "CRITICO").sum(),
        (summary["severity"] == "ATTENZIONE").sum(),
    )
    return summary


def site_level_summary(cell_summary: pd.DataFrame) -> pd.DataFrame:
    """Vista aggregata per sito (utile per decidere su nuovi siti vs upgrade settore)."""
    aggs = {
        "n_celle": ("cell_id", "count"),
        "n_celle_critiche": ("severity", lambda s: (s == "CRITICO").sum()),
        "avg_prb_sito": ("avg_prb", "mean"),
        "avg_weak_signal_sito": ("avg_weak_signal_pct", "mean"),
        "latitude": ("latitude", "mean"),
        "longitude": ("longitude", "mean"),
    }
    if "technology" in cell_summary.columns:
        aggs["tecnologie"] = (
            "technology",
            lambda s: ", ".join(sorted(s.dropna().astype(str).unique())),
        )
    if "band" in cell_summary.columns:
        aggs["bande"] = (
            "band",
            lambda s: ", ".join(sorted(s.dropna().astype(str).unique())),
        )
    site = cell_summary.groupby("site_id").agg(**aggs).reset_index()
    return site


# Mappatura nome tecnologia -> generazione di rete (2G/3G/4G/5G).
TECH_GENERATION = {
    "GSM": "2G",
    "GPRS": "2G",
    "EDGE": "2G",
    "UMTS": "3G",
    "WCDMA": "3G",
    "HSPA": "3G",
    "HSPA+": "3G",
    "TD-SCDMA": "3G",
    "LTE": "4G",
    "LTE-A": "4G",
    "LTE FDD": "4G",
    "LTE TDD": "4G",
    "NR": "5G",
    "NR-NSA": "5G",
    "NR-SA": "5G",
    "5G": "5G",
    "5G NSA": "5G",
    "5G SA": "5G",
}

def tech_generation(technology) -> str:
    """Generazione di rete (2G/3G/4G/5G) corrispondente al nome tecnologia.

    Cerca il nome per intero in TECH_GENERATION (case-insensitive) e poi
    come prefisso; restituisce 'ALTRO' se non riconosciuta.
    """
    if pd.isna(technology):
        return "N/D"
    name = str(technology).strip().upper()
    if name in TECH_GENERATION:
        return TECH_GENERATION[name]
    for tech, gen in TECH_GENERATION.items():
        if name.startswith(tech):
            return gen
    return "ALTRO"


def technology_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Riepilogo per tecnologia/generazione di rete (2G/3G/4G/5G).

    Aggrega le righe del dataset per `technology`: celle servite, PRB
    medio/picco, utenze connesse, volume dati e qualità. Aggiunge la
    colonna `generation` mappata via tech_generation.
    """
    if "technology" not in df.columns:
        return pd.DataFrame()

    aggs = {}
    if "cell_id" in df.columns:
        aggs["n_celle"] = ("cell_id", "nunique")
    if "prb_utilization_pct" in df.columns:
        aggs["avg_prb"] = ("prb_utilization_pct", "mean")
        aggs["peak_prb"] = ("prb_utilization_pct", "max")
    if "connected_users_avg" in df.columns:
        aggs["avg_utenze"] = ("connected_users_avg", "mean")
    if "data_volume_gb" in df.columns:
        aggs["tot_volume_gb"] = ("data_volume_gb", "sum")
    if "call_drop_rate_pct" in df.columns:
        aggs["avg_drop_rate"] = ("call_drop_rate_pct", "mean")
    if "handover_success_rate_pct" in df.columns:
        aggs["avg_ho_success"] = ("handover_success_rate_pct", "mean")
    if not aggs:
        return pd.DataFrame()

    tech = df.groupby("technology").agg(**aggs).reset_index()
    tech.insert(1, "generation", tech["technology"].map(tech_generation))
    order = {"2G": 0, "3G": 1, "4G": 2, "5G": 3}
    tech["_o"] = tech["generation"].map(lambda g: order.get(g, 9))
    return tech.sort_values("_o").drop(columns="_o").reset_index(drop=True)


def subscriber_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Riepilogo per singolo abbonato (modalità subscriber).

    Aggrega le misure per identificativo abbonato (MSISDN/IMSI/...):
    celle utilizzate, tecnologia/generazione prevalente, volumi e
    qualità media. Restituisce DataFrame vuoto se non c'è una colonna
    identificativa.
    """
    from data_reader import subscriber_id_column

    id_col = subscriber_id_column(df)
    if id_col is None:
        return pd.DataFrame()

    aggs = {"n_rilevazioni": (id_col, "size")}
    if "cell_id" in df.columns:
        aggs["n_celle_usate"] = ("cell_id", "nunique")
        aggs["celle"] = (
            "cell_id",
            lambda s: ", ".join(sorted(s.astype(str).unique())[:5]),
        )
    if "technology" in df.columns:
        aggs["tecnologia_principale"] = (
            "technology",
            lambda s: s.mode().iloc[0] if not s.mode().empty else None,
        )
    if "prb_utilization_pct" in df.columns:
        aggs["avg_prb"] = ("prb_utilization_pct", "mean")
    if "data_volume_gb" in df.columns:
        aggs["tot_volume_gb"] = ("data_volume_gb", "sum")
    if "call_drop_rate_pct" in df.columns:
        aggs["avg_drop_rate"] = ("call_drop_rate_pct", "mean")
    if "avg_rsrp_dbm" in df.columns:
        aggs["avg_rsrp"] = ("avg_rsrp_dbm", "mean")
    if "weak_signal_sample_pct" in df.columns:
        aggs["avg_weak_signal_pct"] = ("weak_signal_sample_pct", "mean")

    summary = df.groupby(id_col).agg(**aggs).reset_index()
    if "tecnologia_principale" in summary.columns:
        summary["generazione"] = summary["tecnologia_principale"].map(tech_generation)
    sort_col = (
        "tot_volume_gb" if "tot_volume_gb" in summary.columns else "n_rilevazioni"
    )
    return summary.sort_values(sort_col, ascending=False).reset_index(drop=True)
