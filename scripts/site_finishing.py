"""Presentation-only improvements for ProfEx portfolio pages.

Everything here reads the synced Drive inventory; it does not change the
original Google Docs, Slides, Sheets or files.
"""
import html
import re

ABOUT_ID = "1LRJcZrLnGMH9hDYmw1PISopoeKKAyErfI3Z3btEaQ_o"
REFERENCES_ID = "1gCiC40LUq4HybRawE7Qs-sgRQLPXe3NJ0wqyzgh5oIs"
PEPEHA_SLIDES_ID = "1--Jd9sCrxHqVdq6nyEM2wYsCxzOizEQZ1xov7zrHRdw"
DIRECT_PAGES = {"about.html": ABOUT_ID, "references.html": REFERENCES_ID}

TAG_RE = re.compile(r"<[^>]+>")
IMAGE_RE = re.compile(
    r'(<img\b[^>]*\balt=")Illustration from the source document(")', re.I | re.S
)
PARAGRAPH_RE = re.compile(r"<p(?:\s[^>]*)?>(.*?)</p>", re.I | re.S)


def esc(value):
    return html.escape(str(value), quote=True)


def direct_document_markup(markup, page):
    """Show the entire source document, without an intermediate file list."""
    if page == "about.html":
        markup = re.sub(
            r"^\s*<h3>\s*TEACHER STATEMENT AND PEPEHA\s*</h3>\s*",
            "", markup, flags=re.I,
        )
    elif page == "references.html":
        markup = re.sub(
            r"^\s*<h3>\s*Portfolio References\s*</h3>\s*",
            "", markup, flags=re.I,
        )
    return '<article class="native-reflection"><div class="reflection-prose">' + markup + '</div></article>'


def _week(entry):
    found = re.search(r"\bweek\s*0?(\d+)\b", entry["name"], re.I)
    return int(found.group(1)) if found else 999


def _pretty(entry):
    name = entry["name"].strip()
    week = _week(entry)
    if name.casefold().startswith("observation form") and week != 999:
        return f"Week {week}: Observation form"
    if name.casefold().startswith("mentor teacher feedback") and week != 999:
        return f"Week {week}: Mentor teacher feedback"
    return re.sub(r"\.(?:pdf|docx?)$", "", name, flags=re.I)


def _resource(entry, linked):
    page = linked.get(entry["id"], {}).get("page")
    if not page:
        # No dead or external Drive links in this navigation.
        return ""
    return f'<li><a href="{esc(page)}">{esc(_pretty(entry))}</a></li>'


def _group(title, anchor, entries, linked, subsections=None):
    out = (
        f'<section class="portfolio-source-group observation-group" id="{anchor}">'
        f'<h3>{esc(title)}</h3>'
    )
    if subsections:
        for subtitle, items in subsections:
            if items:
                out += f'<h4>{esc(subtitle)}</h4>'
                out += '<ul class="observation-links">'
                out += "".join(_resource(e, linked) for e in items)
                out += '</ul>'
    elif entries:
        out += '<ul class="observation-links">'
        out += "".join(_resource(e, linked) for e in entries)
        out += '</ul>'
    else:
        out += '<p>Records will appear here when available.</p>'
    return out + "</section>"


def observations_body(entries, linked):
    """Three grounded sections, with weekly forms in numeric week order."""
    items = [e for e in entries if e["mimeType"] != "application/vnd.google-apps.folder"]
    general, others, feedback, forms, visits, remaining = [], [], [], [], [], []
    for entry in items:
        name = entry["name"].casefold().strip()
        folders = " / ".join(entry.get("folderPath", [])).casefold()
        if name.startswith("general observations"):
            general.append(entry)
        elif name.startswith("observations of others") or (
            "my observations of others" in folders
        ):
            others.append(entry)
        elif "observation form" in name:
            forms.append(entry)
        elif "mentor teacher feedback" in name:
            feedback.append(entry)
        elif "evaluative visit" in name or "report" in name:
            visits.append(entry)
        else:
            remaining.append(entry)

    general.sort(key=lambda e: e["name"].casefold())
    others.sort(key=lambda e: e["name"].casefold())
    forms.sort(key=lambda e: (_week(e), e["name"].casefold()))
    feedback.sort(key=lambda e: (_week(e), e["name"].casefold()))
    visits.sort(key=lambda e: e["name"].casefold())

    return (
        '<nav class="observation-jump" aria-label="Observation sections">'
        '<a href="#general-school-observations">General School Observations</a>'
        '<a href="#observations-of-others">Observations of Others</a>'
        '<a href="#feedback-on-my-teaching">Feedback on My Teaching</a>'
        '</nav><div class="portfolio-sources observation-sections">'
        + _group("General School Observations", "general-school-observations", general, linked)
        + _group("Observations of Others", "observations-of-others", others, linked)
        + _group(
            "Feedback on My Teaching", "feedback-on-my-teaching", [], linked,
            [("Weekly observation forms", forms),
             ("Mentor teacher feedback", feedback),
             ("Evaluative visit report", visits),
             ("Additional feedback", remaining)]
        )
        + '</div>'
    )


def improve_image_alts(markup):
    """Use the source image's adjacent caption rather than generic alt text."""
    def resolve(match):
        offset = match.end()
        following = markup[offset:offset + 1100]
        paragraph = PARAGRAPH_RE.search(following)
        candidate = ""
        if paragraph and paragraph.start() < 180:
            candidate = html.unescape(TAG_RE.sub("", paragraph.group(1))).strip()
        if not candidate:
            context = markup[max(0, match.start()-900):match.start()]
            headings = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", context, re.I | re.S)
            if headings:
                candidate = "Visual material for " + html.unescape(TAG_RE.sub("", headings[-1]))
        if not candidate:
            candidate = "Photograph accompanying the portfolio evidence"
        candidate = re.sub(r"\s+", " ", candidate).strip()
        # Descriptive alt text should be concise even if the caption is long.
        candidate = candidate[:165].rsplit(" ", 1)[0] if len(candidate) > 165 else candidate
        return match.group(1) + esc(candidate) + match.group(2)
    return IMAGE_RE.sub(resolve, markup)
