"""Download and extract the CFPB Consumer Complaint Database."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

import requests


URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"
MEMBER = "complaints.csv"


def download(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "complaints.csv.zip"
    output_path = destination / MEMBER

    with requests.get(URL, stream=True, timeout=300) as response:
        response.raise_for_status()
        with archive_path.open("wb") as target:
            shutil.copyfileobj(response.raw, target)

    if not zipfile.is_zipfile(archive_path):
        raise ValueError("Downloaded file is not a valid ZIP archive.")

    with zipfile.ZipFile(archive_path) as archive:
        if MEMBER not in archive.namelist():
            raise ValueError(f"Expected {MEMBER!r} in source archive.")
        with archive.open(MEMBER) as source, output_path.open("wb") as target:
            shutil.copyfileobj(source, target)

    archive_path.unlink()
    print(f"Downloaded complaint data to {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download CFPB complaints.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    download(arguments.destination)
