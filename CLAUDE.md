# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Prepares monthly data for income-tax return. For a given month it: finds the user's
**merged** PRs in a repo (GitHub API), fetches each PR's diff via the API, renders it to
GitHub-styled HTML and screenshots it (Playwright on local HTML — no web login/SSO),
computes Polish working hours (`workalendar`), takes **80%** of them, distributes that
evenly across the PRs, and emits a table + CSV.

## Commands

```bash
uv sync                                # create .venv + install deps
uv run playwright install chromium     # one-time browser download
uv run python main.py                  # process current month
uv run python main.py --month 2026-05  # specific month
uv run python main.py --no-screenshots # table only, skip the browser
```

Config comes from `.env` (see `.env.example`). Required: `GITHUB_TOKEN` (used for BOTH the
PR search and the diff fetch; authorize it for SSO if the repo's org enforces it), `REPO`
(`owner/name`), `AUTHOR`. Optional: `REFUND_PERCENT` (0-100, stored as the `return_rate`
fraction), `WORK_HOURS_PER_DAY`, `OUTPUT_DIR`, `HEADLESS`.

## Architecture

`main.py` orchestrates; logic lives in the `taxreturn/` package:

- `config.py` — loads `.env` into a `Config` dataclass.
- `github_api.py` — `get_merged_prs()` queries the GitHub **Search API**
  (`is:pr is:merged merged:START..END`), returns `PullRequest` dataclasses sorted by merge date.
  `get_pr_diff()` fetches a PR's unified diff via the API (`Accept: application/vnd.github.v3.diff`),
  falling back to assembling per-file patches from the files endpoint for oversized diffs.
- `diff_render.py` — `_parse()` turns a unified diff into files/rows; `diff_to_html()` emits a
  self-contained GitHub-styled HTML page (file headers, old/new line-number columns, green/red rows).
- `hours.py` — Polish working days via `workalendar.europe.Poland`; `distribute_hours()`
  splits `total * rate` evenly and pushes rounding drift into the last share so the sum is exact.
- `screenshots.py` — Playwright (headless ok). `capture_all()` loops PRs: fetch diff → render HTML →
  `capture_html_diff()` loads it via `page.set_content` and saves viewport-sized `screenshot_N.jpg`
  slices. **No GitHub web login / SSO** — only local HTML is rendered.
- `report.py` — builds rows, prints a `rich` table, writes `report.csv`.

## Conventions / gotchas

- Output tree: `OUTPUT_DIR/YYYY-MM/<sanitized PR title>/screenshot_N.jpg`; folder names keep
  `:` but replace path-breaking chars (see `screenshots.sanitize`).
- Table columns: `PR Merge Date | Time | Attachment | Description`.
- Requires Python ≥3.10 (`str | None` annotations). The IDE may flag these if it's pointed at
  the system 3.9 — harmless under the uv-managed interpreter.
- `screenshots/` and `.env` are git-ignored.
