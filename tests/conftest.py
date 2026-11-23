"""Fixture condivise: dataset sintetico e DataFrame normalizzato."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_data import generate  # noqa: E402
from data_reader import read_cell_data  # noqa: E402


@pytest.fixture
def sample_csv(tmp_path):
    """CSV di KPI sintetici (15 celle x 24 ore) in una cartella temporanea."""
    path = tmp_path / "kpis.csv"
    generate(str(path), days=1)
    return str(path)


@pytest.fixture
def sample_df(sample_csv):
    """DataFrame già letto e normalizzato dal reader."""
    return read_cell_data(sample_csv)
