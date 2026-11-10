"""Display linked photo/video evidence inline without changing Drive sources."""
import html
import re
from pathlib import Path

ANCHOR = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)


def attr(tag, name):
    m = re.search(r'\b' + name + r'=["\']([^"\']+)["\']', tag, re.I)
    return html.unescape(m[1]) if m else ''


def media_catalog(root=Path('.')):
    result = {}
    for page in root.glob('file-*.html'):
        text = page.read_text(encoding='utf-8')
        image = re.search(r'<figure class="drive-figure">\s*(<img\b[^>]*>)', text, re.I)
        video = re.search(r'<video\b[^>]*>[\s\S]*?</video>', text, re.I)
        if image:
            result[page.name] = ('image', attr(image[1], 'src'), '')
        elif video:
            source = attr(video[0].split('>')[0], 'src')
            if not source:
                source_tag = re.search(r'<source\b[^>]*>', video[0])
                source = attr(source_tag[0], 'src') if source_tag else ''
            poster = attr(video[0].split('>')[0], 'poster')
            if source:
                result[page.name] = ('video', source, poster)
    return result


def video_card(source, poster='', label='Video evidence'):
    source = html.escape(source, quote=True)
    poster_attr = f' poster="{html.escape(poster, quote=True)}"' if poster else ''
    # The tiny time fragment also supplies a first-frame preview while a poster
    # is being generated on the next sync. No autoplay or background audio.
    if not poster and '#' not in source:
        source += '#t=0.1'
    return (f'<span class="evidence-media evidence-video">'
            f'<span class="evidence-player"><video controls playsinline preload="metadata"'
            f'{poster_attr} aria-label="{html.escape(label, quote=True)}" src="{source}"></video>'
            '<button type="button" class="evidence-play" hidden aria-label="Play video">'
            '▶ Play video</button></span>'
            f'<span class="evidence-caption">{html.escape(label)}</span></span>')


def inline_evidence(markup, catalog):
    def replace(match):
        href, body = match[1], match[2]
        target = href.split('#')[0]
        if target not in catalog or re.search(r'<(?:img|video)\b', body, re.I):
            return match[0]
        label = html.unescape(re.sub(r'<[^>]*>', '', body)).strip() or 'Evidence'
        kind, source, poster = catalog[target]
        if kind == 'image':
            return (f'<span class="evidence-media evidence-photo">'
                    f'<img loading="lazy" decoding="async" src="{html.escape(source, quote=True)}" '
                    f'alt="{html.escape(label, quote=True)}">'
                    f'<span class="evidence-caption">{html.escape(label)}</span></span>')
        return video_card(source, poster, label)
    markup = ANCHOR.sub(replace, markup)
    def existing_video(match):
        prefix = markup[max(0, match.start()-80):match.start()]
        if prefix.endswith('<span class="evidence-player">'):
            return match[0]
        tag = match[0].split('>')[0]
        source = attr(tag, 'src')
        if not source:
            source_tag = re.search(r'<source\b[^>]*>', match[0])
            source = attr(source_tag[0], 'src') if source_tag else ''
        if not source:
            return match[0]
        return video_card(source, attr(tag, 'poster'), attr(tag, 'aria-label') or 'Video demonstration')
    return re.sub(r'<video\b[^>]*>[\s\S]*?</video>', existing_video, markup, flags=re.I)


def publish_inline_media(root=Path('.')):
    catalog = media_catalog(root)
    count = 0
    for page in root.glob('*.html'):
        original = page.read_text(encoding='utf-8')
        updated = inline_evidence(original, catalog)
        if updated != original:
            page.write_text(updated, encoding='utf-8')
            count += 1
    return count
