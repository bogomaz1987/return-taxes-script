# return-taxes-script

A small command-line tool that prepares monthly evidence for an income-tax refund
based on your GitHub work.

For a chosen month it:

1. Finds your **merged** pull requests in a repository (GitHub API).
2. Downloads each PR's diff through the API, renders it as a GitHub-style HTML page,
   and saves screenshots of it. There is **no browser login** — the tool only renders
   local HTML, so it never touches the GitHub website or SSO.
3. Counts the working hours of the month using the **Polish** public-holiday calendar,
   takes **80%** of them, and splits that evenly across the pull requests.
4. Prints a table and writes a CSV:
   `PR Created | PR Merge Date | Time | Attachment | Description` plus a `Total` row.

The 80% share and the 8-hour working day come from a tax rule where only part of the
spent time is refundable; both values are configurable.

## Output layout

```
screenshots/
  2026-05/
    BP-3168: rm PlanContent - Release 7 - drop PlanContent/
      screenshot_1.jpg
      screenshot_2.jpg
      ...
    report.csv
```

Each pull request gets its own folder named after the PR title. The diff is captured
top to bottom as a series of JPEG slices (`screenshot_1.jpg`, `screenshot_2.jpg`, ...).

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager; it also installs Python for you).
- A GitHub Personal Access Token with read access to the repository.

## Setup from scratch

```bash
# 1. Clone the repository and enter it
git clone <your-repo-url>
cd return-taxes-script

# 2. Create the virtual environment and install dependencies
uv sync

# 3. Install the Chromium browser used for screenshots
uv run playwright install chromium

# 4. Create your configuration file and fill it in
cp .env.example .env
```

Open `.env` and set at least these three values:

- `GITHUB_TOKEN` — create one at GitHub → *Settings* → *Developer settings* →
  *Personal access tokens*. A classic token needs the `repo` scope. If the repository
  belongs to an organization that enforces SSO, open the token and click
  *Configure SSO* → *Authorize* for that organization.
- `REPO` — the repository to scan, written as `owner/name`.
- `AUTHOR` — the GitHub login whose merged pull requests you want.

## Usage

```bash
uv run python main.py                  # current month
uv run python main.py --month 2026-05  # a specific month (YYYY-MM)
uv run python main.py --no-screenshots # only compute the hours table, skip the browser
```

At the end of each month, run the tool, check the screenshots, and use `report.csv`
for your tax submission.

## Configuration (.env)

| Variable | Meaning | Default |
|---|---|---|
| `GITHUB_TOKEN` | Token used for both the PR search and the diff download | — (required) |
| `REPO` | Repository as `owner/name` | — (required) |
| `AUTHOR` | PR author's GitHub login | — (required) |
| `RETURN_RATE` | Refundable share of the time | `0.8` |
| `WORK_HOURS_PER_DAY` | Hours in one working day | `8` |
| `OUTPUT_DIR` | Root folder for screenshots and the CSV | `screenshots` |
| `HEADLESS` | `true` runs the browser hidden | `true` |

## Notes

- `.env` and the `screenshots/` folder are git-ignored, so your token and your work
  evidence never end up in the repository.
- Working days follow `workalendar`'s Polish calendar (public holidays + weekends).
- For very large diffs the API may refuse the full `.diff`; the tool then rebuilds the
  diff from per-file patches automatically.
