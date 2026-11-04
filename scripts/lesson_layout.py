"""Lesson-centred Teaching & Planning presentation, sourced from Drive and the Learning Events Register.

The Google Drive source remains read-only. Matching uses verified deck IDs, not
title similarity. Unknown or older slides remain available in a separate section.
"""
import html
import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote

from sync_media import api_json, esc

REGISTER_ID = "16Wky3Pb8fNWfaMRnJXW7gYQcxP4G1tI5eTJoc1fg9LY"
SOURCE_PLANS = "02 Full Lesson Plans"
SLIDES_FOLDER = "03 Lesson Slides"
REDACTED_RE = re.compile(r"(?:\bredacted\b|\bredaction\b)", re.IGNORECASE)

# Slide-deck alignments verified against the source presentations and plans.
# An omitted deck is NOT assumed to match merely because its number is the same.
SLIDE_MAP = {
    (1, 1): ["1C3Ip1Mq-30MtH1R1mx0GfeGuH38xQ0yMBLfbhDIsV_E"],
    (2, 1): ["1C3Ip1Mq-30MtH1R1mx0GfeGuH38xQ0yMBLfbhDIsV_E"],
    (1, 2): ["17CZjb2YHoL3yU5Hp1ijIYjsFmQy9gXG_epuHHj_5RQ4"],
    (2, 2): ["17CZjb2YHoL3yU5Hp1ijIYjsFmQy9gXG_epuHHj_5RQ4"],
    (1, 3): ["1e2sG29x8fAS6p8ptw-mVSjMoRBmEeHX5_6zz95os5Es"],
    (2, 3): ["1XjY2r3Jqh4HZW95WYZnBTu_sGXV75JYxUS6G-K8Izms"],
    (1, 4): ["1U4yjqctdRGABqQ7y2tPu5yMvdgoyinHpGxokSKBU7WA"],
    (2, 4): ["1Z2WWvxwvcxl5tT34Up_WGXHzG6-yEEwARtEoYfLL3jk"],
    (1, 5): ["1V9FaElXcY_K-ZprvRc-JSvwm_uH9Gh92SlJTMGBOp5E"],
    (2, 5): ["1V9FaElXcY_K-ZprvRc-JSvwm_uH9Gh92SlJTMGBOp5E"],
    (1, 6): ["1OJ2d2lITwTzGm85KQRyHvT4YGswxth7-tTViUrSnujk"],
    (2, 6): ["11wfXajVpNvHTWpEDPIga-3n-HRd3sRcpVkrISm4IpmY"],
    (1, 7): ["1ZJDcdOiL-kspemXO_KJz8DczMiHh2rmGs8LMc6CT6qs"],
    # No verified aligned deck for Science 2 Lesson 7.
    # The earlier "Parallel circuits" deck differs substantially from Lesson 8.
    (1, 9): ["1GWqtOyiIkaw86QQ0UGmK3HeJz2LGRSPvtfTt6TB1Nps"],
    (2, 9): ["1GWqtOyiIkaw86QQ0UGmK3HeJz2LGRSPvtfTt6TB1Nps"],
    (1, 10): ["1lMHs5F0caDHSG0BM4mrCDbUB3vI9FXA2q_rmeVAP7zc"],
    (2, 10): ["1lMHs5F0caDHSG0BM4mrCDbUB3vI9FXA2q_rmeVAP7zc"],
    # Old Lesson 11 deck describes a Te Uku visit, not the current beach investigation.
    (1, 12): ["1XTurDj4qJXAgiNkQE0imlB2UjUV6QfhZLTqTiK-yr3o"],
    (2, 12): ["1XTurDj4qJXAgiNkQE0imlB2UjUV6QfhZLTqTiK-yr3o"],
}

WORKSHEETS = {
    2: [("1S4ltFg4bRMT24MQe8iW08Ho5wcVjZ1BxjDy94Yrjr3k", "Charge worksheet")],
    3: [("1RLLgkeHZVxaDZ-BbiTNoGDPGy48tdgnKHBIHL0sElt4", "Quick check")],
    5: [("1ULcE4YEdpnercpaxGNDQH6HXjjN9EF_K", "Crossword"),
        ("1teY5N3MyiXw0NohV1uQ75jZc0R6vfoGN", "Investigation")],
    6: [("1teY5N3MyiXw0NohV1uQ75jZc0R6vfoGN", "Lesson 5 investigation, continued")],
    7: [("1wsc9mqtR6l4aPrKHmSAYy7c3nZUbdZNn6TzRWo3p5Xo", "Connection worksheet")],
    8: [("1rFzdazULtdSoH-Vady3IXnr4T-3bxI5ykCUEyVkMBRI", "Switching worksheet")],
}

EVIDENCE = {
    (1, 5): [
        ("1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq",
         "Crossword sample", "Anonymised retrieval work on earlier electricity ideas. It is not evidence of graph interpretation."),
        ("1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp",
         "Investigation page 1", "Anonymised investigation page used to review measurement recording. No graph or analysis page is provided here."),
    ],
}
UNALLOCATED_EVIDENCE = [
    ("1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM",
     "Lesson 3 worksheet sample", "The filename does not establish whether the work is from Science 1 or Science 2."),
    ("152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB",
     "Lesson 4 exercise-book sample", "The filename does not identify which of the two Year 10 groups produced it."),
]

HIGHLIGHTS = {
    (2, 2): "Conceptual progression from pepeha and particle models to explaining static electricity, with reflection on unfinished written work.",
    (1, 8): "An investigation of independently switched parallel lamp branches, practical checking and electrical-protection reasoning.",
    (1, 12): "An open-ended design assessment requiring circuit planning, testing, troubleshooting and evidence-based explanation.",
}

MISMATCH_NOTES = {
    "1CuXasV-fP5S_sl_1fMIolE4fQ-mETs3NQqbEvV1L8FA":
        "Earlier Lesson 8 deck about general parallel circuits. It is not the current independently switched lamps and electrical protection lesson.",
    "1U1vwrIVj9f9rzXcr_v7D_uH0vPDNTtnITaig0V9TYU0":
        "Earlier Lesson 11 deck about Te Uku wind-farm investigations. The current class plans are for a beach-based generator investigation.",
}
PLAN_RE = re.compile(r"^Lesson\s*0?(\d{1,2})\s*[:.\-–]?\s*(.*)", re.I)


def exclude_from_website(entry):
    """Skip explicitly labelled redacted copies of observations; leave Drive untouched."""
    return (
        entry.get("path", [""])[0] == "02 Observations"
        and entry.get("mimeType") != "application/vnd.google-apps.folder"
        and bool(REDACTED_RE.search(entry.get("name", "")))
    )


def date_text(value):
    raw = str(value or "").strip()
    try:
        return datetime.strptime(raw, "%d/%m/%Y").strftime("%-d %b %Y")
    except (ValueError, TypeError):
        return raw if raw and raw.casefold() != "tbc" else "Date to confirm"


def current_events(session):
    range_key = quote("'Learning Events'!A6:O250", safe="")
    response = api_json(
        session,
        f"https://sheets.googleapis.com/v4/spreadsheets/{REGISTER_ID}/values/{range_key}",
        params={"valueRenderOption": "FORMATTED_VALUE"},
    )
    rows = response.get("values", [])
    events = {}
    for row in rows[1:]:
        row = list(row) + [""] * max(0, 15 - len(row))
        group = re.search(r"\b(?:Y(?:ear)?\s*10)\s+Science\s+([12])\b", row[4], re.I)
        lesson = PLAN_RE.match(row[5].strip())
        if not group or not lesson:
            continue
        status = row[1].strip().casefold()
        if status.startswith("not delivered"):
            state = "Not delivered"
        elif status == "recorded":
            state = "Completed"
        elif status == "planned":
            state = "Planned"
        else:
            state = "Unconfirmed"
        key = (int(group.group(1)), int(lesson.group(1)))
        candidate = {
            "status": state, "date": date_text(row[2]),
            "title": lesson.group(2).strip(),
            "learning": row[8], "learning_evidence": row[11],
            "evaluation": row[12], "entry": row[0],
        }
        previous = events.get(key)
        priority = {"Completed": 3, "Not delivered": 2, "Planned": 1, "Unconfirmed": 0}
        if not previous or priority[state] >= priority.get(previous["status"], 0):
            events[key] = candidate
    if len(events) < 20:
        raise RuntimeError("Learning Events Register returned too few year-group lessons; refusing to infer delivery statuses")
    return events


def lesson_number(entry):
    match = PLAN_RE.match(entry.get("name", ""))
    return int(match.group(1)) if match else None


def lesson_group(entry):
    joined = "/".join(entry.get("path", []))
    match = re.search(r"Y10\s+Science\s+([12])", joined, re.I)
    return int(match.group(1)) if match else None


def lesson_plan_entry(entry):
    return (SOURCE_PLANS in entry.get("path", [])
            and entry.get("mimeType") == "application/vnd.google-apps.document"
            and lesson_group(entry) in (1, 2)
            and lesson_number(entry) is not None)


def get_link(entry, linked, label, css=""):
    if not entry:
        return '<span class="no-resource">Not available</span>'
    target = linked.get(entry["id"], {}).get("page")
    if not target:
        target = entry.get("webViewLink") or (
            "https://drive.google.com/file/d/" + entry["id"] + "/view"
        )
    extra = ' target="_blank" rel="noopener noreferrer"' if target.startswith("https://") else ""
    css_attr = f' class="{esc(css)}"' if css else ""
    return f'<a{css_attr} href="{esc(target)}"{extra}>{esc(label)}</a>'


def make_resources(resources, by_id, linked):
    if not resources:
        return '<span class="no-resource">—</span>'
    output = []
    for fid, label in resources:
        entry = by_id.get(fid)
        if entry:
            output.append(get_link(entry, linked, label))
    return '<span class="lesson-links">' + " · ".join(output) + "</span>" if output else '<span class="no-resource">—</span>'


def lesson_title(group, number, entry, events):
    event = events.get((group, number), {})
    if event.get("title"):
        return re.sub(r"\s+[–—-]\s+Y10.*$", "", event["title"]).strip()
    name = entry.get("name", "")
    m = PLAN_RE.match(name)
    result = m.group(2) if m else name
    return re.split(r"\s+-\s+Y10\s+Science", result, flags=re.I)[0].strip()


def plan_page_info(entry, events):
    if not lesson_plan_entry(entry):
        return None
    group, number = lesson_group(entry), lesson_number(entry)
    event = events.get((group, number), {})
    title = f"Lesson {number:02}: {lesson_title(group, number, entry, events)}"
    caption = (
        f"Year 10 Science {group} · {event.get('date', 'Date to confirm')}"
        f" · {event.get('status', 'Unconfirmed')}"
    )
    return title, caption


def strip_duplicate_title(markup, number):
    return re.sub(
        rf"^\s*<h3>\s*Lesson\s*0?{number}\s*[:.\-–].*?</h3>\s*",
        "", markup, count=1, flags=re.I | re.S
    )


def slide_page_info(entry, events):
    """Short slide headings without asserting an unverified plan match."""
    matched = [key for key, ids in SLIDE_MAP.items() if entry["id"] in ids]
    number = lesson_number(entry)
    if len(matched) == 1:
        group, number = matched[0]
        lesson = f"Lesson {number:02}: {lesson_title(group, number, entry, events)}"
        event = events.get((group, number), {})
        info = (f"Year 10 Science {group} · {event.get('date', 'Date to confirm')}"
                f" · {event.get('status', 'Unconfirmed')} · Teaching slides")
        return lesson, info
    if len(matched) > 1:
        group, number = matched[0]
        lesson = f"Lesson {number:02}: {lesson_title(group, number, entry, events)}"
        return lesson, "Shared teaching slides · Check each class's separate lesson status"
    if number:
        label = re.sub(r"^Lesson\s*0?\d+\s*[-:]\s*", "", entry["name"])
        return f"Lesson {number:02}: {label}", "Other slide deck · Not matched to a current class lesson"
    return entry["name"], "Teaching presentation · Plan alignment not confirmed"


def resource_detail(entry, linked, by_id):
    return get_link(entry, linked, "Open")


def highlighted_panel(plans, events, linked):
    cells = []
    for group, number in ((2, 2), (1, 8), (1, 12)):
        entry = plans.get((group, number))
        if not entry:
            continue
        event = events.get((group, number), {})
        label = lesson_title(group, number, entry, events)
        status = event.get("status", "Unconfirmed")
        date = event.get("date", "Date to confirm")
        cells.append(
            f'<article class="highlight-plan"><p class="highlight-meta">'
            f'Year 10 Science {group} · Lesson {number:02} · {esc(date)} '
            f'<span class="delivery-status {status.lower().replace(" ", "-")}">{esc(status)}</span></p>'
            f'<h4>{esc(label)}</h4><p>{esc(HIGHLIGHTS[group, number])}</p>'
            f'{get_link(entry, linked, "Read lesson plan", "lesson-action")}</article>'
        )
    return (
        '<section class="lesson-featured" aria-label="Highlighted lesson plans">'
        '<div class="teaching-section-heading"><h3>Highlighted lesson plans</h3>'
        '<p>Three selected plans illustrating a range of teaching approaches. '
        'Delivery status is shown for each.</p></div>'
        '<div class="highlight-grid">' + "".join(cells) + "</div></section>"
    )


def lesson_table(group, plans, events, by_id, linked):
    rows = []
    for num in range(1, 13):
        key = (group, num)
        plan = plans.get(key)
        event = events.get(key, {})
        status = event.get("status", "Unconfirmed")
        date = event.get("date", "Date to confirm")
        title = lesson_title(group, num, plan or {"name": f"Lesson {num}"}, events)
        highlight = ' <span class="featured-mark" title="Selected lesson plan">Selected</span>' if key in HIGHLIGHTS else ""
        plan_html = get_link(plan, linked, "Plan") if plan else '<span class="no-resource">—</span>'
        slides = make_resources([(fid, "Slides") for fid in SLIDE_MAP.get(key, [])], by_id, linked)
        worksheets = make_resources(WORKSHEETS.get(num, []), by_id, linked)
        evidence = EVIDENCE.get(key, [])
        evhtml = []
        for fid, label, description in evidence:
            entry = by_id.get(fid)
            if entry and status == "Completed":
                evhtml.append(
                    f'<div class="lesson-evidence-link">{get_link(entry, linked, label)}'
                    f'<p>{esc(description)}</p></div>'
                )
        if not evhtml:
            evhtml = ['<span class="no-resource">No class-specific file linked</span>'
                      if status == "Completed" else '<span class="no-resource">Not yet delivered</span>']
        if num == 8:
            slides += '<small class="alignment-note">Earlier parallel-circuit slides do not match this revised plan.</small>'
        if num == 11:
            slides += '<small class="alignment-note">Earlier Te Uku slides do not match the current beach investigation.</small>'
        if group == 2 and num == 7:
            slides += '<small class="alignment-note">Science 1 deck is not labelled for this class.</small>'
        if num in (3, 4) and status == "Completed":
            evhtml.append('<small class="alignment-note">Lesson evidence requiring class identification is listed below.</small>')
        rows.append(
            f'<tr id="science-{group}-lesson-{num}"><th scope="row">'
            f'<span class="lesson-number">Lesson {num:02}</span><strong>{esc(title)}</strong>{highlight}</th>'
            f'<td><span class="delivery-status {status.lower().replace(" ", "-")}">{esc(status)}</span>'
            f'<span class="lesson-date">{esc(date)}</span></td>'
            f'<td>{plan_html}</td><td>{slides}</td><td>{worksheets}</td>'
            f'<td>{"".join(evhtml)}</td></tr>'
        )
    return (
        f'<section class="lesson-section" id="science-{group}">'
        f'<div class="teaching-section-heading"><h3>Year 10 Science {group}</h3>'
        '<p>Lesson sequence with planned or recorded delivery, supporting resources and evidence.</p></div>'
        '<div class="lesson-table-scroll" role="region" tabindex="0" '
        f'aria-label="Year 10 Science {group} lesson sequence">'
        '<table class="lesson-table"><thead><tr><th>Lesson</th>'
        '<th>Date / status</th><th>Plan</th><th>Slides</th><th>Worksheet</th>'
        '<th>Evidence</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div></section>"
    )


def other_materials(entries, by_id, linked):
    def group(title, items, intro=""):
        if not items:
            return ""
        content = f"<p>{esc(intro)}</p>" if intro else ""
        content += '<ul class="resource-list">' + "".join(
            f'<li>{get_link(e, linked, short_name(e))}'
            + (f'<small>{esc(MISMATCH_NOTES[e["id"]])}</small>' if e["id"] in MISMATCH_NOTES else "")
            + "</li>" for e in sorted(items, key=lambda x: x["name"].casefold())
        ) + "</ul>"
        return f'<div class="supporting-group"><h4>{esc(title)}</h4>{content}</div>'

    matched = {fid for ids in SLIDE_MAP.values() for fid in ids}
    unmatched_slides = [
        x for x in entries if x.get("id") not in matched and SLIDES_FOLDER in x.get("path", [])
    ]
    plans_history = [x for x in entries if "99 Superseded Plans and Resources" in x.get("path", [])]
    older = [x for x in entries if x in unmatched_slides and x["id"] in MISMATCH_NOTES]
    unassigned_slides = [x for x in unmatched_slides if x not in older]
    lesson_attached = set()
    lesson_attached.update(fid for pair in WORKSHEETS.values() for fid, _ in pair)
    lesson_attached.update(fid for vals in EVIDENCE.values() for fid, _, _ in vals)
    lesson_attached.update(fid for fid, _, _ in UNALLOCATED_EVIDENCE)
    ignore = matched | lesson_attached
    ignore.update(x["id"] for x in plans_history)
    ignore.update(x["id"] for x in unmatched_slides)
    other_files = [x for x in entries if x.get("id") not in ignore
                   and not lesson_plan_entry(x)]
    sections = [
        group("Older slide decks, not aligned with the current plans", older,
              "These decks are retained for context, not assigned to a current class lesson."),
        group("Slides awaiting alignment", unassigned_slides,
              "New or other presentations remain accessible but are not linked to a lesson without checking their contents."),
        group("Other teaching and planning resources", other_files),
    ]
    return (
        '<details class="planning-history"><summary>Other teaching resources and slide alignment</summary>'
        + "".join(sections) + "</details>"
        '<details class="planning-history"><summary>Planning history: superseded versions</summary>'
        '<p>These earlier documents show how the electricity unit evolved. Current lesson plans and '
        'class-specific sequences above take precedence. In particular, household-wiring content was '
        'separated into Lessons 7 and 8, and the previous general parallel-circuit material is not '
        'treated as the revised Lesson 8.</p>'
        + group("Earlier plans and worksheets", plans_history) + "</details>"
    )


def short_name(entry):
    text = entry["name"]
    text = re.sub(r"\s*-\s*Y10 Science [12]\s*-\s*Full Lesson Plan.*", "", text, flags=re.I)
    text = re.sub(r"\s*\[Highlighted\]", "", text, flags=re.I)
    text = re.sub(r"^Lesson\s*0?(\d+)\s*[-:]\s*", lambda m: f"Lesson {int(m.group(1)):02}: ", text)
    return text


def unidentified_evidence(by_id, linked):
    items = []
    for fid, title, note in UNALLOCATED_EVIDENCE:
        entry = by_id.get(fid)
        if entry:
            items.append(
                f'<li>{get_link(entry, linked, title)}'
                f'<p>{esc(note)}</p></li>'
            )
    if not items:
        return ""
    return (
        '<section class="evidence-attribution"><h3>Evidence awaiting class identification</h3>'
        '<p>The following samples are associated with Lesson 3 or 4, but their filenames do not '
        'identify the Year 10 group. They are not assigned to either group as class-specific evidence.</p>'
        '<ul>' + "".join(items) + "</ul></section>"
    )


def teaching_body(entries, linked, events):
    by_id = {x["id"]: x for x in entries}
    plans = {(lesson_group(x), lesson_number(x)): x for x in entries if lesson_plan_entry(x)}
    content = (
        '<div class="teaching-dashboard">'
        '<p class="teaching-intro">Follow each class from planning through delivery and evidence. '
        'Dates and delivery statuses come from the Learning Events Register, not from the existence '
        'of a lesson plan. Future plans are not presented as completed teaching.</p>'
        '<nav class="lesson-jump" aria-label="Lesson sequence navigation">'
        '<a href="#science-1">Year 10 Science 1</a><a href="#science-2">Year 10 Science 2</a>'
        '<a href="learning-events.html">Learning events register</a></nav>'
        + highlighted_panel(plans, events, linked)
        + lesson_table(1, plans, events, by_id, linked)
        + lesson_table(2, plans, events, by_id, linked)
        + unidentified_evidence(by_id, linked)
        + other_materials(entries, by_id, linked)
        + "</div>"
    )
    return content
