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

OBSERVATION_FOLDER = "02 Observations"
PDF_MIME = "application/pdf"
# Final PDFs appear on the website. Editable observation forms remain in Drive.
FINISHED_FEEDBACK_PDFS = {
    1: "1rOJLp3MWNZhUypi0VtDrLXwgPv7uGsQP",
    2: "11NQ6VYDJlr4P8Cwkmu_gkJD32W851l7I",
    3: "1JjWQBiCD4yL_brNoUQ1kPYtHbXHsvjlH",
    4: "1LkWOx87OLbR5Dcz1ZX8NtHiCnZfR5QwB",
    5: "1y_jz2PzsB4qBSlLmwHwqXJbETHGU1pNi",
}


def is_editable_observation_form(entry):
    """Exclude editable forms, but never exclude final PDFs."""
    if entry.get("id") == "1I8m_oCzHA_d5RXyN725xnNHgRy8tgK-W":
        return True  # Superseded Week 3 export; publish the completed PDF instead.
    folder_path = entry.get("folderPath", [])
    if not folder_path or folder_path[0] != OBSERVATION_FOLDER:
        return False
    return (
        re.match(r"^\s*observation\s+form\b", entry.get("name", ""), re.I)
        is not None and entry.get("mimeType") != PDF_MIME
    )


def completed_feedback_map(excluded, linked):
    """Redirect old editable-form links to completed PDFs if one exists."""
    redirects = {}
    for entry in excluded:
        if not is_editable_observation_form(entry):
            continue
        fid = FINISHED_FEEDBACK_PDFS.get(_week(entry))
        page = linked.get(fid, {}).get("page") if fid else None
        if page:
            redirects[entry["id"]] = page
    return redirects


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


def _feedback_voice(title, anchor, items, linked):
    links = "".join(_resource(entry, linked) for entry in items)
    return (
        f'<section class="feedback-voice" id="{anchor}"><h4>{esc(title)}</h4>'
        + (f'<ul class="observation-links">{links}</ul>' if links else '<p>No records available.</p>')
        + '</section>'
    )


def _student_scans(entry, linked):
    page = linked.get(entry["id"], {}).get("page")
    if not page:
        return ""
    asset = "assets/drive/1eBxsYyTaPqJJ4byG3CSqaxWeI3w4fMfM/Student-Voice---Exit-Forms-Redacted-.pdf"
    return (
        '<details class="student-scans"><summary>Full feedback forms (names redacted)</summary>'
        f'<p><a href="{esc(asset)}" target="_blank" rel="noopener">Open full PDF</a>'
        f' · <a href="{esc(page)}">Open evidence page</a></p>'
        f'<iframe class="pdf-preview" loading="lazy" title="Full redacted student feedback forms" src="{esc(asset)}"></iframe>'
        '</details>'
    )


def _student_voice(items, linked):
    scans = "".join(_student_scans(entry, linked) for entry in items)
    return (
        "<section class=\"feedback-voice\" id=\"student-voice\"><h4>Student Voice</h4><p><strong>18 of 18 students responded</strong> in one Year 10 science class. All 18 said they received the help they needed when they struggled, and 17 said the lessons helped them understand circuits.</p><p>Two students wrote that I gave them <em>mana</em>. Their words stayed with me and made me reflect on how I can support students without taking over. In a separate response, one student described being shown what to do and then having the chance to do it themselves.</p><figure style=\"margin:1.25rem 0\"><figcaption><strong>Exit questionnaire ratings</strong> · number of students (18 per question)</figcaption><p style=\"display:flex;flex-wrap:wrap;gap:.5rem 1rem\"><span><span aria-hidden=\"true\" style=\"color:#283593;-webkit-text-stroke:.45px #334155\">■</span> Strongly agree</span><span><span aria-hidden=\"true\" style=\"color:#00796b;-webkit-text-stroke:.45px #334155\">■</span> Agree</span><span><span aria-hidden=\"true\" style=\"color:#e2e8f0;-webkit-text-stroke:.45px #334155\">■</span> Neutral</span><span><span aria-hidden=\"true\" style=\"color:#f5a3a8;-webkit-text-stroke:.45px #334155\">■</span> Disagree</span><span><span aria-hidden=\"true\" style=\"color:#8b1e3f;-webkit-text-stroke:.45px #334155\">■</span> Strongly disagree</span><span><span aria-hidden=\"true\" style=\"color:#f7c65e;-webkit-text-stroke:.45px #334155\">■</span> Not sure</span></p><div style=\"margin:.65rem 0\"><div>1. The lessons helped me understand how electrical circuits work.</div><div role=\"img\" aria-label=\"1. The lessons helped me understand how electrical circuits work. Responses: 5 Strongly agree, 12 Agree, 1 Neutral, 0 Disagree, 0 Strongly disagree, 0 Not sure\" style=\"display:flex;overflow:hidden;border-radius:5px\"><span aria-hidden=\"true\" style=\"flex:5 1 0;min-width:0;text-align:center;color:#ffffff;background:#283593;font-weight:600;font-size:.875rem;line-height:1.7rem\">5</span><span aria-hidden=\"true\" style=\"flex:12 1 0;min-width:0;text-align:center;color:#ffffff;background:#00796b;font-weight:600;font-size:.875rem;line-height:1.7rem\">12</span><span aria-hidden=\"true\" style=\"flex:1 1 0;min-width:0;text-align:center;color:#172033;background:#e2e8f0;font-weight:600;font-size:.875rem;line-height:1.7rem\">1</span></div></div><div style=\"margin:.65rem 0\"><div>2. The models and demonstrations helped me understand ideas that were difficult to imagine.</div><div role=\"img\" aria-label=\"2. The models and demonstrations helped me understand ideas that were difficult to imagine. Responses: 7 Strongly agree, 6 Agree, 5 Neutral, 0 Disagree, 0 Strongly disagree, 0 Not sure\" style=\"display:flex;overflow:hidden;border-radius:5px\"><span aria-hidden=\"true\" style=\"flex:7 1 0;min-width:0;text-align:center;color:#ffffff;background:#283593;font-weight:600;font-size:.875rem;line-height:1.7rem\">7</span><span aria-hidden=\"true\" style=\"flex:6 1 0;min-width:0;text-align:center;color:#ffffff;background:#00796b;font-weight:600;font-size:.875rem;line-height:1.7rem\">6</span><span aria-hidden=\"true\" style=\"flex:5 1 0;min-width:0;text-align:center;color:#172033;background:#e2e8f0;font-weight:600;font-size:.875rem;line-height:1.7rem\">5</span></div></div><div style=\"margin:.65rem 0\"><div>3. If I struggled, the teacher gave me the help I needed to continue.</div><div role=\"img\" aria-label=\"3. If I struggled, the teacher gave me the help I needed to continue. Responses: 10 Strongly agree, 8 Agree, 0 Neutral, 0 Disagree, 0 Strongly disagree, 0 Not sure\" style=\"display:flex;overflow:hidden;border-radius:5px\"><span aria-hidden=\"true\" style=\"flex:10 1 0;min-width:0;text-align:center;color:#ffffff;background:#283593;font-weight:600;font-size:.875rem;line-height:1.7rem\">10</span><span aria-hidden=\"true\" style=\"flex:8 1 0;min-width:0;text-align:center;color:#ffffff;background:#00796b;font-weight:600;font-size:.875rem;line-height:1.7rem\">8</span></div></div><div style=\"margin:.65rem 0\"><div>4. There was enough challenge for me, including when I finished early.</div><div role=\"img\" aria-label=\"4. There was enough challenge for me, including when I finished early. Responses: 3 Strongly agree, 11 Agree, 3 Neutral, 0 Disagree, 0 Strongly disagree, 1 Not sure\" style=\"display:flex;overflow:hidden;border-radius:5px\"><span aria-hidden=\"true\" style=\"flex:3 1 0;min-width:0;text-align:center;color:#ffffff;background:#283593;font-weight:600;font-size:.875rem;line-height:1.7rem\">3</span><span aria-hidden=\"true\" style=\"flex:11 1 0;min-width:0;text-align:center;color:#ffffff;background:#00796b;font-weight:600;font-size:.875rem;line-height:1.7rem\">11</span><span aria-hidden=\"true\" style=\"flex:3 1 0;min-width:0;text-align:center;color:#172033;background:#e2e8f0;font-weight:600;font-size:.875rem;line-height:1.7rem\">3</span><span aria-hidden=\"true\" style=\"flex:1 1 0;min-width:0;text-align:center;color:#172033;background:#f7c65e;font-weight:600;font-size:.875rem;line-height:1.7rem\">1</span></div></div><div style=\"margin:.65rem 0\"><div>5. I felt comfortable asking questions, making mistakes and sharing my ideas.</div><div role=\"img\" aria-label=\"5. I felt comfortable asking questions, making mistakes and sharing my ideas. Responses: 10 Strongly agree, 4 Agree, 3 Neutral, 0 Disagree, 0 Strongly disagree, 1 Not sure\" style=\"display:flex;overflow:hidden;border-radius:5px\"><span aria-hidden=\"true\" style=\"flex:10 1 0;min-width:0;text-align:center;color:#ffffff;background:#283593;font-weight:600;font-size:.875rem;line-height:1.7rem\">10</span><span aria-hidden=\"true\" style=\"flex:4 1 0;min-width:0;text-align:center;color:#ffffff;background:#00796b;font-weight:600;font-size:.875rem;line-height:1.7rem\">4</span><span aria-hidden=\"true\" style=\"flex:3 1 0;min-width:0;text-align:center;color:#172033;background:#e2e8f0;font-weight:600;font-size:.875rem;line-height:1.7rem\">3</span><span aria-hidden=\"true\" style=\"flex:1 1 0;min-width:0;text-align:center;color:#172033;background:#f7c65e;font-weight:600;font-size:.875rem;line-height:1.7rem\">1</span></div></div><p><small>No disagreement responses were recorded. Where two ratings were marked, the lower rating was used.</small></p></figure><p>The responses about models and demonstrations were more mixed. In my next placement, I want to ask students to explain what a model helped them understand and allow more time to finish the main practical task, with an extension ready for those who finish early. This is feedback about students’ experiences and perceived learning, alongside the evidence of what they produced in class.</p>"
        + ('<p>The full scans, with names redacted, are included at the bottom of this section '
           'for anyone who would like to see the original responses.</p>' if scans else '')
        + scans
        + '</section>'
    )


def observations_body(entries, linked):
    """Three grounded sections, with weekly forms in numeric week order."""
    items = [
        e for e in entries
        if e["mimeType"] != "application/vnd.google-apps.folder"
        and not is_editable_observation_form(e)
    ]
    general, others, feedback, forms, visits, remaining, student_forms = [], [], [], [], [], [], []
    for entry in items:
        name = entry["name"].casefold().strip()
        folders = " / ".join(entry.get("folderPath", [])).casefold()
        if entry["id"] == "1eBxsYyTaPqJJ4byG3CSqaxWeI3w4fMfM":
            if entry.get("mimeType") == PDF_MIME:
                student_forms.append(entry)
        elif name.startswith("general observations"):
            general.append(entry)
        elif name.startswith("observations of others") or (
            "my observations of others" in folders
        ):
            others.append(entry)
        elif "observation form" in name:
            if entry.get("mimeType") == PDF_MIME:
                feedback.append(entry)
        elif "mentor teacher feedback" in name:
            if entry.get("mimeType") == PDF_MIME:
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
        + '<section class="portfolio-source-group observation-group" id="feedback-on-my-teaching">'
        + '<h3>Feedback on My Teaching</h3>'
        + '<nav class="observation-jump" aria-label="Feedback sources">'
        + '<a href="#mentor-teacher-voice">Mentor Teacher</a>'
        + '<a href="#student-voice">Student Voice</a>'
        + '<a href="#evaluative-visitor-voice">Evaluative Visitor</a></nav>'
        + _feedback_voice("Mentor Teacher", "mentor-teacher-voice", feedback, linked)
        + _student_voice(student_forms, linked)
        + _feedback_voice("Evaluative Visitor", "evaluative-visitor-voice", visits, linked)
        + (_feedback_voice("Additional feedback", "additional-feedback", remaining, linked) if remaining else "")
        + '</section>'
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
