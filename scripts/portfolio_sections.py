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
GOAL_EVIDENCE = {1: [['Original electricity unit overview',
      'doc-10WsaDbhs--YacZgK5GeOJaW2RktNmefuKDce7lotR_w.html',
      'Starting sequence against which the delivered lessons can be compared.'],
     ['Year 10 Science 1 lesson sequence',
      'teaching.html#science-1',
      'Class-specific delivery dates, revised plans and learning evidence.'],
     ['Year 10 Science 2 lesson sequence',
      'teaching.html#science-2',
      'Shows how pacing and activities differed between the two classes.'],
     ['Week 4 lesson reflection',
      'reflection-week-4.html',
      'Early adjustments to lesson timing and checks for understanding.'],
     ['Week 4 mentor feedback',
      'file-11NQ6VYDJlr4P8Cwkmu_gkJD32W851l7I.html',
      'Feedback that informed subsequent circuit challenges.'],
     ['Circuit worksheet samples',
      'file-1jnws3tkTTA1DPXzfPSvdWrAzeyD0HWJM.html',
      'Early student responses for comparison with later work.'],
     ['Current-measurement exercise-book samples',
      'file-152w-8ZhbUAkKyOivkEtCWTHlfZgm8ZlB.html',
      'Students’ predictions, measurements and developing scientific vocabulary.'],
     ['Electricity-generation lesson and evaluation, 11 November',
      'doc-1TlRge3vHrb2nAxlmYoItLTyYuOJHQyqPJMQLUgPBcEo.html',
      'A later plan and reflection showing how the original unit developed.'],
     ['Week 7 reflection',
      'reflection-week-7.html',
      'Explains changes made in response to engagement and mentor feedback.'],
     ['Electricity-generation worksheets, 12 November',
      'file-1SoxlQ-UniCqmiOxVUpj7QRF1gRvOcviB.html',
      'Later learner responses, including remaining confusion about the meter.'],
     ['Combined student feedback',
      'observations.html#student-voice',
      'Learners’ views on support, challenge, pacing and accessible notes.'],
     ['Final mentor teacher report',
      'file-19K27Ff8KA8H5zgwWP7swCO_QObF6Zons.html',
      'Standards 2 and 5 address feedback, responsive planning and adapting the unit to learners.']],
 2: [['Photographs of the working models',
      '#photographic-evidence',
      'Construction evidence and descriptions of my contribution.'],
     ['Year 13 standing-waves demonstration plan',
      'doc-1cwCx4lvhLZ4176e-3mISxNyiCIq221i1lyo6t3dAMKo.html',
      'The scientific purpose and planned use of the apparatus.'],
     ['Standing-wave frame and my explanation video',
      '#standing-wave-apparatus',
      'Shows the support frame, operation of the model and my explanation.'],
     ['Electricity-generation lesson and evaluation, 11 November',
      'doc-1TlRge3vHrb2nAxlmYoItLTyYuOJHQyqPJMQLUgPBcEo.html',
      'Records how the circuit guide and working generator models were used in teaching.'],
     ['Electricity-generation worksheets, 12 November',
      'file-1SoxlQ-UniCqmiOxVUpj7QRF1gRvOcviB.html',
      'Students’ observations and explanations help evaluate the models’ teaching value.'],
     ['Week 7 reflection',
      'reflection-week-7.html',
      'Evaluates the visual guide and investigation approach, including limits of the evidence.'],
     ['Evaluative visit report',
      'file-1dEwr-kpWHhXndo3GnRUC3ZZ2eNtCxzS4.html',
      'The Goal 2 and Standard 6 comments address practical resources, visual models and scaffolded '
      'learning.']],
 3: [['My account of collaborative risk assessment',
      '#risk-assessment',
      'I discussed each point of the beach trip’s safety and risk assessment with my mentor before he entered it into the school’s ERP form.'],
     ['Science 1: beach electricity-generation lesson plan',
      'doc-1d37Sx_n_qNVfIb1KqOM3oCQ7N9ypsN1AEHsZJz52r6s.html',
      'Includes the 20 November delivery reflection and evaluation.'],
     ['Science 2: beach electricity-generation lesson plan',
      'doc-19QlznYT3rqKHTchwaY0LIGhFJ-uter_dzYVHwmkZBAU.html',
      'Includes the 19 November account of testing turbines and adapting the water source.'],
     ['Week 8 mentor feedback',
      'file-1rRvWITIrWeZMXAr96dYh18LTa7rgwhRV.html',
      'Independent feedback on the field trip, with recommendations about time and group size.'],
     ['Week 8 reflection',
      'reflection-week-8.html',
      'Evaluates both trips, the reservoir difficulties and improvements for future planning.'],
     ['Completed beach investigations in the learning register',
      'learning-events.html#event-22',
      'Records the 19 and 20 November learning events and their evaluations.'],
     ['Observations from school and learning events',
      'doc-1HZugSfeanOI_V0GSbUouALCLt5nsNRiMJJsUt0ci90Q.html',
      'Background learning about local settings, school culture and outdoor activities.']]}
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
    "Goal-2---Standing-waves-demonstration.mp4?v=explanation-20261121"
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
    return '<div class="topic-card-grid">' + "".join(cards) + '</div>'


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
    rows = []
    for item in GOAL_EVIDENCE[number]:
        label, url, *description = item
        detail = ': ' + _esc(description[0]) if description else ''
        rows.append(f'<li><a href="{_esc(url)}">{_esc(label)}</a>{detail}</li>')
    return '<ul class="goal-evidence-list">' + ''.join(rows) + '</ul>'


def _replace_goal_evidence(markup, number):
    match = re.search(r'<h3>\s*Evidence\s*</h3>', markup, re.I)
    if not match:
        return markup
    next_heading = re.search(r'<h3\b[^>]*>', markup[match.end():], re.I)
    end = match.end() + next_heading.start() if next_heading else len(markup)
    # Concrete links now live in the Google Doc. Preserve subsequent source
    # edits instead of overwriting them with the older fallback list.
    source = markup[match.end():end]
    if re.search(r'<a\b[^>]*href=', source, re.I):
        if re.search(r'<ul\b', source, re.I):
            contents = re.sub(r'<ul\b[^>]*>', '<ul class="goal-evidence-list">', source, count=1)
        else:
            paragraphs = re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>', source, re.I | re.S)
            contents = '<ul class="goal-evidence-list">' + ''.join(
                '<li>' + text + '</li>' for text in paragraphs if re.sub(r'<[^>]+>', '', text).strip()
            ) + '</ul>'
        return markup[:match.end()] + contents + markup[end:]
    return markup[:match.end()] + _goal_evidence_markup(number) + markup[end:]


def _standing_wave_player():
    """Inline video thumbnail beside the source document's existing images."""
    return (
        '<figure id="standing-wave-video" class="goal-video">'
        f'<video controls playsinline preload="metadata" poster="assets/drive/1FVVPuAvzmVbqKii8oZpPEILcLx9CoBKD/poster.jpg?v=explanation-20261121">'
        f'<source src="{_esc(STANDING_VIDEO)}" type="video/mp4">'
        'Your browser does not support the embedded video.</video>'
        '<figcaption>My explanation of standing waves using the vibration generator '
        'and signal generator.</figcaption></figure>'
    )


def _standard_evidence_rows(markup):
    """Set each evidence reference on its own line without changing the source Doc.

    Single-link paragraphs keep their full descriptions. Known compound source
    paragraphs are divided at their natural sentence / link boundaries.
    Unrecognised multi-link paragraphs still expose every link separately.
    """
    title = re.search(r"<h3>\s*Evidence links\s*</h3>", markup, re.I)
    if not title:
        return markup
    following = markup[title.end():]
    stop = re.search(r"<h3\b", following, re.I)
    end = title.end() + stop.start() if stop else len(markup)
    original = markup[title.end():end]
    paragraphs = list(re.finditer(r"<p(?:\s[^>]*)?>(.*?)</p>", original, re.I | re.S))
    if not paragraphs:
        return markup

    link_re = re.compile(r"<a\b[^>]*>.*?</a>", re.I | re.S)
    def strip_tags(value):
        return re.sub(r"<[^>]+>", "", value).strip()

    rows = []
    for paragraph in paragraphs:
        inner = paragraph.group(1).strip()
        links = link_re.findall(inner)
        if not links:
            rows.append(f'<li>{inner}</li>')
            continue
        if len(links) == 1:
            rows.append(f'<li>{inner}</li>')
            continue

        chunks = link_re.split(inner)
        # This preserves all the evidence references while attaching descriptions
        # to the correct record in the three compound source paragraphs.
        if len(links) == 2 and "learning register" in strip_tags(links[1]).lower():
            separator = " The "
            before, found, after = chunks[1].rpartition(separator)
            rows.append(f'<li>{links[0]}{before if found else chunks[1]}</li>')
            rows.append(f'<li>{separator.strip()} {links[1]}{chunks[2]}' if found
                        else f'<li>{links[1]}{chunks[2]}</li>')
            if found:
                rows[-1] += '</li>' if not rows[-1].endswith('</li>') else ''
        elif len(links) == 2 and "Read alongside the" in chunks[1]:
            before, _, _ = chunks[1].partition(" Read alongside the ")
            rows.append(f'<li>{links[0]}{before}</li>')
            rows.append(f'<li>{links[1]}{chunks[2]}</li>')
        elif len(links) == 2 and "Learner-work samples" in chunks[0]:
            rows.append(f'<li>{links[0]}</li>')
            rows.append(f'<li>{links[1]}</li>')
            # Keep only the Year 10 evidence links, not an attribution note.
        else:
            for anchor in links:
                rows.append(f'<li>{anchor}</li>')
            context = re.sub(r"\s+", " ", "".join(chunks)).strip(" ,.;")
            if context:
                rows.append(f'<li class="standard-evidence-note">{context}</li>')
    contents = '<ul class="standard-evidence-list">' + "".join(rows) + '</ul>'
    return markup[:title.end()] + contents + markup[end:]


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
        if number == 3:
            markup = re.sub(
                r'<p>(I made substantial progress in collaborative planning, delivery and evaluation\.)',
                r'<p id="risk-assessment">\1', markup, count=1,
            )
        if number == 2:
            markup = re.sub(
                r'<h3>\s*Photographic evidence\s*</h3>',
                '<h3 id="photographic-evidence">Photographic evidence</h3>',
                markup, count=1, flags=re.I,
            )
            markup = re.sub(
                r'<h3>\s*Standing.wave apparatus:\s*wooden support frame\s*</h3>',
                '<h3 id="standing-wave-apparatus">Standing-wave apparatus: wooden support frame</h3>',
                markup, count=1, flags=re.I,
            )
            # Two frame photographs are already present in the source Google Doc.
            video_link = (
                r'<p>\s*<a\b[^>]*>\s*(?:<u>\s*)?'
                r'Video:\s*Standing.wave demonstration\s*(?:</u>\s*)?</a>\s*</p>'
            )
            markup, replaced = re.subn(
                video_link, lambda _: _standing_wave_player(),
                markup, count=1, flags=re.I | re.S,
            )
            if not replaced:
                markup += _standing_wave_player()
    elif number == 3:
        markup = markup.replace(
            '<h3>Colleague correspondence</h3>',
            '<h3 id="colleague-correspondence">Colleague correspondence</h3>',
        )
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
    if kind == "standard":
        # Some older mentor-observation references point to redacted duplicates.
        # The corresponding completed PDF is already mirrored on the site.
        markup = markup.replace(
            'href="https://drive.google.com/file/d/1k2YpbtSlsUJIc8Mpn0jzoOqOQwHSCnGw/view"',
            'href="file-11NQ6VYDJlr4P8Cwkmu_gkJD32W851l7I.html"',
        )
        markup = _standard_evidence_rows(markup)
    before, after = navigation(fid)
    return (
        before + '<article class="native-reflection"><div class="reflection-prose">'
        + markup + '</div></article>' + after
    )

