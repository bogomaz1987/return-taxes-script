"""Render each PR's diff (fetched via API) to a local HTML page and screenshot it.

No GitHub web login / SSO is involved: the diff comes from the API with the token,
and Playwright only renders local HTML, so the browser can run headless.
"""
from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from .diff_render import diff_to_html
from .github_api import PullRequest, get_pr_diff

_INVALID = re.compile(r"[/\\\n\r\t]")


def sanitize(name: str) -> str:
    """Make a PR title safe to use as a folder name (keeps ':' as requested)."""
    cleaned = _INVALID.sub("-", name).strip()
    return cleaned[:150] or "pr"


def capture_html_diff(
    page: Page, html: str, out_dir: Path, quality: int = 85, max_shots: int = 300
) -> int:
    """Load the rendered diff HTML and save viewport-sized JPEG slices top-to-bottom."""
    out_dir.mkdir(parents=True, exist_ok=True)
    page.set_content(html, wait_until="load")
    page.wait_for_timeout(150)

    viewport_h = page.viewport_size["height"]
    total_h = page.evaluate("document.body.scrollHeight")
    step = max(viewport_h - 40, 200)  # small overlap between slices

    y = 0
    idx = 0
    while idx < max_shots:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(60)
        idx += 1
        page.screenshot(
            path=str(out_dir / f"screenshot_{idx}.jpg"), type="jpeg", quality=quality
        )
        if y + viewport_h >= total_h:
            break
        y += step
    return idx


def capture_all(
    prs: list[PullRequest], out_root: Path, cfg, skip: bool = False
) -> dict[int, Path]:
    """Fetch + render + screenshot every PR diff. Returns {pr_number: folder_path}."""
    folders = {pr.number: out_root / sanitize(pr.title) for pr in prs}

    if skip:
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)
        return folders

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=cfg.headless)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900}, device_scale_factor=2
        )
        page = context.new_page()

        for pr in prs:
            folder = folders[pr.number]
            print(f"  PR #{pr.number}: {pr.title}")
            diff_text = get_pr_diff(cfg.repo, pr.number, cfg.github_token)
            html = diff_to_html(diff_text, pr.title)
            shots = capture_html_diff(page, html, folder)
            print(f"    -> {shots} скриншот(ов) в {folder}")

        context.close()
        browser.close()

    return folders
