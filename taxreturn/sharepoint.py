"""Build SharePoint/OneDrive folder deep links for the Attachment column.

Given one sample "AllItems.aspx?id=..." folder link from the target library, this
produces a working link for each PR folder, mirroring the OneDrive layout:

    <root>/<YYYY>/<MM MonthName>/<PR folder>

e.g. ".../<root>/2026/05 May/<PR folder>".
The sample link provides the host, the library path, the `viewid`, and the root
folder (everything above the year). No per-folder sharing token is needed.
"""
from __future__ import annotations

import calendar
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse, urlunparse


class SharePointLinker:
    def __init__(self, sample_url: str):
        parsed = urlparse(sample_url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        if "id" not in query:
            raise SystemExit(
                "SHAREPOINT_FOLDER_URL: expected an AllItems.aspx folder link with an "
                "'id=' parameter (open the folder in the browser and copy the URL)."
            )
        # The `id` is the server-relative path to the sample folder, e.g.
        # /sites/.../<root>/2026/05 May/<folder>. Drop the last three segments
        # (year, month, folder) to keep the stable root.
        sample_id = unquote(query["id"][0]).rstrip("/")
        self.root = "/".join(sample_id.split("/")[:-3])
        self._scheme = parsed.scheme
        self._netloc = parsed.netloc
        self._path = parsed.path  # kept verbatim (already percent-encoded)
        self._viewid = query.get("viewid", [None])[0]

    def url_for(self, year: int, month: int, folder_name: str) -> str:
        month_folder = f"{month:02d} {calendar.month_name[month]}"  # e.g. "05 May"
        path_id = f"{self.root}/{year}/{month_folder}/{folder_name}"
        params = {"id": path_id}
        if self._viewid:
            params["viewid"] = self._viewid
        query = urlencode(params, quote_via=quote)  # space -> %20, "/" -> %2F
        return urlunparse((self._scheme, self._netloc, self._path, "", query, ""))
