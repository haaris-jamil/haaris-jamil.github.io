"""Generate portfolio subpages from multi-section Google Docs.

The source Docs remain untouched. Goal 1/2/3 and Standard 2/3/6 become
individual website pages. The master Google Doc is not required to be split.
"""
import html
import re

GOALS_ID = "1e4eJRQcTOQnHcv54RqMHfLrIuZlFwH5SJ2e_59pIu68"
STANDARDS_ID = "1PK2dkQxnGI2gPnI0k06wkhpu55MZpFKm5PUvYAIiANY"
DOCUMENTS = {
    GOALS_ID: {
        "prefix": "goal", "allowed": (1, 2, 3), "hub": "goals.html",
        "label": "Professional goals",
        "intro": "Three professional goals, with rationale, action steps, evidence and ongoing evaluations.",
        "kind": "GOAL", "extract": "Goal",
    },
    STANDARDS_ID: {
        "prefix": "standard", "allowed": (2, 3, 6), "hub": "standards.html",
        "label": "Professional standards",
        "intro": "ProfEx 1 requires reflections and evidence for Standards 2, 3 and 6.",
        "kind": "STANDARD", "extract": "Focus",
    },
}
HEADING = re.compile(
    r"<h3>\s*(GOAL|STANDARD)\s*0?([1-6])\s*[:\u2013\u2014-]\s*([^<]*)</h3>",
    re.I,
)
STRIP_TAGS = re.compile(r"<[^>]+>")
FIRST_PARA = re.compile(
    r"<h3>\s*(?:Goal|Focus)\s*</h3>\s*<p>(.*?)</p>", re.I | re.S
)


def sections_from_html(source_markup, document_id):
    """Return only the selected numbered sections, preserving their source HTML."""
    cfg = DOCUMENTS[document_id]
    matches = list(HEADING.finditer(source_markup))
    selected = {}
    for index, match in enumerate(matches):
        kind, number = match.group(1).upper(), int(match.group(2))
        if kind != cfg["kind"] or number not in cfg["allowed"]:
            continue
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(source_markup)
        body = source_markup[match.end():stop].strip()
        title = html.unescape(STRIP_TAGS.sub("", match.group(3))).strip(" :\u2013\u2014")
        if not title or not body:
            raise ValueError(f"Empty {kind.title()} {number} in the source document")
        if number in selected:
            raise ValueError(f"Duplicate {kind.title()} {number} heading in the source")
        selected[number] = {"number": number, "title": title, "body": body}
    missing = set(cfg["allowed"]) - set(selected)
    if missing:
        raise ValueError(f"Missing {cfg['kind']} sections: {sorted(missing)}")
    return selected


def section_url(document_id, number):
    return f"{DOCUMENTS[document_id]['prefix']}-{number}.html"


def nav_row(document_id, selected, active=None):
    cfg = DOCUMENTS[document_id]
    links = [f'<a href="{cfg["hub"]}">All {html.escape(cfg["label"].lower())}</a>']
    for number in cfg["allowed"]:
        current = ' aria-current="page"' if active == number else ""
        links.append(
            f'<a{current} href="{section_url(document_id, number)}">'
            f'{html.escape(cfg["kind"].title())} {number}</a>'
        )
    return '<nav class="topic-subnav" aria-label="Section navigation">' + "".join(links) + "</nav>"


def subpage_bodies(document_id, selected):
    cfg = DOCUMENTS[document_id]
    result = {}
    for index, number in enumerate(cfg["allowed"]):
        section = selected[number]
        before = cfg["allowed"][index - 1] if index else None
        after = cfg["allowed"][index + 1] if index + 1 < len(cfg["allowed"]) else None
        previous = (
            f'<a href="{section_url(document_id, before)}">Previous: '
            f'{cfg["kind"].title()} {before}</a>' if before else '<span></span>'
        )
        following = (
            f'<a href="{section_url(document_id, after)}">Next: '
            f'{cfg["kind"].title()} {after}</a>' if after else '<span></span>'
        )
        content = (
            nav_row(document_id, selected, active=number)
            + '<article class="native-reflection"><div class="reflection-prose">'
            + section["body"] + '</div></article>'
            + '<nav class="topic-pager" aria-label="Adjacent sections">'
            + previous + following + '</nav>'
        )
        result[section_url(document_id, number)] = {
            "title": f'{cfg["kind"].title()} {number}: {section["title"].title()}',
            "caption": cfg["intro"],
            "body": content,
            "back": cfg["hub"],
        }
    return result


def hub_body(document_id, selected):
    cfg = DOCUMENTS[document_id]
    cards = []
    for number in cfg["allowed"]:
        section = selected[number]
        match = FIRST_PARA.search(section["body"])
        description = STRIP_TAGS.sub("", match.group(1)).strip() if match else ""
        title = section["title"].title()
        cards.append(
            f'<a class="topic-card" href="{section_url(document_id, number)}">'
            f'<span class="topic-card-number">{cfg["kind"].title()} {number}</span>'
            f'<h3>{html.escape(title)}</h3>'
            f'<p>{html.escape(html.unescape(description))}</p>'
            '<span class="topic-card-link">Read reflection and evidence ↗</span></a>'
        )
    return (
        f'<p class="topic-hub-intro">{html.escape(cfg["intro"])}</p>'
        + '<div class="topic-card-grid">' + "".join(cards) + "</div>"
    )
