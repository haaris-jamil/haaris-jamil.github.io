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
    # Keep each class linked to its own source presentation.
    (1, 1): ["1C3Ip1Mq-30MtH1R1mx0GfeGuH38xQ0yMBLfbhDIsV_E"],
    (2, 1): ["1NQKWj_qPn0mPEHvREX0jZXe-TkfAbrE3CcFxTVVAw7A"],
    (1, 2): ["1qJvgmaWPT999umENv4sFWJ687zA2kY7RsDJ4BeLY94w"],
    (2, 2): ["17CZjb2YHoL3yU5Hp1ijIYjsFmQy9gXG_epuHHj_5RQ4"],
    (1, 3): ["1e2sG29x8fAS6p8ptw-mVSjMoRBmEeHX5_6zz95os5Es"],
    (2, 3): ["1XjY2r3Jqh4HZW95WYZnBTu_sGXV75JYxUS6G-K8Izms"],
    (1, 4): ["1U4yjqctdRGABqQ7y2tPu5yMvdgoyinHpGxokSKBU7WA"],
    (2, 4): ["1Z2WWvxwvcxl5tT34Up_WGXHzG6-yEEwARtEoYfLL3jk"],
    (1, 5): ["1V9FaElXcY_K-ZprvRc-JSvwm_uH9Gh92SlJTMGBOp5E"],
    (2, 5): ["1yjMx57cY-kSoNlZtv4ub8jck8W3JD3vmF-ndFFRVjQQ"],
    (1, 6): ["1OJ2d2lITwTzGm85KQRyHvT4YGswxth7-tTViUrSnujk"],
    (2, 6): ["11wfXajVpNvHTWpEDPIga-3n-HRd3sRcpVkrISm4IpmY"],
    (1, 7): ["1ZJDcdOiL-kspemXO_KJz8DczMiHh2rmGs8LMc6CT6qs"],
    (2, 7): ["1OrKPfqtgA6aHBeDM9KMm4vTvH1xgpK2kM6lcZOLBYFw"],
    (1, 8): ["1CuXasV-fP5S_sl_1fMIolE4fQ-mETs3NQqbEvV1L8FA"],
    (2, 8): ["1vBdX4qXE4fsIRZxPG_dUAj6EmdNst3CYpt-65ekUSkY"],
    (1, 9): ["1GWqtOyiIkaw86QQ0UGmK3HeJz2LGRSPvtfTt6TB1Nps"],
    (2, 9): ["1oIHfVsDB8W_f8uGj24_UpK7VhZSY_EamiGoZHkrzaLA"],
    (1, 10): ["1lMHs5F0caDHSG0BM4mrCDbUB3vI9FXA2q_rmeVAP7zc"],
    (2, 10): ["1MJouYp3n6oSdZ9F7uswt2dmECSmSXvHP4b0O5VwiQ-s"],
    (1, 11): ["1U1vwrIVj9f9rzXcr_v7D_uH0vPDNTtnITaig0V9TYU0"],
    (2, 11): ["11yiHzBuwQewZ8GYUY_7pgt--H81w7SXhQMEi8PaR3Mg"],
    (1, 12): ["1XTurDj4qJXAgiNkQE0imlB2UjUV6QfhZLTqTiK-yr3o"],
    (2, 12): ["1WC98gjxSzZKtxDgR0FnWa0DxyUtrD2AOlob_JBjdckk"],
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

# These early uploads were collected across both Year 10 groups. Their
# original filenames are not evidence of class-level attribution.
WORKSHEET_OVERRIDES = {
    # Science 2 Lesson 6 was revised to a brief graphing demonstration
    # followed by the switched-outlet practical, not a continued worksheet.
    (2, 6): [
        ("1wsc9mqtR6l4aPrKHmSAYy7c3nZUbdZNn6TzRWo3p5Xo", "Connection worksheet")
    ],
}
LESSON_TITLE_OVERRIDES = {
    (2, 6): "Graphing demonstration and switched-outlet practical",
}
EVIDENCE_LABELS = {
    "1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM": "Worksheet samples",
    "152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB": "Exercise-book samples",
    "1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq": "Crossword samples",
    "1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp": "Investigation samples",
}
OTHER_LEARNING_EVENTS = [
    ("1cwCx4lvhLZ4176e-3mISxNyiCIq221i1lyo6t3dAMKo",
     "Year 13 Physics: Standing waves on a string", "23 Sep 2026"),
    ("1mlnEweXYo0_3sWmluA01U3haV_ZGnH3KEG-mfyYvstA",
     "Primary Science Club: Design and build model boats", "24 Sep 2026"),
    ("1ofp5jgQ1npOkrbHJrQXB_HmaY6jh0zVUiR3_ksWdn-4",
     "Year 13 Physics: Sound interference and wavelength", "2 Nov 2026"),
    ("1lDfi3t9_bDF90rkYx_it6Sm6RK-UIvIbDMviGUZeKYA",
     "Year 13 Physics: Electrolytic capacitors", "3 Nov 2026"),
]

MIXED_GROUP_EVIDENCE = {
    3: [
        ("1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM",
         "Lesson 3 worksheet sample",
         "Year 10 Lesson 3 worksheet samples."),
    ],
    4: [
        ("152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB",
         "Lesson 4 exercise-book sample",
         "Year 10 Lesson 4 exercise-book samples."),
    ],
    5: [
        ("1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq",
         "Lesson 5 crossword samples",
         "Year 10 Lesson 5 crossword samples."),
        ("1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp",
         "Lesson 5 investigation samples",
         "Year 10 Lesson 5 investigation samples."),
    ],
}
# Only independently confirmed class-specific student evidence is assigned to
# a single class. This PDF covers Science 1 Lesson 7, 4 November 2026.
CLASS_EVIDENCE = {
    (2, 6): [
        ("1LBd40BIKbAQCa27YuzySHHwMHT3vtDmO", "Student work samples", ""),
    ],
    (1, 7): [
        ("11bBS4D14yRgJM3WHFjdrosXkQupp2GuO",
         "Science 1 Lesson 7 student evidence",
         "Anonymised student work from Year 10 Science 1 on 4 November 2026. "
         "The samples do not establish that every learner achieved the outcome."),
    ],
}
MIXED_EVIDENCE_ID_SET = {
    fid for collections in MIXED_GROUP_EVIDENCE.values()
    for fid, _, _ in collections
}

HIGHLIGHTS = {
    (2, 2): "Conceptual progression from pepeha and particle models to explaining static electricity, with reflection on unfinished written work.",
    (1, 8): "An investigation of independently switched parallel lamp branches, practical checking and electrical-protection reasoning.",
    (1, 12): "An open-ended design assessment requiring circuit planning, testing, troubleshooting and evidence-based explanation.",
}

# Some decks are earlier resources for lessons still being revised. They remain
# accessible within their lesson, with no assumption that planning is final.
EARLIER_SLIDES = {
    "1U1vwrIVj9f9rzXcr_v7D_uH0vPDNTtnITaig0V9TYU0",
}
UNIT_OVERVIEW_ID = "10WsaDbhs--YacZgK5GeOJaW2RktNmefuKDce7lotR_w"

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
    if (group, number) in LESSON_TITLE_OVERRIDES:
        return LESSON_TITLE_OVERRIDES[(group, number)]
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
        if status == "Not delivered":
            # A missed timetable slot stays in the register and planning
            # history, never in the delivered/planned class lesson table.
            continue
        date = event.get("date", "Date to confirm")
        title = lesson_title(group, num, plan or {"name": f"Lesson {num}"}, events)
        highlight = ' <span class="featured-mark" title="Selected lesson plan">Selected</span>' if key in HIGHLIGHTS else ""
        plan_html = get_link(plan, linked, "Plan") if plan else '<span class="no-resource">—</span>'
        slides = make_resources(
            [(fid, "Earlier slides" if fid in EARLIER_SLIDES else "Slides")
             for fid in SLIDE_MAP.get(key, [])], by_id, linked
        )
        worksheets = make_resources(WORKSHEET_OVERRIDES.get(key, WORKSHEETS.get(num, [])), by_id, linked)
        evhtml = []
        if status == "Completed":
            for fid, label, _description in MIXED_GROUP_EVIDENCE.get(num, []):
                entry = by_id.get(fid)
                if entry:
                    evhtml.append(
                        get_link(entry, linked, EVIDENCE_LABELS.get(fid, label), "mixed-evidence-link")
                    )
            for fid, label, description in CLASS_EVIDENCE.get(key, []):
                entry = by_id.get(fid)
                if entry:
                    evhtml.append(get_link(entry, linked, label))
        evidence_html = (
            '<div class="lesson-evidence-items">'
            + "".join(f'<div>{item}</div>' for item in evhtml)
            + '</div>'
        ) if evhtml else ""
        rows.append(
            f'<tr id="science-{group}-lesson-{num}"><th scope="row">'
            f'<span class="lesson-number">Lesson {num:02}</span><strong>{esc(title)}</strong>{highlight}</th>'
            f'<td><span class="delivery-status {status.lower().replace(" ", "-")}">{esc(status)}</span>'
            f'<span class="lesson-date">{esc(date)}</span></td>'
            f'<td>{plan_html}</td><td>{slides}</td><td>{worksheets}</td>'
            f'<td>{evidence_html}</td></tr>'
        )
    sequence_note = (
        '<p class="lesson-sequence-note">Lesson 2 was not delivered by me. '
        'Its prepared resources are retained in Planning history.</p>'
    ) if group == 1 else ""
    return (
        f'<section class="lesson-section" id="science-{group}">'
        f'<div class="teaching-section-heading"><h3>Year 10 Science {group}</h3>'
        '<p>Lesson sequence with planned or recorded delivery, supporting resources and evidence.</p></div>'
        + sequence_note
        + '<div class="lesson-table-scroll" role="region" tabindex="0" '
        f'aria-label="Year 10 Science {group} lesson sequence">'
        '<table class="lesson-table"><thead><tr><th>Lesson</th>'
        '<th>Date / status</th><th>Plan</th><th>Slides</th><th>Worksheet</th>'
        '<th>Evidence</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div></section>"
    )


def other_learning_events(by_id, linked):
    items = []
    for fid, label, date in OTHER_LEARNING_EVENTS:
        entry = by_id.get(fid)
        if not entry:
            continue
        items.append(
            '<li><div class="other-event-entry">'
            f'{get_link(entry, linked, label, "other-event-link")}'
            f'<span class="other-event-date">{esc(date)}</span>'
            '</div></li>'
        )
    return (
        '<section class="other-learning-events" id="other-learning-events">'
        '<div class="teaching-section-heading"><h3>Other learning events</h3>'
        '<p>Year 13 Physics demonstrations and Science Club activities, '
        'with their plans and records.</p></div>'
        '<ul class="other-event-list">' + "".join(items) + '</ul></section>'
    ) if items else ""


def other_materials(entries, by_id, linked, events, plans):
    def group(title, items, intro=""):
        if not items:
            return ""
        content = f"<p>{esc(intro)}</p>" if intro else ""
        content += '<ul class="resource-list">' + "".join(
            f'<li>{get_link(e, linked, short_name(e))}'
            + "</li>" for e in sorted(items, key=lambda x: x["name"].casefold())
        ) + "</ul>"
        return f'<div class="supporting-group"><h4>{esc(title)}</h4>{content}</div>'

    matched = {fid for ids in SLIDE_MAP.values() for fid in ids}
    unmatched_slides = [
        x for x in entries if x.get("id") not in matched and SLIDES_FOLDER in x.get("path", [])
    ]
    plans_history = [x for x in entries if "99 Superseded Plans and Resources" in x.get("path", [])]
    unassigned_slides = unmatched_slides
    lesson_attached = set()
    lesson_attached.update(fid for pair in WORKSHEETS.values() for fid, _ in pair)
    lesson_attached.update(MIXED_EVIDENCE_ID_SET)
    lesson_attached.update(fid for vals in CLASS_EVIDENCE.values() for fid, _, _ in vals)
    ignore = matched | lesson_attached
    ignore.update(fid for fid, _, _ in OTHER_LEARNING_EVENTS)
    ignore.update(x["id"] for x in plans_history)
    ignore.update(x["id"] for x in unmatched_slides)
    other_files = [x for x in entries if x.get("id") not in ignore
                   and not lesson_plan_entry(x) and x.get("id") != UNIT_OVERVIEW_ID]
    sections = [
        group("Other presentations", unassigned_slides,
              "Additional decks are retained here until their class or lesson is confirmed."),
        group("Other teaching and planning resources", other_files),
    ]
    missed = []
    for (class_group, lesson), event in sorted(events.items()):
        if event["status"] != "Not delivered":
            continue
        plan = plans.get((class_group, lesson))
        plan_item = get_link(plan, linked, "Prepared lesson plan") if plan else "Plan not available"
        slides = make_resources(
            [(fid, "Prepared slides") for fid in SLIDE_MAP.get((class_group, lesson), [])],
            by_id, linked
        )
        missed.append(
            f'<li><strong>Year 10 Science {class_group}, Lesson {lesson:02}</strong> '
            f'({esc(event["date"])}): <strong>Not delivered by me.</strong> '
            'Preparation evidence only, not completed teaching or evidence of student learning. '
            + plan_item + ' · ' + slides + '</li>'
        )
    missed_block = (
        '<details class="planning-history"><summary>Prepared but not delivered</summary>'
        '<p>These resources were prepared for missed timetable slots. They do not count as '
        'completed teaching or evidence of learning, and their original dates remain recorded '
        'in the Learning Events Register.</p><ul class="resource-list">'
        + "".join(missed) + "</ul></details>"
    ) if missed else ""
    return (
        '<details class="planning-history"><summary>Other teaching resources</summary>'
        + "".join(sections) + "</details>"
        '<details class="planning-history"><summary>Planning history</summary>'
        + missed_block
        + '<details class="planning-history"><summary>Superseded versions</summary>'
        '<p>The original unit overview and earlier planning records show the development of '
        'the unit. Current class-specific plans and the delivery register take precedence.</p>'
        + group("Earlier plans and worksheets", plans_history)
        + '</details></details>'
    )


def short_name(entry):
    text = entry["name"]
    text = re.sub(r"\s*-\s*Y10 Science [12]\s*-\s*Full Lesson Plan.*", "", text, flags=re.I)
    text = re.sub(r"\s*\[Highlighted\]", "", text, flags=re.I)
    text = re.sub(r"^Lesson\s*0?(\d+)\s*[-:]\s*", lambda m: f"Lesson {int(m.group(1)):02}: ", text)
    return text


def teaching_body(entries, linked, events):
    by_id = {x["id"]: x for x in entries}
    plans = {(lesson_group(x), lesson_number(x)): x for x in entries if lesson_plan_entry(x)}
    content = (
        '<div class="teaching-dashboard">'
        '<p class="teaching-intro">Follow each class from planning through delivery and evidence. '
        'Dates and delivery statuses come from the Learning Events Register. Lesson plans and '
        'presentations are working documents that evolve with teaching experience.</p>'
        '<nav class="lesson-jump" aria-label="Lesson sequence navigation">'
        '<a href="#science-1">Year 10 Science 1</a><a href="#science-2">Year 10 Science 2</a>'
        '<a href="#other-learning-events">Other learning events</a>'
        '<a href="learning-events.html">Learning events register</a></nav>'
        + highlighted_panel(plans, events, linked)
        + ('<section class="unit-overview-note"><h3>Original unit overview</h3>'
           '<p>The initial unit overview records the starting plan. The lesson tables and '
           'class-specific plans below reflect subsequent revisions as teaching progresses.</p>'
           + get_link(by_id.get(UNIT_OVERVIEW_ID), linked, "Read original unit overview")
           + '</section>')
        + lesson_table(1, plans, events, by_id, linked)
        + lesson_table(2, plans, events, by_id, linked)
        + other_learning_events(by_id, linked)
        + other_materials(entries, by_id, linked, events, plans)
        + "</div>"
    )
    return content
