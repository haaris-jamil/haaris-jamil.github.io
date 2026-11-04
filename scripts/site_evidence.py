"""Website-only clarifications for pooled evidence and missed lesson chronology.

Never edit source Docs, Sheets, PDF bytes, student names or their redactions.
The annotation layer is applied after copying source content to the website.
"""
import html
import re

POOLED_FILES = {
    "1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM": (
        "Year 10 Lesson 3 worksheet samples",
        "Anonymised Year 10 worksheet samples from Lesson 3."
    ),
    "152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB": (
        "Year 10 Lesson 4 exercise-book samples",
        "Anonymised Year 10 exercise-book samples from Lesson 4."
    ),
    "1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq": (
        "Year 10 Lesson 5 crossword samples",
        "Anonymised Year 10 crossword samples from Lesson 5."
    ),
    "1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp": (
        "Year 10 Lesson 5 investigation samples",
        "Anonymised Year 10 investigation samples from Lesson 5."
    ),
}
CONFIRMED_FILES = {
    "11bBS4D14yRgJM3WHFjdrosXkQupp2GuO": (
        "Lesson 7: Science 1 student evidence",
        "Anonymised Year 10 Science 1 student work from 4 November 2026. "
        "This is class-specific evidence, but the samples do not prove that every student "
        "achieved the learning outcome."
    ),
}
ALL_FILES = {**POOLED_FILES, **CONFIRMED_FILES}
REGISTER_ID = "16Wky3Pb8fNWfaMRnJXW7gYQcxP4G1tI5eTJoc1fg9LY"
SAMPLE_ROOT = "https://haaris-jamil.github.io/"
REGISTER_ROW = re.compile(r"(<tr><td>(\d+)</td>.*?</tr>)", re.S)
TD = re.compile(r"<td>(.*?)</td>", re.S)


def evidence_page_info(entry):
    return ALL_FILES.get(entry["id"])


def _local_link(file_id, title="Year 10 evidence"):
    label = html.escape(title)
    return f'<a href="file-{file_id}.html">{label}</a>'


def _register_row(content, event_id):
    """Return original register source row without editing its other columns."""
    matches = list(TD.finditer(content))
    if len(matches) < 12:
        return content
    if event_id == 5:
        content = content[:matches[1].start(1)] + "Not delivered by me" + content[matches[1].end(1):]
        matches = list(TD.finditer(content))
    lesson = None
    if event_id in (7, 10):
        lesson = 3
    elif event_id in (9, 33):
        lesson = 4
    elif event_id in (11, 12):
        lesson = 5
    # Column L (index 11) is the register's evidence/observable outcomes.
    if event_id == 10:
        prior = matches[11].group(1)
        # Hide historical editing notes in the public table without changing
        # the Learning Events Register in Google Drive.
        prior = re.sub(
            r"Corrected to Lesson 3 following Haaris(?:&#x27;|')s confirmation "
            r"of the reconstructed Science 2 sequence\. The circuit-building "
            r"lesson postponed on 19 October was delivered in this slot\.\s*",
            "", prior
        )
        prior = prior.replace(
            "Delivered 22 October 2026. my mentor teacher",
            "Delivered 22 October 2026. My mentor teacher"
        )
        prior = prior.replace(
            "No Science 2 student work is linked here yet.",
            "Lesson 3 worksheet samples are linked below."
        )
        content = content[:matches[11].start(1)] + prior + content[matches[11].end(1):]
        matches = list(TD.finditer(content))
    if event_id == 15:
        prior = matches[11].group(1)
        prior = prior.replace(
            "no new photographs or student work samples have been linked here.",
            "anonymised student work has since been linked here."
        )
        more = (
            '<p><strong>Confirmed Science 1 evidence (4 November 2026):</strong> '
            + _local_link("11bBS4D14yRgJM3WHFjdrosXkQupp2GuO", "Anonymised Lesson 7 student work")
            + '</p>'
        )
        content = content[:matches[11].start(1)] + prior + more + content[matches[11].end(1):]
        matches = list(TD.finditer(content))
    if lesson is None:
        return content
    prior = matches[11].group(1)
    if event_id == 7:
        prior = prior.replace("Lessons 2–3: anonymised worksheet evidence",
                              "Year 10 Lesson 3 worksheet samples")
    if event_id == 9:
        prior = prior.replace("Lesson 4: anonymised exercise-book evidence",
                              "Year 10 Lesson 4 exercise-book samples")
    if lesson == 3:
        ids = ["1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM"]
    elif lesson == 4:
        ids = ["152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB"]
    else:
        ids = ["1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq",
               "1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp"]
    titles = {
        "1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM": "Worksheet samples",
        "152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB": "Exercise-book samples",
        "1KtOIR28Bb_5rQEVwZLhbbbzbgawfe5Uq": "Crossword samples",
        "1Gfg_Hoj-1bujSh3UdyKRI6i4BsLlhCtp": "Investigation samples",
    }
    links = " · ".join(_local_link(i, titles[i]) for i in ids)
    if not all(f'file-{i}.html' in prior for i in ids):
        prior += '<p>' + links + '</p>'
    return content[:matches[11].start(1)] + prior + content[matches[11].end(1):]


def reconcile_register(markup):
    def render(match):
        row, rid = match.group(1), int(match.group(2))
        return _register_row(row, rid)
    revised = REGISTER_ROW.sub(render, markup)
    # Preserve register facts and evidence URLs without internal commentary.
    return re.sub(r'<p class="register-provenance">.*?</p>', '', revised, flags=re.S)

def correct_standard_six(markup):
    """Keep Year 10 evidence labels without internal attribution commentary."""
    markup = markup.replace(
        "Anonymised worksheet and exercise-book samples are linked below, but I have not "
        "added a sample-by-sample analysis here or inferred whole-class mastery from their presence.",
        "Year 10 worksheet and exercise-book samples are linked below."
    )
    markup = markup.replace(
        "Pooled, anonymised worksheet and exercise-book samples are linked below. Their individual "
        "pages have not been attributed to either Year 10 group. There is no sample-by-sample "
        "class comparison and no inference of whole-class mastery.",
        "Year 10 worksheet and exercise-book samples are linked below."
    )
    for old, new in [
        ("<u>Lessons 2–3 worksheets</u>", "<u>Year 10 Lesson 3 worksheet samples</u>"),
        ("<u>Lesson 3 mixed-group worksheet samples</u>", "<u>Year 10 Lesson 3 worksheet samples</u>"),
        ("<u>Lesson 4 exercise-book evidence</u>", "<u>Year 10 Lesson 4 exercise-book samples</u>"),
        ("<u>Lesson 4 mixed-group exercise-book samples</u>", "<u>Year 10 Lesson 4 exercise-book samples</u>")
    ]:
        markup = markup.replace(old, new)
    for note in (
        "These are existing uploaded samples, not a claim that every response is correct; "
        "specific analysis remains a next step.",
        "These were pooled across both Year 10 groups. Their existence does not prove "
        "every response is correct or that either class independently met the objective."
    ):
        markup = markup.replace(note, "")
    markup = re.sub(
        r'<li class="standard-evidence-note">\s*These were pooled across both Year 10 groups\..*?</li>',
        "", markup, flags=re.I | re.S
    )
    return markup


def correct_audit(markup):
    markup = markup.replace(
        "Five exercise-book scans; predictions, diagrams and readings. Reflection now in plan.",
        "Pooled Lesson 4 exercise-book scans; predictions, diagrams and readings. "
        "Individual pages are not attributed to Science 1 or Science 2."
    ).replace(
        "Six crossword samples, five investigation page-1 samples, reflection and EV report.",
        "Pooled Lesson 5 crossword and investigation page-1 samples, with separate "
        "dated lesson reflection and EV report. No individual page attribution is confirmed."
    ).replace(
        "The five exercise-book pages are dated 23 October and support Science 1, not Science 2.",
        "The five exercise-book pages form a pooled Lesson 4 collection from both "
        "Year 10 groups. Their individual class attribution is not independently confirmed."
    ).replace(
        "Strong evidence for analysis; use the sample notes on the next page.",
        "Pooled evidence for sample-level analysis; it cannot establish a "
        "Science 1 or Science 2 class-wide outcome."
    ).replace(
        "Specific student work is not linked. Collect/locate existing diagrams or a later retention check, labelling the later date accurately.",
        "Pooled Lesson 3 student work is linked for context, but the individual "
        "pages are not independently attributable to Science 2. Collect a class-specific "
        "check before making a separate outcome claim."
    )
    return markup


def correct_goal_one(markup):
    return markup.replace(
        "Anonymised assessment/work samples",
        "Earlier pooled anonymised work samples across both Year 10 groups; individual "
        "pages are not class-attributed without confirmation. Separately confirmed "
        "Science 1 Lesson 7 evidence is labelled as such."
    )


def reconcile_page(page_name, markup):
    if page_name == "learning-events.html":
        return reconcile_register(markup)
    if page_name == "standard-6.html":
        return correct_standard_six(markup)
    if page_name == "doc-1CNI_D-c-NAObRIZKBPCiIUjMnvyYXVRhQQJK9eQjJsU.html":
        return correct_audit(markup)
    if page_name == "goal-1.html":
        return correct_goal_one(markup)
    markup = re.sub(r"mixed[- ]group", "Year 10", markup, flags=re.I)
    return markup
