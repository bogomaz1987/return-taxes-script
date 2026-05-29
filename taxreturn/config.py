"""Configuration loaded from environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    github_token: str
    repo: str
    author: str
    return_rate: float
    work_hours_per_day: float
    output_dir: Path
    headless: bool


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
    return Config(
        github_token=token,
        repo=repo,
        author=author,
        return_rate=float(os.getenv("REFUND_PERCENT", "80")) / 100,
        work_hours_per_day=float(os.getenv("WORK_HOURS_PER_DAY", "8")),
        output_dir=Path(os.getenv("OUTPUT_DIR", "screenshots")).expanduser(),
        headless=os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes"),
    )
