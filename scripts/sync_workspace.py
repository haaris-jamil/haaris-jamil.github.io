#!/usr/bin/env python3
"""Synchronise the entire ProfEx 1 Drive folder into GitHub Pages.

Read-only access to Google. The portfolio's folder structure is preserved in
webpage indexes. Reflections publish their 'Published version' section only.
No automatic anonymisation, editing or rewriting of source text is performed.
"""
import html
import json
import os
import re
from collections import Counter, defaultdict
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

from sync_reflections import (
    render_blocks, render_document as render_published,
    page as reflection_page
)
from sync_media import api_json, sync_sheet, sync_slides, sync_binary, sync_doc_images, esc
from lesson_layout import (
    exclude_from_website, current_events, teaching_body,
    lesson_plan_entry, lesson_number, plan_page_info, strip_duplicate_title,
    slide_page_info,
)
from site_links import make_local_map, rewrite_html
from section_pages import (
    DOCUMENTS, GOALS_ID, STANDARDS_ID, sections_from_html, subpage_bodies, hub_body
)

ROOT_ID = "13L9IMcA3-j3OjUWTHgB8YKwYKXbvHKX4"
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/presentations.readonly",
]
CATEGORIES = [
    ("01 About Me", "about.html", "Teacher statement & pepeha",
     "My background, philosophy and pepeha."),
    ("02 Observations", "observations.html", "Observations",
     "Initial observation tasks, observations of others and feedback on my teaching."),
    ("03 Professional Goals", "goals.html", "Professional goals",
     "Goals, rationale, action steps, evaluations and linked evidence."),
    ("04 Weekly Reflections", "reflections.html", "Weekly reflections",
     "Critical reflections from each placement week."),
    ("05 Professional Standards", "standards.html", "Professional standards",
     "Standards evidence, rationale and KTT connections."),
    ("06 Teaching & Planning", "teaching.html", "Teaching & planning",
     "Unit planning, lesson plans, resources, evidence and learning events."),
    ("07 References", "references.html", "References",
     "Professional reading and academic sources."),
]
NAV = [
    ("Home", "index.html"), ("About Me", "about.html"),
    ("Observations", "observations.html"), ("Goals", "goals.html"),
    ("Reflections", "reflections.html"), ("Standards", "standards.html"),
    ("Teaching", "teaching.html"), ("References", "references.html"),
]
MANIFEST = Path(".sync-manifest/portfolio.json")
DOC_MIME = "application/vnd.google-apps.document"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
SLIDE_MIME = "application/vnd.google-apps.presentation"
FOLDER_MIME = "application/vnd.google-apps.folder"


def write(path, contents):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.is_file() or dest.read_text(encoding="utf-8") != contents:
        dest.write_text(contents, encoding="utf-8")


def document_html(title, caption, inner, back="teaching.html"):
    links = "".join(
        f'<a href="{esc(target)}">{esc(label)}</a>' for label, target in NAV
    )
    return f"""<!doctype html>
<html lang="en-NZ"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | ProfEx 1</title>
<link rel="stylesheet" href="portfolio-v2.css"><script defer src="script.js"></script>
</head><body><a class="skip" href="#main">Skip to content</a>
<header class="sitehead"><div class="headinner">
<a class="brand" href="index.html"><span class="monogram">HJ</span>
<span>Haaris Jamil <small>Professional Experience 1</small></span></a>
<button class="menu" aria-controls="nav" aria-expanded="false">Menu ☰</button>
<nav id="nav" aria-label="Main navigation">{links}</nav></div></header>
<main id="main"><section class="section"><div class="shell">
<div class="sectionhead"><p class="eyebrow">Professional Experience 1</p>
<h2>{esc(title)}</h2><p>{esc(caption)}</p></div>
{inner}
</div></section></main>
<footer><div class="shell footinner"><strong>Haaris Jamil · ProfEx 1</strong>
<a href="{esc(back)}">Return to portfolio ↑</a></div></footer>
</body></html>"""


def list_children(session, folder):
    gathered = []
    token = None
    while True:
        params = {
            "q": f"'{folder}' in parents and trashed = false",
            "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,webViewLink)",
            "pageSize": 1000,
        }
        if token:
            params["pageToken"] = token
        data = api_json(session, DRIVE_API, params=params)
        gathered.extend(data.get("files", []))
        token = data.get("nextPageToken")
        if not token:
            return gathered


def scan_drive(session):
    entries = []
    queue = [(ROOT_ID, [])]
    seen = set()
    while queue:
        parent, labels = queue.pop(0)
        if parent in seen:
            continue
        seen.add(parent)
        for file in list_children(session, parent):
            record = dict(file)
            record["path"] = labels + [file["name"]]
            record["folderPath"] = labels
            entries.append(record)
            if record["mimeType"] == FOLDER_MIME:
                queue.append((file["id"], record["path"]))
    return sorted(entries, key=lambda x: "/".join(x["path"]).casefold())


def all_doc_html(doc):
    tabs = doc.get("tabs") or []
    if not tabs:
        return render_blocks(doc.get("body", {}).get("content", []))
    segments = []

    def visit(tab):
        title = tab.get("tabProperties", {}).get("title", "")
        if len(tabs) > 1 and title:
            segments.append(f"<h3>{esc(title)}</h3>")
        content = tab.get("documentTab", {}).get("body", {}).get("content", [])
        segments.append(render_blocks(content))
        for nested in tab.get("childTabs", []):
            visit(nested)

    for tab in tabs:
        visit(tab)
    return "\n".join(segments)


def folder_area(entry):
    if entry["folderPath"]:
        return entry["folderPath"][0]
    return "Other portfolio files"


def file_source_link(entry):
    kind = entry["mimeType"]
    fid = entry["id"]
    existing = entry.get("webViewLink")
    if existing:
        return existing
    if kind == DOC_MIME:
        return f"https://docs.google.com/document/d/{fid}/edit"
    if kind == SHEET_MIME:
        return f"https://docs.google.com/spreadsheets/d/{fid}/edit"
    if kind == SLIDE_MIME:
        return f"https://docs.google.com/presentation/d/{fid}/edit"
    return f"https://drive.google.com/file/d/{fid}/view"


def file_description(entry, page, note=""):
    out = '<div class="source-item">'
    if page:
        out += f'<a class="source-title" href="{esc(page)}">{esc(entry["name"])}</a>'
    else:
        out += (
            f'<a class="source-title" href="{esc(file_source_link(entry))}" '
            'target="_blank" rel="noopener noreferrer">'
            f'{esc(entry["name"])}</a>'
        )
    if note:
        out += f'<p>{esc(note)}</p>'
    return out + "</div>"


def section_index(title, desc, entries, linked, errors, category):
    grouped = defaultdict(list)
    for e in entries:
        key = e["folderPath"][-1] if len(e["folderPath"]) > 1 else "Main documents"
        key = re.sub(r"^\d+\s+", "", key)
        note = linked.get(e["id"], {}).get("note", "")
        grouped[key].append(file_description(e, linked.get(e["id"], {}).get("page"), note))
    panels = []
    for label in sorted(grouped, key=str.casefold):
        panels.append(
            f'<section class="portfolio-source-group"><h3>{esc(label)}</h3>'
            + "".join(grouped[label]) + "</section>"
        )
    if not panels:
        panels.append("<p>No source documents are currently present in this section.</p>")
    if category == "06 Teaching & Planning":
        panels.insert(0,
            '<p><a class="button primary" href="learning-events.html">'
            'Learning events register</a></p>'
        )
    return document_html(title, desc, '<div class="portfolio-sources">' + "".join(panels) + "</div>")


def reflection_index(weeks):
    cards = []
    for w, _name in sorted(weeks.items()):
        cards.append(
            f'<a class="tile" href="reflection-week-{w}.html"><span class="number">'
            f'{w:02}</span><h3>Week {w}</h3><span class="jump">Read reflection ↗</span></a>'
        )
    cards.append(
        '<article class="tile"><span class="number">More</span><h3>Further reflections</h3>'
        '<p>New reflections will appear here as they are added to the portfolio.</p></article>'
    )
    return document_html(
        "Weekly reflections",
        "Critical reflections informed by Rolfe's What? So what? Now what? framework.",
        '<div class="tilegrid">' + "".join(cards) + "</div>",
        back="index.html",
    )


def audit_page(scanned, linked, failures, not_auto, incomplete):
    counted = Counter(x["mimeType"].split(".")[-1] for x in scanned
                      if x["mimeType"] != FOLDER_MIME)
    summary = (
        f"<p>Source files found: {sum(counted.values())}. "
        f"Discovered and linked: {len(linked)}. "
        f"Unable to update in this run: {len(failures)}. "
        f"Not configured to mirror: {len(not_auto)}.</p>"
    )
    def listing(items, none):
        if not items:
            return f"<p>{none}</p>"
        return "<ul>" + "".join(
            f'<li>{esc(x.get("path", "?"))}: {esc(x.get("reason", "?"))}</li>'
            for x in items
        ) + "</ul>"
    body = summary + (
        "<h3>1. Could not update</h3>" + listing(failures, "No failed updates recorded.")
        + "<h3>2. Not set to sync automatically</h3>"
        + listing(not_auto, "All discovered supported files have a sync path.")
        + "<h3>Partial presentation limitations</h3>"
        + listing(incomplete, "No partial-content limitations recorded.")
    )
    return document_html(
        "Portfolio synchronisation audit",
        "Generated from the most recent successful folder scan.",
        '<article class="native-reflection"><div class="reflection-prose">' + body + "</div></article>",
        back="index.html"
    )


def main():
    secret = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not secret:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON secret is missing")
    creds = service_account.Credentials.from_service_account_info(
        json.loads(secret), scopes=SCOPES
    )
    session = AuthorizedSession(creds)
    old = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}
    old_files = old.get("files", {})
    scanned = scan_drive(session)
    excluded = [e for e in scanned if exclude_from_website(e)]
    records = [e for e in scanned if not exclude_from_website(e)]
    for e in excluded:
        # Deliberately remove website copies of redacted observation duplicates;
        # nothing is deleted or changed in Google Drive.
        stale_id = e["id"]
        Path(f"file-{stale_id}.html").unlink(missing_ok=True)
        shutil.rmtree(Path("assets/drive") / stale_id, ignore_errors=True)
    events = current_events(session)
    print(f"Discovered {len(scanned)} Drive entries; excluded {len(excluded)} "
          "redacted observation duplicates from the website")
    linked, current_files = {}, {}
    failures, not_auto, incomplete = [], [], []
    pages = set()
    weeks = {}
    section_hubs = {}
    for entry in records:
        if entry["mimeType"] == FOLDER_MIME:
            continue
        fid = entry["id"]
        path = "/".join(entry["path"])
        kind = entry["mimeType"]
        src = file_source_link(entry)
        category = folder_area(entry)
        backlink = next((slug for name, slug, _, _ in CATEGORIES if name == category), "index.html")
        previous = old_files.get(fid, {})
        try:
            if kind == DOC_MIME:
                response = api_json(
                    session, f"https://docs.googleapis.com/v1/documents/{fid}",
                    params={"includeTabsContent": "true"},
                )
                if category == "04 Weekly Reflections" and re.match(
                    r"^Week\s+(\d+)\b", entry["name"], re.I
                ):
                    week = int(re.match(r"^Week\s+(\d+)\b", entry["name"], re.I).group(1))
                    markup = render_published(response)
                    markup, image_warnings = sync_doc_images(
                        response, markup, fid, entry.get("modifiedTime", ""), previous,
                        published_only=True,
                    )
                    for reason in image_warnings:
                        incomplete.append({"path": path, "reason": reason})
                    if not markup.strip():
                        raise RuntimeError("Published version is empty")
                    page = f"reflection-week-{week}.html"
                    write(page, reflection_page(week, markup))
                    weeks[week] = entry["name"]
                else:
                    markup = all_doc_html(response)
                    markup, image_warnings = sync_doc_images(
                        response, markup, fid, entry.get("modifiedTime", ""), previous,
                        published_only=False,
                    )
                    for reason in image_warnings:
                        incomplete.append({"path": path, "reason": reason})
                    if not markup.strip():
                        markup = "<p>Document is empty.</p>"
                    if fid in DOCUMENTS:
                        cfg = DOCUMENTS[fid]
                        selected = sections_from_html(markup, fid)
                        for child_page, info in subpage_bodies(fid, selected).items():
                            write(child_page, document_html(
                                info["title"], info["caption"], info["body"], back=info["back"]
                            ))
                            pages.add(child_page)
                        hub_markup = hub_body(fid, selected)
                        section_hubs[cfg["hub"]] = document_html(
                            cfg["label"], cfg["intro"], hub_markup, back="index.html"
                        )
                        # Keep the former all-in-one URL valid, but never expose
                        # Standards 1, 4 or 5 in that obsolete website location.
                        legacy = f"doc-{fid}.html"
                        write(legacy, document_html(
                            cfg["label"], "This content is organised into separate sections.",
                            hub_markup, back=cfg["hub"]
                        ))
                        pages.add(legacy)
                        page = cfg["hub"]
                    else:
                        page = f"doc-{fid}.html"
                        detail = plan_page_info(entry, events)
                        if detail:
                            title, caption = detail
                            markup = strip_duplicate_title(markup, lesson_number(entry))
                        else:
                            title, caption = entry["name"], "Portfolio source document"
                        write(page, document_html(
                            title, caption,
                            f'<article class="native-reflection"><div class="reflection-prose">'
                            + markup + "</div></article>"
                            + f'<p><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">'
                            'View source in Google Docs ↗</a></p>',
                            back=backlink,
                        ))
                if "[Embedded image or object in Google Doc]" in markup:
                    incomplete.append({
                        "path": path, "reason": "Inline images or drawings show as placeholders"
                    })
                linked[fid] = {"page": page}
                pages.add(page)
            elif kind == SHEET_MIME:
                page, title, markup, trunc = sync_sheet(session, entry, previous)
                write(page, document_html(
                    title, "Spreadsheet data and links from Google Sheets.",
                    f'<p><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">'
                    'View source spreadsheet ↗</a></p>' + markup, back=backlink,
                ))
                for reason in trunc:
                    incomplete.append({"path": path, "reason": reason})
                linked[fid] = {"page": page}
                pages.add(page)
            elif kind == SLIDE_MIME:
                page, title, markup, cache = sync_slides(session, entry, previous)
                title, caption = slide_page_info(entry, events)
                write(page, document_html(
                    title, caption,
                    f'<p><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">'
                    'View source presentation ↗</a></p>' + markup, back=backlink,
                ))
                linked[fid] = {"page": page}
                previous.update(cache)
                pages.add(page)
            else:
                preview, why = sync_binary(session, entry, previous)
                if preview is None:
                    not_auto.append({"path": path, "reason": why})
                    linked[fid] = {"page": None, "note": why}
                else:
                    page = f"file-{fid}.html"
                    write(page, document_html(
                        entry["name"], "Original file from Google Drive.",
                        preview + f'<p><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">'
                        'Open source file ↗</a></p>', back=backlink
                    ))
                    linked[fid] = {"page": page}
                    pages.add(page)
            current_files[fid] = {
                "modifiedTime": entry.get("modifiedTime", ""),
                "path": path,
                "page": linked[fid].get("page"),
                **{k: previous[k] for k in ("slides",) if k in previous},
            }
        except Exception as err:
            print(f"Unable to sync {path}: {err}", flush=True)
            failures.append({"path": path, "reason": str(err)[:350]})
            # Failed conversions remain scheduled for retry, so they are not
            # classified as intentionally excluded from automatic sync.
            last_page = previous.get("page")
            if not last_page and category == "04 Weekly Reflections":
                matched = re.match(r"^Week\s+(\d+)\b", entry["name"], re.I)
                if matched:
                    candidate = f"reflection-week-{matched.group(1)}.html"
                    if Path(candidate).is_file():
                        last_page = candidate
            if last_page and Path(last_page).is_file():
                linked[fid] = {"page": last_page, "note": "Earlier website copy; source update failed"}
                pages.add(last_page)
                if category == "04 Weekly Reflections":
                    matched = re.match(r"^Week\s+(\d+)\b", entry["name"], re.I)
                    if matched:
                        weeks[int(matched.group(1))] = entry["name"]
            else:
                linked[fid] = {"page": None, "note": "Open the Google Drive source"}
            current_files[fid] = previous
    for name, slug, title, desc in CATEGORIES:
        if name == "04 Weekly Reflections":
            write(slug, reflection_index(weeks))
        elif slug in section_hubs:
            write(slug, section_hubs[slug])
        elif slug in ("goals.html", "standards.html") and Path(slug).is_file():
            # On a temporary source-read failure, preserve the previously
            # published navigation and its sections rather than reverting.
            source_id = GOALS_ID if slug == "goals.html" else STANDARDS_ID
            for number in DOCUMENTS[source_id]["allowed"]:
                cached = f'{DOCUMENTS[source_id]["prefix"]}-{number}.html'
                if Path(cached).is_file():
                    pages.add(cached)
        else:
            subset = [f for f in records if f["mimeType"] != FOLDER_MIME and folder_area(f) == name]
            if name == "06 Teaching & Planning":
                markup = teaching_body(subset, linked, events)
                write(slug, document_html(
                    "Teaching & planning", "Lesson sequences, delivery and evidence.",
                    markup, back="index.html",
                ))
            else:
                write(slug, section_index(title, desc, subset, linked, failures, name))
        pages.add(slug)
    miscellaneous = [
        f for f in records if f["mimeType"] != FOLDER_MIME
        and folder_area(f) == "Other portfolio files"
    ]
    write("portfolio-sources.html", section_index(
        "Other portfolio files", "Documents stored in the root of the portfolio Drive folder.",
        miscellaneous, linked, failures, "Other portfolio files"
    ))
    pages.add("portfolio-sources.html")
    write("sync-audit.html", audit_page(records, linked, failures, not_auto, incomplete))
    pages.add("sync-audit.html")
    # Rebuild internal cross-references only after all source files have been
    # scanned and their matching local pages are known.
    local_pages, local_folders = make_local_map(
        records, linked, excluded, [(name, slug) for name, slug, _, _ in CATEGORIES]
    )
    link_counts = {"anchors": 0, "plain_urls": 0, "source_footers": 0, "unresolved": 0}
    for html_page in sorted(pages | {"index.html"}):
        target = Path(html_page)
        if not target.is_file():
            continue
        original = target.read_text(encoding="utf-8")
        updated, changes = rewrite_html(original, local_pages, local_folders)
        if updated != original:
            write(html_page, updated)
        for name, amount in changes.items():
            link_counts[name] += amount
    print("Internal source links: " + json.dumps(link_counts))
    for stale in set(old.get("generatedPages", [])) - pages:
        target = Path(stale)
        if target.name.startswith(("doc-", "sheet-", "slides-", "file-", "reflection-week-")):
            target.unlink(missing_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "root": ROOT_ID, "files": current_files,
        "generatedPages": sorted(pages),
        "failures": failures, "notAutomaticallySynced": not_auto,
        "partialSupport": incomplete,
        "linkRewriting": link_counts,
    }
    write(MANIFEST, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"Published {len(linked)} source entries; {len(failures)} failures; "
          f"{len(not_auto)} link-only or non-synced files; "
          f"{len(incomplete)} presentation limitations.")


if __name__ == "__main__":
    main()
