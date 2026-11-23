"""Test per data_reader: lettura, alias, validazione e rifiuto dati abbonato."""

import pandas as pd
import pytest

from data_reader import (
    DataValidationError,
    describe_dataset,
    read_cell_data,
)


def _write_csv(tmp_path, rows, header):
    path = tmp_path / "in.csv"
    df = pd.DataFrame(rows, columns=header)
    df.to_csv(path, index=False)
    return str(path)


def test_read_sample_csv(sample_df):
    assert not sample_df.empty
    for col in ("site_id", "cell_id", "prb_utilization_pct"):
        assert col in sample_df.columns
    assert pd.api.types.is_numeric_dtype(sample_df["prb_utilization_pct"])
    assert pd.api.types.is_datetime64_any_dtype(sample_df["timestamp_hour"])


def test_column_aliases_are_normalized(tmp_path):
    path = _write_csv(
        tmp_path,
        rows=[["S1", "C1", 50.0], ["S1", "C1", 60.0]],
        header=["sito", "cella", "prb_util"],
    )
    df = read_cell_data(path)
    assert {"site_id", "cell_id", "prb_utilization_pct"} <= set(df.columns)


def test_subscriber_columns_are_rejected(tmp_path):
    path = _write_csv(
        tmp_path,
        rows=[["S1", "C1", 50.0, "3510000000"]],
        header=["site_id", "cell_id", "prb_utilization_pct", "msisdn"],
    )
    with pytest.raises(DataValidationError, match="abbonato"):
        read_cell_data(path)


def test_missing_required_columns_error(tmp_path):
    path = _write_csv(
        tmp_path,
        rows=[["S1", "C1"]],
        header=["site_id", "cell_id"],
    )
    with pytest.raises(DataValidationError, match="prb_utilization_pct"):
        read_cell_data(path)


def test_unsupported_extension(tmp_path):
    path = tmp_path / "dati.txt"
    path.write_text("a,b,c", encoding="utf-8")
    with pytest.raises(DataValidationError, match="non supportato"):
        read_cell_data(str(path))


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_cell_data(str(tmp_path / "inesistente.csv"))


def test_empty_file_is_rejected(tmp_path):
    path = _write_csv(
        tmp_path, rows=[], header=["site_id", "cell_id", "prb_utilization_pct"]
    )
    with pytest.raises(DataValidationError, match="non contiene righe"):
        read_cell_data(path)


def test_out_of_range_percent_warns_but_reads(tmp_path):
    path = _write_csv(
        tmp_path,
        rows=[["S1", "C1", 150.0]],
        header=["site_id", "cell_id", "prb_utilization_pct"],
    )
    df = read_cell_data(path)  # solo avviso
    assert len(df) == 1
    with pytest.raises(DataValidationError, match="strict"):
        read_cell_data(path, strict=True)


def test_ambiguous_alias_warns(tmp_path):
    path = _write_csv(
        tmp_path,
        rows=[["S1", "C1", "C1x", 50.0]],
        header=["site_id", "cell_id", "cella", "prb_utilization_pct"],
    )
    df = read_cell_data(path)
    assert df["cell_id"].iloc[0] == "C1"  # prevale il nome standard
    with pytest.raises(DataValidationError, match="strict"):
        read_cell_data(path, strict=True)


def test_describe_dataset(sample_df):
    desc = describe_dataset(sample_df)
    assert "Righe totali" in desc
    assert "Celle uniche" in desc
    assert "Intervallo temporale" in desc
