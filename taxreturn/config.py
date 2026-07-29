"""Configuration loaded from environment / .env file."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    github_token: str
    repos: list[str]
    author: str
    return_rate: float
    work_hours_per_day: float
    output_dir: Path
    headless: bool
    sharepoint_url: str


def load() -> Config:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo = os.getenv("REPO", "").strip()
    author = os.getenv("AUTHOR", "").strip()
    missing = [
        name
        for name, value in (("GITHUB_TOKEN", token), ("REPO", repo), ("AUTHOR", author))
        if not value
    ]
    if missing:
        raise SystemExit(
            f"Missing variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
    repos = [r for r in re.split(r"[,\s]+", repo) if r]
    return Config(
        github_token=token,
        repos=repos,
        author=author,
        return_rate=float(os.getenv("REFUND_PERCENT", "80")) / 100,
        work_hours_per_day=float(os.getenv("WORK_HOURS_PER_DAY", "8")),
        output_dir=Path(os.getenv("OUTPUT_DIR", "screenshots")).expanduser(),
        headless=os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes"),
        sharepoint_url=os.getenv("SHAREPOINT_FOLDER_URL", "").strip(),
    )
