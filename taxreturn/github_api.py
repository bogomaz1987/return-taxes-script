"""Find merged pull requests for a given author/repo/month via the GitHub Search API."""
from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass

import requests

SEARCH_URL = "https://api.github.com/search/issues"


@dataclass
class PullRequest:
    number: int
    title: str
    url: str
    created_at: dt.datetime
    merged_at: dt.datetime


def _month_range(year: int, month: int) -> tuple[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def _parse_dt(raw: str) -> dt.datetime:
    return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))


def get_merged_prs(
    repo: str, author: str, year: int, month: int, token: str
) -> list[PullRequest]:
    """Return PRs by `author` in `repo` that were merged within the given month."""
    start, end = _month_range(year, month)
    query = f"repo:{repo} author:{author} is:pr is:merged merged:{start}..{end}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    prs: list[PullRequest] = []
    page = 1
    while True:
        resp = requests.get(
            SEARCH_URL,
            headers=headers,
            params={"q": query, "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        for it in items:
            merged_raw = it.get("pull_request", {}).get("merged_at") or it.get("closed_at")
            prs.append(
                PullRequest(
                    number=it["number"],
                    title=it["title"],
                    url=it["html_url"],
                    created_at=_parse_dt(it["created_at"]),
                    merged_at=_parse_dt(merged_raw),
                )
            )
        if len(items) < 100:
            break
        page += 1

    prs.sort(key=lambda p: p.merged_at)
    return prs


def get_pr_diff(repo: str, number: int, token: str) -> str:
    """Return the unified diff text of a PR via the API (token-only, no browser).

    Tries the `.diff` media type first; falls back to assembling per-file patches
    from the files endpoint when GitHub refuses the full diff (e.g. too large).
    """
    base = f"https://api.github.com/repos/{repo}/pulls/{number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.get(
        base, headers={**headers, "Accept": "application/vnd.github.v3.diff"}, timeout=60
    )
    if resp.status_code == 200 and resp.text.strip():
        return resp.text
    return _diff_from_files(base, headers)


def _diff_from_files(base: str, headers: dict) -> str:
    parts: list[str] = []
    page = 1
    while True:
        resp = requests.get(
            f"{base}/files",
            headers={**headers, "Accept": "application/vnd.github+json"},
            params={"per_page": 100, "page": page},
            timeout=60,
        )
        resp.raise_for_status()
        files = resp.json()
        for f in files:
            name = f["filename"]
            parts.append(f"diff --git a/{name} b/{name}")
            patch = f.get("patch")
            if patch:
                parts.append(f"--- a/{name}")
                parts.append(f"+++ b/{name}")
                parts.append(patch)
            else:
                parts.append(
                    f"(no textual diff: {f.get('status')}, "
                    f"+{f.get('additions', 0)}/-{f.get('deletions', 0)})"
                )
        if len(files) < 100:
            break
        page += 1
    return "\n".join(parts)
