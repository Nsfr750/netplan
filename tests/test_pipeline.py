"""Test di integrazione per pipeline.run_analysis."""

import os

from pipeline import run_analysis


def test_run_analysis_produces_outputs(sample_csv, tmp_path):
    outdir = str(tmp_path / "out")
    result = run_analysis(sample_csv, outdir)

    for key in ("csv_cell", "csv_site", "xlsx", "html", "pdf"):
        assert result[key] and os.path.exists(result[key]), key

    chart_names = {os.path.basename(p) for p in result["charts"]}
    assert "prb_distribution.png" in chart_names
    assert "trend_celle.png" in chart_names  # il sample ha 24 rilevazioni orarie

    cs = result["cell_summary"]
    assert set(cs["severity"].unique()) <= {"OK", "ATTENZIONE", "CRITICO"}
    assert "recommendation" in cs.columns


def test_run_analysis_without_html_pdf(sample_csv, tmp_path):
    outdir = str(tmp_path / "out")
    result = run_analysis(sample_csv, outdir, html_report=False, pdf_report=False)
    assert result["html"] is None
    assert result["pdf"] is None
    assert os.path.exists(result["csv_cell"])
