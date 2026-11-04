"""Publish one Goal/Standard page per native Google Doc.

The six current documents are the only authoritative source for these pages.
Older combined records remain in Google Drive but are not used to build pages.
This is a read-only presentation layer; it does not edit the source documents.
"""
import html
import re

GOAL_ARCHIVE = "1e4eJRQcTOQnHcv54RqMHfLrIuZlFwH5SJ2e_59pIu68"
STANDARD_ARCHIVE = "1PK2dkQxnGI2gPnI0k06wkhpu55MZpFKm5PUvYAIiANY"
ARCHIVE_PAGES = {GOAL_ARCHIVE: "goals.html", STANDARD_ARCHIVE: "standards.html"}

NEW_DOCUMENTS = {
    "1Dw5L_yjeuPlsrmzdWCc6BSA7ZVXoQ00cZfDRoOPfUac": ("goal", 1, "Curriculum and Lesson Planning"),
    "1Lb6tJF_dCHF31E100dqt7PDt3U3sCN78CkhrmKIyzzY": ("goal", 2, "Visual and Working Models"),
    "1OQIy08xo9qaTOoEXg6hfQycEkW3x2G5voD4Mfzo6xmU": ("goal", 3, "Local Field Trip"),
    "1tjr9_4MAaD8rfHP_hAppl5q4-IDa-l7H_igYmQJN440": ("standard", 2, "Professional Learning"),
    "1QWPX6RaidsiZVwXo9b8chnwWCXSk2V7QgOC9EhzAJt0": ("standard", 3, "Professional Relationships"),
    "1YGr2Y3LuDbW_Up21Pbxm2dlN6RkuigtKCOtUJ__zKnU": ("standard", 6, "Teaching"),
}
GROUPS = {
    "goal": {
        "hub": "goals.html", "title": "Professional goals",
        "intro": "Three professional goals, with rationale, actions, evidence and ongoing evaluation.",
        "items": [
            (1, "Curriculum and Lesson Planning", "Planning, delivering and evaluating a coherent Science unit."),
            (2, "Visual and Working Models", "Constructing working models and evaluating their teaching value."),
            (3, "Local Field Trip", "Preparing a curriculum-linked field investigation."),
        ],
    },
    "standard": {
        "hub": "standards.html", "title": "Professional standards",
        "intro": "ProfEx 1 reflections and evidence for Standards 2, 3 and 6.",
        "items": [
            (2, "Professional Learning", "Professional growth through reflection and feedback."),
            (3, "Professional Relationships", "Relationships that support learning and collaboration."),
            (6, "Teaching", "Teaching practice, assessment and responsive support for learning."),
        ],
    },
}
GOAL_EVIDENCE = {
    1: [
        ("Original electricity unit overview", "doc-10WsaDbhs--YacZgK5GeOJaW2RktNmefuKDce7lotR_w.html"),
        ("Year 10 Science 1 lesson sequence", "teaching.html#science-1"),
        ("Year 10 Science 2 lesson sequence", "teaching.html#science-2"),
        ("Week 4 lesson reflection", "reflection-week-4.html"),
        ("Mentor feedback", "file-11NQ6VYDJlr4P8Cwkmu_gkJD32W851l7I.html"),
        ("Lesson 3 worksheet samples", "file-1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM.html"),
        ("Lesson 4 exercise-book samples", "file-152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB.html"),
    ],
    2: [
        ("Photographs of the working models", "#photographic-evidence"),
        ("Year 13 standing-waves demonstration plan", "doc-1cwCx4lvhLZ4176e-3mISxNyiCIq221i1lyo6t3dAMKo.html"),
        ("Standing-wave frame photographs and playable video", "#standing-wave-apparatus"),
    ],
    3: [
        ("Science 1: beach electricity-generation lesson plan", "doc-1d37Sx_n_qNVfIb1KqOM3oCQ7N9ypsN1AEHsZJz52r6s.html"),
        ("Science 2: beach electricity-generation lesson plan", "doc-19QlznYT3rqKHTchwaY0LIGhFJ-uter_dzYVHwmkZBAU.html"),
        ("Observations from school and learning events", "doc-1HZugSfeanOI_V0GSbUouALCLt5nsNRiMJJsUt0ci90Q.html"),
    ],
}
STANDING_IMAGE_CLOSE = (
    "assets/drive/1xbXqSmR_t2K7-Jg25Yk7XjqrEI9GBWf9/"
    "Goal-2---Vibration-generator-wooden-frame---close-view.JPG"
)
STANDING_IMAGE_WIDE = (
    "assets/drive/1U8DLa3GjbBcpiTLSEY6MZWDG5EEThvZU/"
    "Goal-2---Standing-wave-setup-and-piano-strings.JPG"
)
STANDING_VIDEO = (
    "assets/drive/1FVVPuAvzmVbqKii8oZpPEILcLx9CoBKD/"
    "Goal-2---Standing-waves-demonstration.mp4"
)


def _esc(value):
    return html.escape(str(value), quote=True)


def group_for_page(page):
    if page == "goals.html":
        return "goal"
    if page == "standards.html":
        return "standard"
    return None


def section_page(fid):
    kind, number, _ = NEW_DOCUMENTS[fid]
    return f"{kind}-{number}.html"


def section_heading(fid):
    kind, number, title = NEW_DOCUMENTS[fid]
    return f"{kind.title()} {number}: {title}"


def hub_markup(kind):
    data = GROUPS[kind]
    cards = []
    for number, title, description in data["items"]:
        cards.append(
            f'<a class="topic-card" href="{kind}-{number}.html">'
            f'<span class="topic-card-number">{kind.title()} {number}</span>'
            f'<h3>{_esc(title)}</h3><p>{_esc(description)}</p>'
            '<span class="topic-card-link">Read reflection and evidence ↗</span></a>'
        )
    return (
        f'<p class="topic-hub-intro">{_esc(data["intro"])}</p>'
        + '<div class="topic-card-grid">' + "".join(cards) + '</div>'
    )


def navigation(fid):
    kind, number, _ = NEW_DOCUMENTS[fid]
    meta = GROUPS[kind]
    entries = meta["items"]
    link = [f'<a href="{meta["hub"]}">All {kind}s</a>']
    for n, _, _ in entries:
        current = ' aria-current="page"' if n == number else ""
        link.append(f'<a href="{kind}-{n}.html"{current}>{kind.title()} {n}</a>')
    j = [n for n, _, _ in entries].index(number)
    prev = (f'<a href="{kind}-{entries[j-1][0]}.html">Previous: '
            f'{kind.title()} {entries[j-1][0]}</a>') if j else '<span></span>'
    nxt = (f'<a href="{kind}-{entries[j+1][0]}.html">Next: '
           f'{kind.title()} {entries[j+1][0]}</a>') if j < len(entries)-1 else '<span></span>'
    return (
        '<nav class="topic-subnav" aria-label="Section navigation">'
        + "".join(link) + '</nav>',
        '<nav class="topic-pager" aria-label="Adjacent sections">'
        + prev + nxt + '</nav>'
    )


def _strip_audit_notes(markup, kind, number):
    """Remove dated cross-goal/standard housekeeping notes, not assessment evidence."""
    match = re.search(r'<p>\s*Evidence audit update:\s*[^<]*</p>', markup, re.I)
    if not match:
        return markup
    if kind == "goal" and number == 2:
        # New apparatus content was appended AFTER the older audit notes.
        following = re.search(
            r'<h3>\s*Standing.wave apparatus:\s*wooden support frame\s*</h3>',
            markup[match.end():], re.I,
        )
        if following:
            return markup[:match.start()] + markup[match.end() + following.start():]
    return markup[:match.start()]


def _goal_evidence_markup(number):
    items = GOAL_EVIDENCE[number]
    return '<ul class="goal-evidence-list">' + "".join(
        f'<li><a href="{_esc(url)}">{_esc(label)}</a></li>'
        for label, url in items
    ) + '</ul>'


def _replace_goal_evidence(markup, number):
    match = re.search(r'<h3>\s*Evidence\s*</h3>', markup, re.I)
    if not match:
        return markup
    next_heading = re.search(r'<h3\b[^>]*>', markup[match.end():], re.I)
    end = match.end() + next_heading.start() if next_heading else len(markup)
    return markup[:match.end()] + _goal_evidence_markup(number) + markup[end:]


def _standing_wave_gallery():
    return (
        '<section id="standing-wave-apparatus" class="goal-apparatus" '
        'aria-label="Wooden standing-wave frame and video">'
        '<h3>Standing-wave apparatus: construction and demonstration</h3>'
        '<p>Photographs of the wooden frame I built to hold the vibration '
        'generator and the driven-string setup beside the piano.</p>'
        '<div class="goal-media-grid">'
        '<figure><a href="file-1xbXqSmR_t2K7-Jg25Yk7XjqrEI9GBWf9.html">'
        f'<img loading="lazy" src="{_esc(STANDING_IMAGE_CLOSE)}" '
        'alt="Close view of the wooden vibration-generator support frame"></a>'
        '<figcaption>Wooden support frame, close view</figcaption></figure>'
        '<figure><a href="file-1U8DLa3GjbBcpiTLSEY6MZWDG5EEThvZU.html">'
        f'<img loading="lazy" src="{_esc(STANDING_IMAGE_WIDE)}" '
        'alt="Standing-wave string apparatus beside piano strings"></a>'
        '<figcaption>Wider standing-wave demonstration setup</figcaption></figure>'
        '</div>'
        '<figure class="goal-video"><video controls playsinline preload="metadata" '
        f'poster="{_esc(STANDING_IMAGE_WIDE)}">'
        f'<source src="{_esc(STANDING_VIDEO)}" type="video/mp4">'
        'Your browser does not support the embedded video.</video>'
        '<figcaption>Standing-wave demonstration using the vibration generator '
        'and signal generator. Select play to watch on this page.</figcaption>'
        '</figure></section>'
    )


def adapt_source(fid, markup):
    kind, number, title = NEW_DOCUMENTS[fid]
    # The page wrapper supplies the title. Avoid displaying the same heading twice.
    markup = re.sub(
        rf'^\s*<h3>\s*{kind}\s*0?{number}\s*[:–—-]\s*[^<]*</h3>\s*',
        "", markup, count=1, flags=re.I,
    )
    markup = _strip_audit_notes(markup, kind, number)
    if kind == "goal":
        markup = _replace_goal_evidence(markup, number)
        if number == 2:
            markup = re.sub(
                r'<p>\s*<a\b[^>]*>\s*Video:\s*Standing.wave demonstration\s*</a>\s*</p>',
                "", markup, flags=re.I | re.S,
            )
            markup = re.sub(
                r'<h3>\s*Photographic evidence\s*</h3>',
                '<h3 id="photographic-evidence">Photographic evidence</h3>',
                markup, count=1, flags=re.I,
            )
            markup += _standing_wave_gallery()
    elif number == 3:
        markup = markup.replace(
            "Sharing my pepeha gave students an opportunity to learn about me "
            "and ask questions. In the observed lesson on 21 October, they "
            "asked me to present it in Hindi, which I did.",
            "Sharing my pepeha gave students an opportunity to learn about me "
            "and ask questions. During the Science 1 lesson on 21 October, "
            "students asked me to deliver part of the lesson in Hindi, which I did."
        )
    elif number == 6:
        markup = markup.replace(
            "The learning register records Science 1 Lesson 4 delivery on 23 October 2026. "
            "Science 2's 22 October lesson is now identified as Lesson 3, not Lesson 4.",
            "The learning register records Science 1 Lesson 4 on 23 October "
            "and Science 2 Lesson 4 on 29 October 2026."
        )
        insertion = (
            '<p>Year 10 Science 2 completed Lesson 4, the current-measurement '
            'practical, on 29 October 2026. Most students worked productively; '
            'two students did not complete the task despite reminders. This '
            'observation helps identify where more individual checking is needed.</p>'
        )
        marker = '<h3>Evidence links</h3>'
        if marker in markup:
            markup = markup.replace(marker, insertion + marker, 1)
    before, after = navigation(fid)
    return (
        before + '<article class="native-reflection"><div class="reflection-prose">'
        + markup + '</div></article>' + after
    )
