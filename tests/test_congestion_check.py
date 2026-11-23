"""Test per congestion_check: snapshot, livelli e ordinamento."""

import pandas as pd

from congestion_check import check_congestion, congestion_level, latest_snapshot


def test_congestion_level_boundaries():
    assert congestion_level(50.0) == "OK"
    assert congestion_level(70.0) == "ATTENZIONE"
    assert congestion_level(85.0) == "CRITICO"
    assert congestion_level(float("nan")) == "N/D"


def test_congestion_level_custom_thresholds():
    th = {"prb_congestion_warning": 40.0, "prb_congestion_critical": 60.0}
    assert congestion_level(50.0, thresholds=th) == "ATTENZIONE"
    assert congestion_level(65.0, thresholds=th) == "CRITICO"


def test_latest_snapshot_takes_last_timestamp():
    df = pd.DataFrame(
        {
            "cell_id": ["C1", "C1", "C2"],
            "timestamp_hour": pd.to_datetime(
                ["2026-01-01 10:00", "2026-01-01 11:00", "2026-01-01 10:00"]
            ),
            "prb_utilization_pct": [10.0, 20.0, 30.0],
        }
    )
    snap = latest_snapshot(df)
    assert len(snap) == 2
    assert snap.loc[snap["cell_id"] == "C1", "prb_utilization_pct"].iloc[0] == 20.0


def test_latest_snapshot_without_timestamps():
    df = pd.DataFrame({"cell_id": ["C1"], "prb_utilization_pct": [10.0]})
    assert len(latest_snapshot(df)) == 1


def test_check_congestion_sorted_by_severity():
    df = pd.DataFrame(
        {
            "site_id": ["S1"] * 3,
            "cell_id": ["C1", "C2", "C3"],
            "prb_utilization_pct": [10.0, 90.0, 75.0],
        }
    )
    res = check_congestion(df)
    assert res["congestion_level"].tolist() == ["CRITICO", "ATTENZIONE", "OK"]
