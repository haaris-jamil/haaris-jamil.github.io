"""Turn links to mirrored Google files into links to their public portfolio pages.

This operates only on generated HTML and never changes the Google Drive sources.
It also resolves explicitly excluded redacted observation copies to their
original counterparts, where the matching original exists in the same folder.
"""
import html
import re
from collections import defaultdict
from urllib.parse import parse_qs, unquote, urlsplit

SOURCE_URL = re.compile(r"https?://(?:docs|drive)\.google\.com/[^\s<>'\"]+", re.I)
HTML_TAG = re.compile(r"(<[^>]+>)", re.S)
OPEN_ANCHOR = re.compile(r"<a\b[^>]*>", re.I | re.S)
HREF = re.compile(r"\bhref\s*=\s*([\"'])(.*?)\1", re.I | re.S)
SOURCE_FOOTER = re.compile(
    r"<p>\s*<a\b[^>]*>\s*(?:View source in Google Docs|"
    r"View source presentation|View source spreadsheet|Open source file)\s*↗?\s*</a>\s*</p>",
    re.I | re.S,
)
DOCUMENT_ID = re.compile(
    r"^/(?:document|spreadsheets|presentation)/d/([A-Za-z0-9_-]+)(?:/|$)", re.I
)
DRIVE_ID = re.compile(r"^/file/d/([A-Za-z0-9_-]+)(?:/|$)", re.I)
FOLDER_ID = re.compile(r"^/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)(?:/|$)", re.I)
ALLOWED_PAGES = re.compile(r"^[A-Za-z0-9_.-]+\.html(?:#[A-Za-z0-9_-]+)?$")


def file_id_from_url(url):
    """Return the Google Drive file ID for familiar file, Doc, Slide, and Sheet links."""
    try:
        parsed = urlsplit(html.unescape(url))
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    path = unquote(parsed.path)
    if host == "docs.google.com":
        match = DOCUMENT_ID.match(path)
        return match.group(1) if match else None
    if host in ("drive.google.com", "www.drive.google.com"):
        match = DRIVE_ID.match(path)
        if match:
            return match.group(1)
        if path in ("/open", "/uc", "/file/d"):
            return parse_qs(parsed.query).get("id", [None])[0]
    return None


def folder_id_from_url(url):
    try:
        parsed = urlsplit(html.unescape(url))
    except ValueError:
        return None
    if (parsed.hostname or "").lower() != "drive.google.com":
        return None
    match = FOLDER_ID.match(unquote(parsed.path))
    return match.group(1) if match else None


def _original_name(name):
    name = re.sub(r"\s*[-–—]?\s*redacted(?:\s+copy)?(?=\.pdf|$)", "", name, flags=re.I)
    name = re.sub(r"\.(pdf|docx?|pptx?)$", "", name, flags=re.I)
    return re.sub(r"\s+", " ", name).strip().casefold()


def make_local_map(records, published, excluded=(), category_slugs=()):
    """Resolve published files and Drive folder references to site URLs."""
    pages = {
        fid: info["page"]
        for fid, info in published.items()
        if info.get("page") and ALLOWED_PAGES.fullmatch(info["page"])
    }
    by_path = defaultdict(list)
    for item in records:
        if item.get("mimeType") == "application/vnd.google-apps.folder":
            continue
        if item["id"] not in pages:
            continue
        key = ("/".join(item.get("folderPath", [])), _original_name(item["name"]))
        by_path[key].append(item["id"])

    replacements = {}
    for entry in excluded:
        key = ("/".join(entry.get("folderPath", [])), _original_name(entry["name"]))
        originals = by_path.get(key, [])
        if len(originals) == 1:
            replacements[entry["id"]] = pages[originals[0]]
    pages.update(replacements)

    folders = {}
    root = "13L9IMcA3-j3OjUWTHgB8YKwYKXbvHKX4"
    folders[root] = "index.html"
    section_map = {name: page for name, page in category_slugs}
    for entry in records:
        if entry.get("mimeType") != "application/vnd.google-apps.folder":
            continue
        parts = entry.get("path", [])
        if not parts:
            continue
        main = section_map.get(parts[0])
        if not main:
            continue
        if "Y10 Science 1" in parts:
            main = "teaching.html#science-1"
        elif "Y10 Science 2" in parts:
            main = "teaching.html#science-2"
        folders[entry["id"]] = main
    return pages, folders


def _target(url, pages, folders):
    fid = file_id_from_url(url)
    if fid:
        return pages.get(fid)
    folder = folder_id_from_url(url)
    if folder:
        return folders.get(folder)
    return None


def rewrite_html(markup, pages, folders):
    """Rewrite hrefs and visible raw source URLs, preserving all other content."""
    counts = {"anchors": 0, "plain_urls": 0, "source_footers": 0, "unresolved": 0}
    markup, counts["source_footers"] = SOURCE_FOOTER.subn("", markup)

    def convert_tag(match):
        tag = match.group(0)
        current = HREF.search(tag)
        if not current:
            return tag
        target = _target(current.group(2), pages, folders)
        if not target:
            if file_id_from_url(current.group(2)):
                counts["unresolved"] += 1
            return tag
        counts["anchors"] += 1
        updated = tag[:current.start()] + f'href="{html.escape(target, quote=True)}"' + tag[current.end():]
        updated = re.sub(r"\s+(?:target|rel)\s*=\s*([\"']).*?\1", "", updated, flags=re.I | re.S)
        return updated

    markup = OPEN_ANCHOR.sub(convert_tag, markup)

    # Source URLs written as text in the Google Doc become clickable local links.
    fragments = HTML_TAG.split(markup)
    inside_anchor = False
    inside_script = False
    for i, part in enumerate(fragments):
        if i % 2:
            if re.match(r"<a\b", part, re.I):
                inside_anchor = True
            elif re.match(r"</a\b", part, re.I):
                inside_anchor = False
            elif re.match(r"<(?:script|style)\b", part, re.I):
                inside_script = True
            elif re.match(r"</(?:script|style)\b", part, re.I):
                inside_script = False
            continue
        if inside_anchor or inside_script:
            continue

        def make_local(match):
            original = match.group(0)
            trimmed = original.rstrip(".,;:)")
            ending = original[len(trimmed):]
            target = _target(trimmed, pages, folders)
            if not target:
                if file_id_from_url(trimmed):
                    counts["unresolved"] += 1
                return original
            counts["plain_urls"] += 1
            return (f'<a href="{html.escape(target, quote=True)}">'
                    f'View portfolio evidence</a>{ending}')

        fragments[i] = SOURCE_URL.sub(make_local, part)
    return "".join(fragments), counts
