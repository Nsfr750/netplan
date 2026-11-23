"""Test per analysis: classificazione, report e soglie configurabili."""

import json

import pandas as pd
import pytest

from analysis import (
    THRESHOLDS,
    build_report,
    classify_cell,
    load_thresholds,
    per_cell_summary,
    site_level_summary,
)


def _row(**kwargs):
    defaults = dict(
        peak_prb=50.0,
        avg_prb=40.0,
        peak_drop_rate=0.5,
        avg_drop_rate=0.3,
        avg_ho_success=99.0,
        avg_weak_signal_pct=5.0,
    )
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_classify_ok():
    res = classify_cell(_row())
    assert res["severity"] == "OK"
    assert "Nessuna anomalia" in res["issues"]


def test_classify_critical_congestion():
    res = classify_cell(_row(peak_prb=90.0))
    assert res["severity"] == "CRITICO"
    assert "Congestione critica" in res["issues"]


def test_classify_warning_congestion():
    res = classify_cell(_row(avg_prb=75.0, peak_prb=75.0))
    assert res["severity"] == "ATTENZIONE"


def test_classify_coverage_hole():
    res = classify_cell(_row(avg_weak_signal_pct=35.0))
    assert res["severity"] == "CRITICO"
    assert "buco di copertura" in res["issues"]


def test_classify_handover_warning():
    res = classify_cell(_row(avg_ho_success=90.0))
    assert res["severity"] == "ATTENZIONE"
    assert "handover" in res["issues"].lower()


def test_classify_missing_metrics_is_ok():
    res = classify_cell(pd.Series({"peak_prb": float("nan")}))
    assert res["severity"] == "OK"


def test_classify_custom_thresholds():
    th = dict(THRESHOLDS, prb_congestion_critical=60.0)
    res = classify_cell(_row(peak_prb=65.0), thresholds=th)
    assert res["severity"] == "CRITICO"


def test_per_cell_summary_grouping(sample_df):
    agg = per_cell_summary(sample_df)
    assert "avg_prb" in agg.columns
    assert "peak_prb" in agg.columns
    assert "band" in agg.columns  # il sample include la banda
    assert agg["n_rilevazioni"].max() == 24
    assert len(agg) == sample_df["cell_id"].nunique()


def test_build_report_orders_critical_first(sample_df):
    report = build_report(sample_df)
    sev = report["severity"].tolist()
    ranks = {"CRITICO": 0, "ATTENZIONE": 1, "OK": 2}
    assert [ranks[s] for s in sev] == sorted(ranks[s] for s in sev)
    assert "recommendation" in report.columns


def test_build_report_from_path(sample_csv):
    report = build_report(sample_csv)
    assert not report.empty


def test_site_level_summary(sample_df):
    report = build_report(sample_df)
    site = site_level_summary(report)
    assert "n_celle" in site.columns
    assert "n_celle_critiche" in site.columns
    assert "tecnologie" in site.columns
    assert site["n_celle"].sum() == len(report)


def test_load_thresholds_json(tmp_path):
    path = tmp_path / "soglie.json"
    path.write_text(json.dumps({"prb_congestion_critical": 90}), encoding="utf-8")
    th = load_thresholds(str(path))
    assert th["prb_congestion_critical"] == 90.0
    assert th["prb_congestion_warning"] == THRESHOLDS["prb_congestion_warning"]


def test_load_thresholds_keyvalue(tmp_path):
    path = tmp_path / "soglie.txt"
    path.write_text("# commento\nprb_congestion_warning = 65\n", encoding="utf-8")
    th = load_thresholds(str(path))
    assert th["prb_congestion_warning"] == 65.0


def test_load_thresholds_invalid_value(tmp_path):
    path = tmp_path / "soglie.txt"
    path.write_text("prb_congestion_warning = abc\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_thresholds(str(path))
