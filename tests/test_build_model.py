"""Missing dispute outcomes must not be reported as negative outcomes."""

import pandas as pd

from src.build_model import aggregate, combine, build_model, USE_COLUMNS


def test_dispute_rate_uses_only_known_outcomes_across_chunks():
    frame = pd.DataFrame({
        "Complaint ID": [1, 2, 3, 4],
        "Company": ["A", "A", "B", "B"],
        "is_timely": [1, 0, 1, 0],
        "is_disputed": pd.Series([pd.NA, 1, pd.NA, pd.NA], dtype="Int64"),
    })
    parts = [aggregate(frame.iloc[:2], ["Company"]), aggregate(frame.iloc[2:], ["Company"])]
    result = combine(parts, ["Company"]).set_index("Company")
    assert result.loc["A", "dispute_observations"] == 1
    assert result.loc["A", "dispute_rate"] == 1.0
    assert result.loc["B", "dispute_observations"] == 0
    assert pd.isna(result.loc["B", "dispute_rate"])


def test_end_to_end_missing_dispute_is_not_false_zero(tmp_path):
    records = [{column: "" for column in USE_COLUMNS} for _ in range(2)]
    for number, record in enumerate(records, start=1):
        record.update({
            "Complaint ID": number,
            "Date received": "2026-01-01",
            "Date sent to company": "2026-01-02",
            "Company": "Example",
            "Timely response?": "Yes",
            "Consumer disputed?": "" if number == 1 else "No",
        })
    source = tmp_path / "complaints.csv"
    pd.DataFrame(records).to_csv(source, index=False)
    output = tmp_path / "processed"
    build_model(source, output, pd.Timestamp("2025-01-01"), chunksize=1)
    score = pd.read_csv(output / "company_scorecard.csv").iloc[0]
    assert score["complaints"] == 2
    assert score["dispute_observations"] == 1
    assert score["disputed_responses"] == 0
    assert score["dispute_rate"] == 0


def test_all_unknown_disputes_yield_blank_rate(tmp_path):
    records = [{column: "" for column in USE_COLUMNS}]
    records[0].update({
        "Complaint ID": 1,
        "Date received": "2026-01-01",
        "Company": "Example",
        "Consumer disputed?": "",
    })
    source = tmp_path / "complaints.csv"
    pd.DataFrame(records).to_csv(source, index=False)
    output = tmp_path / "processed"
    build_model(source, output, pd.Timestamp("2025-01-01"), chunksize=1)
    score = pd.read_csv(output / "company_scorecard.csv").iloc[0]
    assert score["dispute_observations"] == 0
    assert pd.isna(score["dispute_rate"])


def test_failed_rebuild_preserves_previous_successful_outputs(tmp_path):
    output = tmp_path / "processed"
    output.mkdir()
    previous_fact = output / "fact_complaints.csv"
    previous_scorecard = output / "company_scorecard.csv"
    previous_fact.write_text("previous fact data")
    previous_scorecard.write_text("previous scorecard")

    record = {column: "" for column in USE_COLUMNS}
    record.update({"Complaint ID": 1, "Date received": "2020-01-01"})
    source = tmp_path / "complaints.csv"
    pd.DataFrame([record]).to_csv(source, index=False)

    import pytest

    with pytest.raises(ValueError, match="No complaint rows matched"):
        build_model(source, output, pd.Timestamp("2025-01-01"), chunksize=1)
    assert previous_fact.read_text() == "previous fact data"
    assert previous_scorecard.read_text() == "previous scorecard"
    assert not list(output.glob(".complaints-build-*"))
