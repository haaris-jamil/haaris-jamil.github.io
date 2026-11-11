"""Present documented non-Year-10 events without inventing plans or evidence."""
import html
from datetime import datetime

EVENTS = {
    '2': ('Standing waves on a string', 'Year 13 Physics', '1cwCx4lvhLZ4176e-3mISxNyiCIq221i1lyo6t3dAMKo'),
    '1': ('Design and build model boats', 'Primary Science Club', '1mlnEweXYo0_3sWmluA01U3haV_ZGnH3KEG-mfyYvstA'),
    '27': ('One-to-one past-paper exam preparation', 'Year 13 Physics', None),
    '28': ('One-to-one exam preparation', 'Year 13 Physics', None),
    '29': ('One-to-one exam preparation', 'Year 13 Physics', None),
    '34': ('Sound interference and wavelength', 'Year 13 Physics', '1ofp5jgQ1npOkrbHJrQXB_HmaY6jh0zVUiR3_ksWdn-4'),
}


def render_other_events(rows, by_id, linked):
    selected = []
    for row in rows:
        if not row or str(row[0]) not in EVENTS:
            continue
        row = list(row) + [''] * max(0, 15 - len(row))
        try:
            date = datetime.strptime(row[2], '%d/%m/%Y')
        except ValueError:
            date = datetime.max
        selected.append((date, str(row[0]), row))
    output = []
    for date, rid, row in sorted(selected):
        title, group, plan = EVENTS[rid]
        status = {'recorded':'Completed', 'planned':'Planned'}.get(row[1].strip().lower(), row[1] or 'Unconfirmed')
        formatted_date = date.strftime('%-d %b %Y') if date != datetime.max else row[2] or 'Date to confirm'
        record = f'event-{rid}-reflection.html'
        if plan:
            page = linked.get(plan, {}).get('page') or f'doc-{plan}.html'
            preparation = f'<a href="{html.escape(page, quote=True)}">Plan</a>'
        else:
            preparation = f'<a href="event-{rid}-plan.html">Plan</a>'
        resources = ('<a href="https://www.nzqa.govt.nz/ncea/assessment/view-detailed.do?standardNumber=91526" target="_blank" rel="noopener noreferrer">NZQA AS 91526</a>'
                     if rid in ('27','28','29') else '<span class="no-resource">—</span>')
        record_label = 'Reflection' if status == 'Completed' else 'Planning record'
        output.append(
            f'<tr id="other-event-{rid}"><th scope="row"><strong>{html.escape(title)}</strong></th>'
            f'<td>{html.escape(group)}</td><td><span class="delivery-status {status.lower()}">{html.escape(status)}</span>'
            f'<span class="lesson-date">{html.escape(formatted_date)}</span></td>'
            f'<td>{preparation}</td><td>{resources}</td><td><a href="{record}">{record_label}</a></td></tr>'
        )
    if not output:
        return ''
    return ('<section class="other-learning-events" id="other-learning-events">'
            '<div class="teaching-section-heading"><h3>Other learning events</h3>'
            '<p>Individual support, demonstrations and Science Club activities.</p></div>'
            '<div class="lesson-table-scroll" role="region" tabindex="0" aria-label="Other learning events">'
            '<table class="lesson-table"><thead><tr><th scope="col">Learning event</th>'
            '<th scope="col">Class/group</th><th scope="col">Date/status</th>'
            '<th scope="col">Plan</th><th scope="col">Resources</th><th scope="col">Reflection</th>'
            '</tr></thead><tbody>' + ''.join(output) + '</tbody></table></div></section>')

