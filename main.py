"""Entry point.

For a given month: find your merged PRs in the repo, screenshot each diff into
`OUTPUT_DIR/YYYY-MM/<PR title>/screenshot_N.jpg`, compute Polish working hours,
distribute 80% of them evenly across the PRs, and print/export the hours table.

Usage:
    uv run python main.py                 # current month
    uv run python main.py --month 2026-05 # specific month
    uv run python main.py --no-screenshots
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from taxreturn import config
from taxreturn.github_api import get_merged_prs
from taxreturn.hours import distribute_hours, total_working_hours, working_days_count
from taxreturn.report import build_rows, print_table, write_csv
from taxreturn.screenshots import capture_all
from taxreturn.sharepoint import SharePointLinker


def parse_month(value: str | None) -> tuple[int, int]:
    if not value:
        today = dt.date.today()
        return today.year, today.month
    parsed = dt.datetime.strptime(value, "%Y-%m")
    return parsed.year, parsed.month


def main() -> int:
    parser = argparse.ArgumentParser(description="Tax-return PR screenshots & hours table.")
    parser.add_argument("--month", help="Target month YYYY-MM (defaults to the current month).")
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip screenshots and only compute the hours table.",
    )
    args = parser.parse_args()

    cfg = config.load()
    year, month = parse_month(args.month)
    month_dir = f"{year:04d}-{month:02d}"
    print(f"Month: {month_dir} | repository: {cfg.repo} | author: {cfg.author}")

    prs = get_merged_prs(cfg.repo, cfg.author, year, month, cfg.github_token)
    if not prs:
        print("No merged PRs found for this month.")
        return 0

    print(f"\nMerged PRs found: {len(prs)}")
    for pr in prs:
        print(f"  #{pr.number}  {pr.merged_at:%d.%m.%Y}  {pr.title}")

    days = working_days_count(year, month)
    total = total_working_hours(year, month, cfg.work_hours_per_day)
    returnable = round(total * cfg.return_rate, 2)
    hours_list = distribute_hours(total, len(prs), cfg.return_rate)
    print(
        f"\nWorking days (Poland): {days} → {total:g} h | "
        f"refundable {cfg.return_rate * 100:g}% = {returnable:g} h | "
        f"per PR ≈ {returnable / len(prs):.2f} h"
    )

    out_root = cfg.output_dir / month_dir
    folders = capture_all(prs, out_root, cfg, skip=args.no_screenshots)

    if cfg.sharepoint_url:
        linker = SharePointLinker(cfg.sharepoint_url)
        attachments = {
            pr.number: linker.url_for(year, month, folders[pr.number].name) for pr in prs
        }
    else:
        attachments = {pr.number: str(folders[pr.number]) for pr in prs}

    rows = build_rows(prs, hours_list, attachments)
    print()
    print_table(rows)

    csv_path = out_root / "report.csv"
    write_csv(rows, csv_path)
    print(f"\nCSV saved: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
