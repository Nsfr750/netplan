"""
data_reader.py
Lettura e normalizzazione di export di KPI di rete aggregati per cella,
provenienti da sistemi OSS/PM reali (Nokia, Ericsson, Huawei, data
warehouse interni, ecc.), che spesso usano nomi di colonna diversi tra loro.

Lavora su dati aggregati per cella/settore. I file con colonne a livello
di singolo abbonato (numeri di telefono, IMSI, IMEI, MSISDN...) sono
rifiutati per default (vedi `_detect_subscriber_columns`), a meno che
non venga esplicitamente abilitata la modalità subscriber
(`allow_subscriber_data=True`) per analisi per-utente autorizzate.

Riconosce anche i nomi colonna tipici degli export OSS/PM di Nokia,
Ericsson e Huawei (vedi `detect_vendor`).
"""

import os
import pandas as pd

from logger import get_logger

log = get_logger(__name__)

# Colonne che NON devono mai comparire in un dataset aggregato per pianificazione.
# Se presenti, indicano che il file è a livello di singolo abbonato/dispositivo
# e non è un export aggregato adatto a questo strumento.
FORBIDDEN_COLUMNS = {
    "msisdn",
    "imsi",
    "imei",
    "phone_number",
    "numero_telefono",
    "subscriber_id",
    "subscriber",
    "sim_id",
    "ip_address",
    "indirizzo_ip",
}

# Colonne che identificano il singolo abbonato, in ordine di preferenza
# come chiave del report per-abbonato (analysis.subscriber_summary).
SUBSCRIBER_ID_CANDIDATES = [
    "msisdn",
    "imsi",
    "imei",
    "subscriber_id",
    "subscriber",
    "sim_id",
    "numero_telefono",
    "phone_number",
]

# Firme caratteristiche per riconoscere il vendor dell'export OSS/PM.
VENDOR_SIGNATURES = {
    "Nokia": {"nrcelldu", "lnbts", "wcel", "lnrel", "nrcellcu"},
    "Ericsson": {"eutrancellfdd", "eutrancell", "me_context", "erbs", "euancel"},
    "Huawei": {"ne_name", "cell_name", "ne_id", "object_id", "cellid"},
}

# Mapping alias -> nome colonna standard usato internamente dal resto del tool.
# Include anche i nomi tipici degli export OSS/PM (Nokia, Ericsson, Huawei).
# Aggiungi qui gli alias usati dai tuoi export reali.
COLUMN_ALIASES = {
    "site_id": [
        "site_id",
        "site",
        "bts_id",
        "node_id",
        "sito",
        "id_sito",
        # vendor OSS/PM
        "me_name",  # Nokia/Huawei: Managed Element
        "me_context",  # Ericsson: managed element context
        "ne_name",  # Huawei: Network Element
        "node_name",
        "enb_id",
        "gnb_id",
        "bts_name",
    ],
    "cell_id": [
        "cell_id",
        "cell",
        "cella",
        "id_cella",
        "sector_id",
        # vendor OSS/PM
        "cell_name",  # Huawei
        "cellname",
        "nrcelldu",  # Nokia: NRCellDU
        "nrcellid",
        "eutrancellfdd",  # Ericsson: EUtranCellFDD
        "eutrancell",
        "eci",
        "cgi",
        "sector_name",
    ],
    "technology": [
        "technology",
        "tech",
        "rat",
        "tecnologia",
        "rat_type",
        "radio_access_technology",
    ],
    "band": ["band", "frequency_band", "banda", "band_mhz", "freq_band"],
    "timestamp_hour": [
        "timestamp_hour",
        "timestamp",
        "datetime",
        "data_ora",
        "period_start_time",
        # vendor OSS/PM
        "begin_time",  # Ericsson/Huawei PM counters
        "end_time",
        "start_time",
        "collection_time",
        "period",
    ],
    "latitude": ["latitude", "lat", "latitudine"],
    "longitude": ["longitude", "lon", "lng", "longitudine"],
    "azimuth_deg": ["azimuth_deg", "azimuth", "azimut"],
    "prb_utilization_pct": [
        "prb_utilization_pct",
        "prb_util",
        "prb_utilization",
        "rrc_util_pct",
        "resource_block_utilization",
        # vendor OSS/PM
        "dl_prb_usage_rate",
        "prb_dl_util",
        "dl_prb_utilization",
        "prb_usage",
        "pmprbuseddl",
    ],
    "traffic_erlang": [
        "traffic_erlang",
        "erlang",
        "voice_traffic_erl",
        "traffic_volume_erl",
        "erl",
    ],
    "data_volume_gb": [
        "data_volume_gb",
        "data_volume",
        "throughput_gb",
        "volume_dati_gb",
        "dl_data_volume_gb",
        "pdcpsduvolumedl",
    ],
    "connected_users_avg": [
        "connected_users_avg",
        "avg_connected_users",
        "rrc_connected_users_avg",
        "utenze_medie",
        "rrcconnuser",
        "average_user_number",
        "rrc_connected_users",
    ],
    "call_drop_rate_pct": [
        "call_drop_rate_pct",
        "drop_rate",
        "cdr_pct",
        "call_drop_rate",
        "call_drop_ratio",
        "dcr",
    ],
    "handover_success_rate_pct": [
        "handover_success_rate_pct",
        "ho_success_rate",
        "handover_success",
        "ho_sr",
        "hosr",
        "intra_freq_ho_sr",
    ],
    "avg_rsrp_dbm": [
        "avg_rsrp_dbm",
        "rsrp_avg",
        "avg_rsrp",
        "rsrp",
        "mr_rsrp_avg",
        "rsrp_mean",
    ],
    "weak_signal_sample_pct": [
        "weak_signal_sample_pct",
        "weak_signal_pct",
        "poor_coverage_pct",
    ],
}

REQUIRED_FOR_CONGESTION = [
    "site_id",
    "cell_id",
    "prb_utilization_pct",
]

# Colonne percentuali: i valori devono restare in [0, 100].
PERCENT_COLUMNS = [
    "prb_utilization_pct",
    "call_drop_rate_pct",
    "handover_success_rate_pct",
    "weak_signal_sample_pct",
]

# Intervallo plausibile per l'RSRP medio aggregato (dBm).
RSRP_RANGE = (-140.0, -40.0)

class DataValidationError(Exception):
    pass

def _detect_subscriber_columns(df: pd.DataFrame) -> set:
    """Colonne a livello di singolo abbonato presenti nel file."""
    return FORBIDDEN_COLUMNS.intersection({c.lower().strip() for c in df.columns})


def subscriber_id_column(df: pd.DataFrame) -> str | None:
    """Colonna identificativa dell'abbonato, se presente nel DataFrame."""
    for col in SUBSCRIBER_ID_CANDIDATES:
        if col in df.columns:
            return col
    return None


def detect_vendor(df: pd.DataFrame) -> str | None:
    """Riconosce il vendor OSS/PM dai nomi colonna caratteristici.

    Confronta le colonne normalizzate con le firme in VENDOR_SIGNATURES;
    restituisce il vendor con più corrispondenze oppure None.
    """
    cols = {c.lower().strip().replace(" ", "_") for c in df.columns}
    scores = {vendor: len(cols & sigs) for vendor, sigs in VENDOR_SIGNATURES.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None
    return best


def _normalize_columns(df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    """Porta i nomi colonna a minuscolo_snake_case e applica gli alias noti.

    Segnala come ambiguo il caso in cui due colonne diverse del file
    puntino allo stesso nome standard (es. 'cell' e 'cell_id' insieme):
    in quel caso prevale il nome standard già presente / il primo alias
    in ordine di elenco.
    """
    lower_map = {c: c.lower().strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=lower_map)

    rename_final = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        found = [a for a in aliases if a in df.columns]
        if len(found) > 1:
            warnings.append(
                f"Colonna ambigua '{standard_name}': trovati più alias "
                f"{found}. Verrà usato '{found[0]}', gli altri restano invariati."
            )
        for alias in found:
            if standard_name not in df.columns and alias != standard_name:
                rename_final[alias] = standard_name
            break
    df = df.rename(columns=rename_final)
    return df


def _warn_or_raise(warnings: list[str], strict: bool):
    """Accumula gli avvisi di validazione: loggati sempre, errore in strict."""
    for w in warnings:
        log.warning(w)
    if strict and warnings:
        raise DataValidationError(
            "Validazione fallita in modalità strict:\n- " + "\n- ".join(warnings)
        )


def _validate_values(df: pd.DataFrame, source: str) -> list[str]:
    """Controlli di coerenza sui valori: range percentuali, RSRP, righe vuote/duplicate."""
    warnings = []

    if df.empty:
        raise DataValidationError(f"Il file '{source}' non contiene righe di dati.")

    for col in PERCENT_COLUMNS:
        if col in df.columns:
            out_of_range = df[col].dropna()
            out_of_range = out_of_range[(out_of_range < 0) | (out_of_range > 100)]
            if not out_of_range.empty:
                warnings.append(
                    f"'{col}': {len(out_of_range)} righe fuori dal range 0-100 "
                    f"(min={df[col].min()}, max={df[col].max()})."
                )

    if "avg_rsrp_dbm" in df.columns:
        rsrp = df["avg_rsrp_dbm"].dropna()
        bad = rsrp[(rsrp < RSRP_RANGE[0]) | (rsrp > RSRP_RANGE[1])]
        if not bad.empty:
            warnings.append(
                f"'avg_rsrp_dbm': {len(bad)} valori fuori dal range plausibile "
                f"{RSRP_RANGE[0]}..{RSRP_RANGE[1]} dBm."
            )

    if "prb_utilization_pct" in df.columns:
        nan_pct = df["prb_utilization_pct"].isna().mean() * 100
        if nan_pct > 0:
            warnings.append(
                f"'prb_utilization_pct': {nan_pct:.0f}% di valori mancanti/non numerici."
            )

    key_cols = [c for c in ("site_id", "cell_id", "timestamp_hour") if c in df.columns]
    if len(key_cols) >= 2:
        n_dup = df.duplicated(subset=key_cols).sum()
        if n_dup:
            warnings.append(
                f"{n_dup} righe duplicate sulla chiave {key_cols}: "
                f"verifica che l'export non contenga sovrapposizioni."
            )

    return warnings


def read_cell_data(
    path: str,
    require_congestion_fields: bool = True,
    strict: bool = False,
    allow_subscriber_data: bool = False,
) -> pd.DataFrame:
    """
    Legge un export di KPI celle (.csv, .xlsx, .xls), normalizza i nomi
    colonna sugli alias noti e valida struttura e valori.

    Args:
        path: percorso del file da leggere.
        require_congestion_fields: se True, richiede site_id, cell_id e
            prb_utilization_pct.
        strict: se True, gli avvisi di validazione (valori fuori range,
            duplicati, alias ambigui...) diventano errori.
        allow_subscriber_data: se True, accetta anche file con colonne a
            livello di singolo abbonato (MSISDN, IMSI...); da usare solo
            per analisi autorizzate su dati di propria competenza.

    Returns:
        DataFrame normalizzato con i nomi colonna standard.

    Raises:
        FileNotFoundError: file inesistente.
        DataValidationError: formato non supportato, dati a livello
            abbonato (senza allow_subscriber_data), colonne obbligatorie
            mancanti o (in strict) avvisi.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File non trovato: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise DataValidationError(
            f"Formato file non supportato: '{ext}'. Usa .csv, .xlsx o .xls."
        )

    subscriber_cols = _detect_subscriber_columns(df)
    if subscriber_cols and not allow_subscriber_data:
        raise DataValidationError(
            f"Il file '{path}' contiene colonne a livello di singolo abbonato/dispositivo "
            f"({', '.join(sorted(subscriber_cols))}). Per default questo strumento accetta "
            f"solo KPI aggregati per cella: rimuovi queste colonne, fornisci un export "
            f"aggregato dal sistema OSS/PM, oppure riprova con --subscriber se sei "
            f"autorizzato a trattare dati a livello utente."
        )
    if subscriber_cols:
        log.warning(
            "Modalità subscriber attiva: il file '%s' contiene dati a livello "
            "di singolo abbonato (%s). Usare solo per analisi autorizzate.",
            path,
            ", ".join(sorted(subscriber_cols)),
        )
        # gli identificativi restano stringa (MSISDN con zeri iniziali ecc.)
        for col in df.columns:
            if col.lower().strip() in FORBIDDEN_COLUMNS:
                df[col] = df[col].astype(str)

    vendor = detect_vendor(df)
    if vendor:
        log.info("Formato export riconosciuto: %s", vendor)

    warnings: list[str] = []
    df = _normalize_columns(df, warnings)

    if require_congestion_fields:
        missing = [c for c in REQUIRED_FOR_CONGESTION if c not in df.columns]
        if missing:
            dettaglio = "; ".join(
                f"'{c}' (alias accettati: {', '.join(COLUMN_ALIASES.get(c, [c]))})"
                for c in missing
            )
            raise DataValidationError(
                f"Colonne mancanti per l'analisi di congestione: {missing}.\n"
                f"Dettaglio: {dettaglio}\n"
                f"Colonne trovate nel file: {list(df.columns)}.\n"
                f"Aggiorna COLUMN_ALIASES in data_reader.py se il tuo export usa nomi diversi."
            )

    if "timestamp_hour" in df.columns:
        df["timestamp_hour"] = pd.to_datetime(df["timestamp_hour"], errors="coerce")
        n_bad_ts = int(df["timestamp_hour"].isna().sum())
        if n_bad_ts:
            warnings.append(
                f"'timestamp_hour': {n_bad_ts} timestamp non riconosciuti (impostati a vuoto)."
            )

    numeric_cols = [
        "prb_utilization_pct",
        "traffic_erlang",
        "data_volume_gb",
        "connected_users_avg",
        "call_drop_rate_pct",
        "handover_success_rate_pct",
        "avg_rsrp_dbm",
        "weak_signal_sample_pct",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    warnings.extend(_validate_values(df, path))
    _warn_or_raise(warnings, strict)

    log.info("Letto '%s': %d righe, %d colonne.", path, len(df), len(df.columns))
    return df


def describe_dataset(df: pd.DataFrame) -> str:
    """Riepilogo rapido di cosa è stato letto, utile per un controllo manuale prima dell'analisi."""
    lines = [
        f"Righe totali: {len(df)}",
        f"Celle uniche: {df['cell_id'].nunique() if 'cell_id' in df.columns else 'n/d'}",
        f"Siti unici: {df['site_id'].nunique() if 'site_id' in df.columns else 'n/d'}",
    ]
    if "technology" in df.columns:
        tech = ", ".join(sorted(df["technology"].dropna().astype(str).unique()))
        lines.append(f"Tecnologie presenti: {tech}")
    if "band" in df.columns:
        bande = ", ".join(sorted(df["band"].dropna().astype(str).unique()))
        lines.append(f"Bande presenti: {bande}")
    sub_col = subscriber_id_column(df)
    if sub_col:
        lines.append(
            f"Dati a livello abbonato: colonna '{sub_col}' "
            f"({df[sub_col].nunique()} abbonati unici)"
        )
    vendor = detect_vendor(df)
    if vendor:
        lines.append(f"Vendor export rilevato: {vendor}")
    if "timestamp_hour" in df.columns and df["timestamp_hour"].notna().any():
        lines.append(
            f"Intervallo temporale: {df['timestamp_hour'].min()} -> {df['timestamp_hour'].max()}"
        )
    lines.append(f"Colonne disponibili: {', '.join(df.columns)}")
    return "\n".join(lines)
