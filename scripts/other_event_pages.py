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
            preparation = str(row[10]).strip()
            if rid in ('28','29'):
                preparation = preparation.replace('\nNZQA AS 91526 resources', '')
            body = ('<h3>Learning intention</h3><p>' + html.escape(str(row[8])) + '</p>'
                    '<h3>Preparation</h3><p>' + html.escape(preparation) + '</p>'
                    '<h3>Teaching and learning</h3><p>' + html.escape(str(row[11])) + '</p>')
            if rid in ('28','29'):
                body += ('<h3>Resources</h3><p><a href="https://www.nzqa.govt.nz/ncea/assessment/view-detailed.do?standardNumber=91526" target="_blank" rel="noopener noreferrer">NZQA AS 91526 assessment resources</a>.</p>')
            slug = f'event-{rid}-plan.html'
            write(slug, document_html(title + ': Session record', caption,
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
