"""Build SharePoint/OneDrive folder deep links for the Attachment column.

Given one sample folder link from the target library, this produces a working
link for each PR folder, mirroring the OneDrive layout:

    <root>/<YYYY>/<MM MonthName>/<PR folder>

e.g. ".../<root>/2026/05 May/<PR folder>".
The sample link provides the host, the library path, and the root folder
(everything above the year). No per-folder sharing token is needed.

Two sample link shapes are supported:
- Classic library view: ".../Forms/AllItems.aspx?id=<server-relative path>&viewid=..."
- Modern "Copy link" share link: ".../:f:/r/<server-relative path>?csf=1&web=1&e=..."
"""
from __future__ import annotations

import calendar
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse, urlunparse


class SharePointLinker:
    def __init__(self, sample_url: str):
        parsed = urlparse(sample_url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        self._scheme = parsed.scheme
        self._netloc = parsed.netloc

        if "id" in query:
            self._mode = "id"
            self._path = parsed.path  # kept verbatim (already percent-encoded)
            self._viewid = query.get("viewid", [None])[0]
            # The `id` is the server-relative path to the sample folder, e.g.
            # /sites/.../<root>/2026/05 May/<folder>. Drop the last three segments
            # (year, month, folder) to keep the stable root.
            sample_id = unquote(query["id"][0]).rstrip("/")
            self.root = "/".join(sample_id.split("/")[:-3])
        elif ":f:" in parsed.path or ":w:" in parsed.path:
            # Modern share link: the path itself is the server-relative folder
            # path (prefixed with a "/:f:/r/" marker), everything else about
            # navigating there is just a "shared with your org" style link.
            self._mode = "path"
            self._query_extra = {k: v[0] for k, v in query.items()}
            sample_path = unquote(parsed.path).rstrip("/")
            self.root = "/".join(sample_path.split("/")[:-3])
        else:
            raise SystemExit(
                "SHAREPOINT_FOLDER_URL: expected either an AllItems.aspx folder "
                "link with an 'id=' parameter, or a modern ':f:/r/...' share link "
                "(open the folder in the browser / use 'Copy link' and paste that URL)."
            )

    def url_for(self, year: int, month: int, folder_name: str) -> str:
        month_folder = f"{month:02d} {calendar.month_name[month]}"  # e.g. "05 May"
        path_id = f"{self.root}/{year}/{month_folder}/{folder_name}"

        if self._mode == "id":
            params = {"id": path_id}
            if self._viewid:
                params["viewid"] = self._viewid
            query = urlencode(params, quote_via=quote)  # space -> %20, "/" -> %2F
            return urlunparse((self._scheme, self._netloc, self._path, "", query, ""))

        path = quote(path_id, safe="/,()!'~*:")
        query = urlencode(self._query_extra) if self._query_extra else ""
        return urlunparse((self._scheme, self._netloc, path, "", query, ""))
