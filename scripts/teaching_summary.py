"""Mutually exclusive completed-event counts from the source register."""
from collections import Counter
import html

def event_category(row):
    row = list(row) + [''] * max(0, 8-len(row))
    kind = str(row[6]).strip().casefold()
    if 'individual support' in kind or 'one-to-one' in str(row[5]).casefold():
        return 'individual'
    if kind == 'full lesson' or 'cover lesson' in kind or 'cover session' in kind:
        return 'full'
    if 'part-lesson' in kind or 'demonstration' in kind:
        return 'part'
    return 'other'

def event_type_label(row):
    return {'full':'Full lesson', 'part':'Part-lesson / demonstration',
            'individual':'Individual support', 'other':'Other group activity'}[event_category(row)]

def event_counts(rows):
    counts = Counter()
    seen = set()
    for row in rows:
        row = list(row) + [''] * max(0, 8-len(row))
        event_id, status, kind = str(row[0]).strip(), str(row[1]).strip().casefold(), str(row[6]).strip().casefold()
        if not event_id or not row[5] or event_id in seen:
            continue
        seen.add(event_id)
        if status == 'planned':
            counts['planned'] += 1
            continue
        if status != 'recorded':
            continue
        category = event_category(row)
        counts[category] += 1
        counts['completed'] += 1
    assert counts['completed'] == sum(counts[k] for k in ('full','part','individual','other'))
    return counts

def render_teaching_summary(rows):
    counts = event_counts(rows)
    labels = [('completed','Completed teaching events'), ('full','Full lessons'),
              ('part','Part-lessons / demonstrations'), ('individual','Individual support sessions')]
    if counts['other']:
        labels.append(('other','Other group activities'))
    cards = ''.join(f'<div><dt>{html.escape(label)}</dt><dd>{counts[key]}</dd></div>' for key,label in labels)
    return ('<section class="teaching-summary" aria-labelledby="teaching-summary-title">'
            '<h3 id="teaching-summary-title">Teaching at a glance</h3><dl class="teaching-summary-counts">'
            + cards + '</dl>'
            '<p>'
            '<a href="learning-events.html">View the learning events register</a>.</p></section>')
