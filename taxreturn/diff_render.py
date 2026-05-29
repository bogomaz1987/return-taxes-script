"""Render a unified diff into a GitHub-styled HTML page (for screenshotting)."""
from __future__ import annotations

import html as _html
import re

_HUNK_RE = re.compile(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

_SKIP_PREFIXES = (
    "index ",
    "new file",
    "deleted file",
    "old mode",
    "new mode",
    "similarity ",
    "rename ",
    "copy ",
    "Binary ",
    "GIT binary",
)

_HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 16px; background: #ffffff;
         font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; }}
  .pr-title {{ font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
              font-size: 18px; font-weight: 600; color: #1f2328; margin: 0 0 16px; }}
  .file {{ border: 1px solid #d0d7de; border-radius: 6px; margin-bottom: 16px; overflow: hidden; }}
  .file-header {{ background: #f6f8fa; border-bottom: 1px solid #d0d7de; padding: 8px 12px;
                 font-size: 12px; font-weight: 600; color: #1f2328;
                 font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; }}
  table.diff-table {{ width: 100%; border-collapse: collapse; font-size: 12px; line-height: 20px; }}
  td.ln {{ width: 1%; min-width: 40px; text-align: right; padding: 0 10px;
          color: #6e7781; background: #ffffff; user-select: none;
          white-space: nowrap; vertical-align: top; }}
  td.code {{ white-space: pre-wrap; word-break: break-word; padding: 0 10px;
            color: #1f2328; vertical-align: top; }}
  tr.add td.code {{ background: #e6ffec; }}
  tr.add td.ln  {{ background: #ccffd8; }}
  tr.del td.code {{ background: #ffebe9; }}
  tr.del td.ln  {{ background: #ffd7d5; }}
  tr.hunk td {{ background: #f6f8fa; color: #57606a; }}
  tr.info td {{ background: #fff8c5; color: #57606a; }}
</style></head><body>
<div class="pr-title">{title}</div>
"""


def _file_name(git_line: str) -> str:
    # "diff --git a/path b/path" -> "path"
    m = re.search(r" b/(.+)$", git_line)
    return m.group(1) if m else ""


def _parse(diff_text: str) -> list[dict]:
    files: list[dict] = []
    cur: dict | None = None
    old_ln = new_ln = None

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            cur = {"name": _file_name(line), "rows": []}
            files.append(cur)
            old_ln = new_ln = None
            continue
        if cur is None:
            cur = {"name": "", "rows": []}
            files.append(cur)
        if line.startswith("+++ "):
            name = line[4:].strip()
            name = name[2:] if name.startswith("b/") else name
            if name and name != "/dev/null":
                cur["name"] = name
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("@@"):
            m = _HUNK_RE.search(line)
            if m:
                old_ln, new_ln = int(m.group(1)), int(m.group(2))
            cur["rows"].append(("hunk", "", "", line))
            continue
        if line.startswith(_SKIP_PREFIXES):
            continue
        if line.startswith("(no textual diff"):
            cur["rows"].append(("info", "", "", line))
            continue
        if old_ln is None:  # not inside a hunk yet
            continue
        if line.startswith("+"):
            cur["rows"].append(("add", "", new_ln, line[1:]))
            new_ln += 1
        elif line.startswith("-"):
            cur["rows"].append(("del", old_ln, "", line[1:]))
            old_ln += 1
        elif line.startswith("\\"):  # "\ No newline at end of file"
            cur["rows"].append(("hunk", "", "", line))
        else:
            content = line[1:] if line.startswith(" ") else line
            cur["rows"].append(("ctx", old_ln, new_ln, content))
            old_ln += 1
            new_ln += 1
    return files


def diff_to_html(diff_text: str, title: str) -> str:
    files = _parse(diff_text)
    out = [_HEAD.format(title=_html.escape(title))]
    for f in files:
        out.append('<div class="file">')
        out.append(f'<div class="file-header">{_html.escape(f["name"] or "file")}</div>')
        out.append('<table class="diff-table">')
        for kind, oln, nln, content in f["rows"]:
            if kind in ("hunk", "info"):
                out.append(
                    f'<tr class="{kind}"><td class="ln"></td><td class="ln"></td>'
                    f'<td class="code">{_html.escape(content)}</td></tr>'
                )
                continue
            sign = "+" if kind == "add" else "-" if kind == "del" else " "
            out.append(
                f'<tr class="{kind}"><td class="ln">{oln}</td><td class="ln">{nln}</td>'
                f'<td class="code">{_html.escape(sign + content)}</td></tr>'
            )
        out.append("</table></div>")
    out.append("</body></html>")
    return "\n".join(out)
