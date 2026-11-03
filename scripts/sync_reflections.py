#!/usr/bin/env python3
"""Read the Published version of each reflection and publish it as HTML.

Read-only Google Docs access. The selection is based on source document structure,
not on redaction rules. Rough notes are excluded. Google Drive is never modified.
"""
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SCOPE = "https://www.googleapis.com/auth/documents.readonly"
DOCUMENTS = {
    1: "1hooa_XjoAVPRPebf6F3yb07RCiL0k4coKu7tQc9rjAs",
    2: "1H_StZt2sbxdTy8QcC5HfkW2c069-7e1c5gtZtXSrT3Q",
    3: "1HzSyW02_FMNCcJynbl7uPmc-4nuN-Jz5HUTMZdtvKDM",
    4: "1nwwmrlurPnl2gzp4msoz0UgYHZYk8Yd2tPAxwBc3ruA",
    5: "1bJSxhs6-f7VDcazZ_tTcDjcUaE8ONasGGKnmDI58G_Y",
}
NAV = [
    ("Home", "index.html"),
    ("About Me", "about.html"),
    ("Observations", "observations.html"),
    ("Goals", "goals.html"),
    ("Reflections", "reflections.html"),
    ("Standards", "standards.html"),
    ("Teaching", "teaching.html"),
    ("References", "references.html"),
]


def inline_elements(paragraph):
    chunks = []
    for element in paragraph.get("elements", []):
        text_run = element.get("textRun")
        if text_run is None:
            if "inlineObjectElement" in element:
                chunks.append("<em>[Embedded image or object in Google Doc]</em>")
            continue
        raw = text_run.get("content", "").rstrip("\n")
        if not raw:
            continue
        markup = html.escape(raw).replace("\n", "<br>")
        style = text_run.get("textStyle", {})
        if style.get("bold"):
            markup = f"<strong>{markup}</strong>"
        if style.get("italic"):
            markup = f"<em>{markup}</em>"
        if style.get("underline"):
            markup = f"<u>{markup}</u>"
        url = style.get("link", {}).get("url", "")
        if url and urlparse(url).scheme in ("http", "https"):
            markup = f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">{markup}</a>'
        chunks.append(markup)
    return "".join(chunks).strip()


def render_blocks(blocks):
    output = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for block in blocks:
        if "paragraph" in block:
            para = block["paragraph"]
            markup = inline_elements(para)
            if not markup:
                close_list()
                continue
            if "bullet" in para:
                if not in_list:
                    output.append("<ul>")
                    in_list = True
                output.append(f"<li>{markup}</li>")
                continue
            close_list()
            style = para.get("paragraphStyle", {}).get("namedStyleType", "")
            label = re.sub("<[^>]+>", "", markup).strip().lower()
            if style in ("TITLE", "HEADING_1", "HEADING_2") or label in (
                "what?", "so what?", "now what?", "references", "reference"
            ):
                tag = "h3"
            elif style in ("HEADING_3", "HEADING_4", "HEADING_5"):
                tag = "h4"
            else:
                tag = "p"
            output.append(f"<{tag}>{markup}</{tag}>")
        elif "table" in block:
            close_list()
            rows = []
            for row in block["table"].get("tableRows", []):
                cells = [
                    "<td>" + render_blocks(cell.get("content", [])) + "</td>"
                    for cell in row.get("tableCells", [])
                ]
                rows.append("<tr>" + "".join(cells) + "</tr>")
            output.append('<table class="document-table">' + "".join(rows) + "</table>")
    close_list()
    return "\n".join(output)


def _paragraph_text(block):
    para = block.get("paragraph", {})
    return "".join(
        e.get("textRun", {}).get("content", "")
        for e in para.get("elements", [])
    ).strip()


def _published_blocks(blocks):
    """Stop at the Rough notes heading when both sections are in one tab."""
    selected = []
    for block in blocks:
        title = _paragraph_text(block)
        if re.match(r"^(?:week\s*\d+\s*[–—-]\s*)?rough\s+notes\b", title, re.I):
            break
        if title.strip().casefold() == "published version":
            continue
        selected.append(block)
    return selected


def render_document(document):
    """Use only the explicitly titled Published version tab when present."""
    tabs = []

    def collect(tab):
        tabs.append(tab)
        for child in tab.get("childTabs", []):
            collect(child)

    for tab in document.get("tabs", []):
        collect(tab)

    if tabs:
        published = [
            t for t in tabs
            if t.get("tabProperties", {}).get("title", "").strip().casefold()
            == "published version"
        ]
        if len(published) == 1:
            blocks = published[0].get("documentTab", {}).get("body", {}).get("content", [])
        elif len(tabs) == 1:
            blocks = tabs[0].get("documentTab", {}).get("body", {}).get("content", [])
        else:
            raise RuntimeError(
                "Multiple Google Docs tabs found, but no unique 'Published version' tab. "
                "Refusing to publish other tabs."
            )
    else:
        blocks = document.get("body", {}).get("content", [])
    return render_blocks(_published_blocks(blocks))

def page(week, rendered):
    links = "".join(
        f'<a href="{target}">{html.escape(label)}</a>' for label, target in NAV
    )
    title = f"Week {week} Reflection"
    return f"""<!doctype html>
<html lang="en-NZ">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | ProfEx 1</title>
<link rel="stylesheet" href="portfolio-v2.css">
<script defer src="script.js"></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="sitehead"><div class="headinner">
<a class="brand" href="index.html"><span class="monogram">HJ</span>
<span>Haaris Jamil <small>Professional Experience 1</small></span></a>
<button class="menu" aria-expanded="false" aria-controls="nav">Menu ☰</button>
<nav id="nav" aria-label="Main navigation">{links}</nav>
</div></header>
<main id="main"><section class="section"><div class="shell">
<div class="sectionhead">
<p class="eyebrow"><a href="reflections.html">04 · Weekly Reflections</a> / Week {week}</p>
<h2>{title}</h2>
</div>
<article class="native-reflection"><div class="reflection-prose">
{rendered}
</div></article>
<p class="footnote"><a href="reflections.html">← All weekly reflections</a></p>
</div></section></main>
<footer><div class="shell footinner"><strong>Haaris Jamil · ProfEx 1</strong>
<a href="index.html">Home ↑</a></div></footer>
</body></html>
"""


def main():
    secret = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not secret:
        raise RuntimeError("Missing GitHub secret GOOGLE_SERVICE_ACCOUNT_JSON")
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(secret), scopes=[SCOPE]
    )
    session = AuthorizedSession(credentials)
    generated = {}
    for week, document_id in DOCUMENTS.items():
        endpoint = f"https://docs.googleapis.com/v1/documents/{document_id}"
        response = session.get(endpoint, params={"includeTabsContent": "true"}, timeout=40)
        if not response.ok:
            raise RuntimeError(f"Failed to read Week {week}: HTTP {response.status_code}")
        doc = response.json()
        rendered = render_document(doc)
        if not rendered.strip():
            raise RuntimeError(f"Week {week} returned no readable content; no files were replaced")
        generated[week] = page(week, rendered)
    for week, markup in generated.items():
        Path(f"reflection-week-{week}.html").write_text(markup, encoding="utf-8")
        print(f"Prepared reflection-week-{week}.html")


if __name__ == "__main__":
    main()
