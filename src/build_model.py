"""Build privacy-conscious complaint reporting tables in chunks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


USE_COLUMNS = [
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company public response",
    "Company",
    "State",
    "Tags",
    "Consumer consent provided?",
    "Submitted via",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Consumer disputed?",
    "Complaint ID",
]


def aggregate(frame: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    summary = (
        frame.groupby(dimensions, dropna=False)
        .agg(
            complaints=("Complaint ID", "count"),
            timely_responses=("is_timely", "sum"),
            disputed_responses=("is_disputed", "sum"),
        )
        .reset_index()
    )
    return summary


def combine(parts: list[pd.DataFrame], dimensions: list[str]) -> pd.DataFrame:
    merged = pd.concat(parts, ignore_index=True)
    merged = (
        merged.groupby(dimensions, dropna=False)[
            ["complaints", "timely_responses", "disputed_responses"]
        ]
        .sum()
        .reset_index()
    )
    merged["timely_response_rate"] = merged["timely_responses"] / merged["complaints"]
    merged["dispute_rate"] = merged["disputed_responses"] / merged["complaints"]
    return merged.sort_values("complaints", ascending=False)


def build_model(
    source: Path,
    output_dir: Path,
    start_date: pd.Timestamp,
    chunksize: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fact_path = output_dir / "fact_complaints.csv"
    if fact_path.exists():
        fact_path.unlink()

    groups = {
        "monthly": ["received_month"],
        "product": ["Product", "Sub-product"],
        "issue": ["Product", "Issue", "Sub-issue"],
        "company": ["Company"],
        "state": ["State"],
        "channel": ["Submitted via"],
        "response": ["Company response to consumer"],
    }
    partials: dict[str, list[pd.DataFrame]] = {name: [] for name in groups}
    rows_written = 0

    for chunk in pd.read_csv(
        source,
        usecols=USE_COLUMNS,
        chunksize=chunksize,
        low_memory=False,
    ):
        chunk["Date received"] = pd.to_datetime(
            chunk["Date received"], errors="coerce"
        )
        chunk["Date sent to company"] = pd.to_datetime(
            chunk["Date sent to company"], errors="coerce"
        )
        chunk = chunk.loc[chunk["Date received"].ge(start_date)].copy()
        if chunk.empty:
            continue

        chunk["received_month"] = (
            chunk["Date received"].dt.to_period("M").astype("string")
        )
        chunk["days_to_company"] = (
            chunk["Date sent to company"] - chunk["Date received"]
        ).dt.days
        chunk["is_timely"] = chunk["Timely response?"].eq("Yes").astype(int)
        chunk["is_disputed"] = chunk["Consumer disputed?"].eq("Yes").astype(int)

        chunk.to_csv(
            fact_path,
            mode="a",
            header=rows_written == 0,
            index=False,
        )
        rows_written += len(chunk)

        for name, dimensions in groups.items():
            partials[name].append(aggregate(chunk, dimensions))

    if rows_written == 0:
        raise ValueError("No complaint rows matched the selected start date.")

    for name, dimensions in groups.items():
        combine(partials[name], dimensions).to_csv(
            output_dir / f"{name}_scorecard.csv",
            index=False,
        )

    print(f"Wrote {rows_written:,} complaint records to {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build complaint BI tables.")
    parser.add_argument(
        "--source", type=Path, default=Path("data/raw/complaints.csv")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/processed")
    )
    parser.add_argument("--start-date", type=pd.Timestamp, default=pd.Timestamp("2023-01-01"))
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_model(
        arguments.source,
        arguments.output_dir,
        arguments.start_date,
        arguments.chunksize,
    )
