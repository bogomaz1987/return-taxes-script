"""Build, print and export the tax-return hours table."""
from __future__ import annotations

import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .github_api import PullRequest

COLUMNS = ["PR Created", "PR Merge Date", "Time", "Attachment", "Description"]
_TOTAL_LABEL = "Total"


def _fmt_hours(hours: float) -> str:
    return f"{hours:g} hrs"


def build_rows(
    prs: list[PullRequest], hours_list: list[float], folders: dict[int, Path]
) -> list[dict[str, str]]:
    rows = []
    for pr, hours in zip(prs, hours_list):
        rows.append(
            {
                "PR Created": pr.created_at.strftime("%d.%m.%Y"),
                "PR Merge Date": pr.merged_at.strftime("%d.%m.%Y"),
                "Time": _fmt_hours(hours),
                "Attachment": str(folders[pr.number]),
                "Description": pr.title,
            }
        )
    rows.append(
        {
            "PR Created": "",
            "PR Merge Date": "",
            "Time": _fmt_hours(sum(hours_list)),
            "Attachment": "",
            "Description": _TOTAL_LABEL,
        }
    )
    return rows


def print_table(rows: list[dict[str, str]]) -> None:
    table = Table(show_lines=True)
    for col in COLUMNS:
        table.add_column(col, overflow="fold")
    for row in rows:
        if row["Description"] == _TOTAL_LABEL:
            table.add_section()
            table.add_row(*(row[col] for col in COLUMNS), style="bold")
        else:
            table.add_row(*(row[col] for col in COLUMNS))
    Console().print(table)


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
