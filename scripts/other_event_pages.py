"""Dedicated plans and reflections, using confirmed accounts only."""
import html
from other_events_table import EVENTS

def publish_other_event_pages(rows, document_html, write):
    pages = set()
    for row in rows:
        if not row or str(row[0]) not in EVENTS:
            continue
        row = list(row) + [''] * max(0,15-len(row))
        rid = str(row[0])
        title, group, plan = EVENTS[rid]
        caption = f'{group} · {row[2]}'
        if rid in ('27','28','29'):
            body = ('<h3>Learning intention</h3><p>Support one student in working through Year 13 Physics exam questions.</p>'
                    '<h3>Preparation</h3><p>I reviewed the NZQA AS 91526 resources to familiarise myself with the curriculum and assessment requirements before supporting the student.</p>'
                    '<h3>Resources</h3><p>Physics past-paper questions and '
                    '<a href="https://www.nzqa.govt.nz/ncea/assessment/view-detailed.do?standardNumber=91526" target="_blank" rel="noopener noreferrer">NZQA AS 91526 assessment resources</a>.</p>'
                    '<h3>Teaching and learning</h3><table class="document-table"><thead><tr><th>Teacher activity</th><th>Student activity</th></tr></thead>'
                    '<tbody><tr><td>Work through exam questions with the student and provide support in response to the questions and their needs.</td>'
                    '<td>Work through past-paper questions with individual guidance.</td></tr></tbody></table>'
                    '<h3>Checking understanding</h3><p>Use the student’s responses while working through the questions to guide the support provided.</p>')
            slug = f'event-{rid}-plan.html'
            write(slug, document_html(title + ': Plan', caption,
                  '<article class="native-reflection"><div class="reflection-prose">'+body+'</div></article>',back='teaching.html#other-learning-events'))
            pages.add(slug)
            reflection = ('I worked with one student during the Year 13 Physics lesson, guiding them as we solved questions from a past paper. '
                          'I made teaching decisions in response to the questions and the student’s needs.' if rid=='27' else
                          'I supported one student with Physics exam preparation, drawing on my review of the NZQA assessment resources.')
        else:
            reflection = str(row[12]).strip()
            if not reflection and rid=='1':
                reflection = 'I co-led the practical boat-building activity. Students worked collaboratively to construct model boats, and completed boats and observations were recorded during the activity.'
            if rid=='2':
                reflection = 'I delivered the standing-wave demonstration to Year 13 Physics with a brief explanation of the underlying principles. '+reflection
        slug = f'event-{rid}-reflection.html'
        body = ''.join('<p>'+html.escape(p)+'</p>' for p in reflection.split('\n\n') if p.strip())
        write(slug, document_html(title + ': Reflection',caption,
              '<article class="native-reflection"><div class="reflection-prose">'+body+'</div></article>',back='teaching.html#other-learning-events'))
        pages.add(slug)
    return pages
