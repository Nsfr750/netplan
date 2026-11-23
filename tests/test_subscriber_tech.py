"""Test per modalità subscriber, generazioni RAT e riconoscimento vendor."""

import pandas as pd
import pytest

from analysis import (
    subscriber_summary,
    tech_generation,
    technology_summary,
)
from data_reader import DataValidationError, detect_vendor, read_cell_data
from pipeline import run_analysis


def _subscriber_csv(tmp_path, extra_cols=None):
    """CSV con una colonna msisdn e KPI per cella."""
    cols = {
        "site_id": ["S1"] * 6,
        "cell_id": ["C1", "C1", "C2", "C2", "C1", "C3"],
        "technology": ["LTE", "LTE", "NR", "NR", "LTE", "UMTS"],
        "msisdn": ["390001", "390001", "390002", "390002", "390003", "390003"],
        "prb_utilization_pct": [50.0, 55.0, 60.0, 65.0, 70.0, 30.0],
        "data_volume_gb": [1.0, 1.5, 2.0, 2.5, 3.0, 0.5],
        "call_drop_rate_pct": [0.5, 0.6, 0.4, 0.3, 1.0, 0.2],
    }
    df = pd.DataFrame(cols)
    path = tmp_path / "subscriber.csv"
    df.to_csv(path, index=False)
    return str(path)


def test_subscriber_rejected_by_default(tmp_path):
    path = _subscriber_csv(tmp_path)
    with pytest.raises(DataValidationError, match="abbonato"):
        read_cell_data(path)


def test_subscriber_accepted_with_flag(tmp_path):
    path = _subscriber_csv(tmp_path)
    df = read_cell_data(path, allow_subscriber_data=True)
    assert "msisdn" in df.columns
    assert len(df) == 6


def test_subscriber_summary(tmp_path):
    df = read_cell_data(_subscriber_csv(tmp_path), allow_subscriber_data=True)
    sub = subscriber_summary(df)
    assert len(sub) == 3
    assert set(sub["msisdn"]) == {"390001", "390002", "390003"}
    row = sub[sub["msisdn"] == "390003"].iloc[0]
    assert row["n_celle_usate"] == 2  # C1 (LTE) e C3 (UMTS)
    assert "generazione" in sub.columns


def test_subscriber_summary_empty_without_ids(sample_df):
    assert subscriber_summary(sample_df).empty


def test_tech_generation_mapping():
    assert tech_generation("LTE") == "4G"
    assert tech_generation("NR") == "5G"
    assert tech_generation("nr-sa") == "5G"
    assert tech_generation("UMTS") == "3G"
    assert tech_generation("GSM") == "2G"
    assert tech_generation("LTE-Advanced Pro") == "4G"
    assert tech_generation("Sconosciuta") == "ALTRO"
    assert tech_generation(None) == "N/D"


def test_technology_summary(sample_df):
    tech = technology_summary(sample_df)
    assert not tech.empty
    assert {"technology", "generation", "n_celle"} <= set(tech.columns)
    assert set(tech["generation"]) <= {"4G", "5G"}  # il sample ha LTE e NR


def test_detect_vendor():
    nokia = pd.DataFrame(columns=["nrcelldu", "lnbts", "cell_name"])
    assert detect_vendor(nokia) == "Nokia"
    ericsson = pd.DataFrame(columns=["eutrancellfdd", "me_context"])
    assert detect_vendor(ericsson) == "Ericsson"
    huawei = pd.DataFrame(columns=["ne_name", "ne_id", "object_id"])
    assert detect_vendor(huawei) == "Huawei"
    assert detect_vendor(pd.DataFrame(columns=["site_id", "cell_id"])) is None


def test_vendor_aliases_normalized(tmp_path):
    """Le colonne tipiche Nokia/Ericsson vengono mappate ai nomi standard."""
    df = pd.DataFrame(
        {
            "me_name": ["S1", "S1"],
            "nrcelldu": ["C1", "C2"],
            "dl_prb_usage_rate": [40.0, 50.0],
        }
    )
    path = tmp_path / "nokia.csv"
    df.to_csv(path, index=False)
    out = read_cell_data(str(path))
    assert {"site_id", "cell_id", "prb_utilization_pct"} <= set(out.columns)


def test_pipeline_subscriber_outputs(tmp_path):
    path = _subscriber_csv(tmp_path)
    result = run_analysis(path, str(tmp_path / "out"), allow_subscriber_data=True)
    assert result["subscriber_summary"] is not None
    assert not result["subscriber_summary"].empty
    assert result["csv_subscriber"] and result["csv_subscriber"].endswith(".csv")
    assert result["csv_tech"]
