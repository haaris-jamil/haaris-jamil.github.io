"""Read-only converters for Google Sheets, Slides and stored Drive files.

Results are HTML, local asset paths and status metadata. No Google writes.
"""
import html
import json
import mimetypes
import shutil
import re
import time
import random
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

MAX_BINARY_BYTES = 40 * 1024 * 1024
SLIDE_ASSET_ROOT = Path("assets/slides")
BINARY_ASSET_ROOT = Path("assets/drive")


def esc(value):
    return html.escape(str(value or ""), quote=True)


def api_json(session, url, params=None, timeout=90):
    """Retry short-term Google rate limits without turning them into file failures."""
    for attempt in range(8):
        r = session.get(url, params=params, timeout=timeout)
        if r.ok:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and attempt < 7:
            value = r.headers.get("Retry-After")
            try:
                wait = min(90, max(1, float(value))) if value else min(90, 5 * 2 ** attempt)
            except ValueError:
                wait = min(90, 5 * 2 ** attempt)
            print(f"Google API HTTP {r.status_code}: retrying in {wait:.0f}s", flush=True)
            time.sleep(wait + random.uniform(0, 1.5))
            continue
        raise RuntimeError(f"Google API HTTP {r.status_code}: {r.text[:250]}")


def safe_filename(name, default):
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(name)).strip(".-")
    return (clean[:110] or default)


def render_cell(cell):
    val = str(cell.get("formattedValue", "") or "")
    if not val:
        return ""
    link = cell.get("hyperlink")
    if not link:
        urls = {
            x.get("format", {}).get("link", {}).get("uri")
            for x in cell.get("textFormatRuns", [])
        }
        urls.discard(None)
        if len(urls) == 1:
            link = next(iter(urls))
    if not link and val.startswith(("https://", "http://")):
        link = val
    if link and urlparse(link).scheme in ("http", "https"):
        return f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer">{esc(val)}</a>'
    return esc(val)


def tab_matrix(tab):
    rows = []
    for group in tab.get("data", []):
        for row in group.get("rowData", []):
            rows.append(row.get("values", []))
    while rows and not any(c.get("formattedValue") for c in rows[-1]):
        rows.pop()
    return rows


def column_label(number):
    result = ""
    while number:
        number, offset = divmod(number - 1, 26)
        result = chr(65 + offset) + result
    return result


def sync_sheet(session, entry, old):
    fid = entry["id"]
    base = f"https://sheets.googleapis.com/v4/spreadsheets/{fid}"
    meta = api_json(session, base, params={"fields": "properties(title),sheets(properties(title,gridProperties(rowCount,columnCount,frozenRowCount)))"})
    tabs = meta.get("sheets", [])
    if not tabs:
        raise RuntimeError("Spreadsheet has no tabs")
    title = meta.get("properties", {}).get("title", entry["name"])
    sections = []
    truncated = []
    for tab in tabs:
        prop = tab.get("properties", {})
        label = prop.get("title", "Sheet")
        grid = prop.get("gridProperties", {})
        rowcount = int(grid.get("rowCount", 1000))
        colcount = int(grid.get("columnCount", 26))
        max_rows = min(rowcount, 2000)
        max_cols = min(colcount, 52)
        # Google Sheets API supports a bound without an end column.
        col_end = column_label(max_cols)
        request_range = f"'{label.replace(chr(39), chr(39)*2)}'!A1:{col_end}{max_rows}"
        if rowcount > max_rows or colcount > max_cols:
            truncated.append(f"{label}: grid exceeds {max_rows} rows or {max_cols} columns")
        data = api_json(session, base, params=[
            ("includeGridData", "true"),
            ("ranges", request_range),
            ("fields", "sheets(properties(title,gridProperties(frozenRowCount)),data(rowData(values(formattedValue,hyperlink,textFormatRuns))))"),
        ])
        shown = data.get("sheets", [])
        if not shown:
            raise RuntimeError(f"Could not read tab {label}")
        matrix = tab_matrix(shown[0])
        if not matrix:
            sections.append(f"<h3>{esc(label)}</h3><p>This sheet is empty.</p>")
            continue
        cols = min(max_cols, max(len(row) for row in matrix))
        header_idx = max(0, int(grid.get("frozenRowCount", 1)) - 1)
        header_idx = min(header_idx, len(matrix) - 1)
        while header_idx < len(matrix) - 1 and not any(
            c.get("formattedValue") for c in matrix[header_idx]
        ):
            header_idx += 1
        pre = []
        for row in matrix[:header_idx]:
            nonempty = [c.get("formattedValue", "") for c in row if c.get("formattedValue")]
            if nonempty:
                pre.append("<p>" + " · ".join(esc(x) for x in nonempty) + "</p>")
        hdr = matrix[header_idx]
        headers = "".join(
            "<th scope=\"col\">" + render_cell(hdr[j] if j < len(hdr) else {}) + "</th>"
            for j in range(cols)
        )
        body_rows = []
        for row in matrix[header_idx + 1:]:
            if not any(c.get("formattedValue") for c in row):
                continue
            body_rows.append(
                "<tr>" + "".join(
                    "<td>" + render_cell(row[j] if j < len(row) else {}) + "</td>"
                    for j in range(cols)
                ) + "</tr>"
            )
        sections.append(
            f'<section class="sheet-section"><h3>{esc(label)}</h3>'
            + '<div class="sheet-overview">' + "".join(pre) + "</div>"
            + f'<div class="sheet-scroll" role="region" aria-label="{esc(label)}" tabindex="0">'
            + '<table class="sheet-table"><thead><tr>' + headers
            + '</tr></thead><tbody>' + "".join(body_rows) + "</tbody></table></div></section>"
        )
    name = "learning-events.html" if fid == "16Wky3Pb8fNWfaMRnJXW7gYQcxP4G1tI5eTJoc1fg9LY" else f"sheet-{fid}.html"
    return name, title, "\n".join(sections), truncated


def download_slide_image(url, path):
    response = requests.get(url, timeout=90)
    if not response.ok:
        raise RuntimeError(f"Slide thumbnail download failed: HTTP {response.status_code}")
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise RuntimeError(f"Slide thumbnail did not return an image: {content_type}")
    from PIL import Image
    from io import BytesIO
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image.thumbnail((1400, 1400))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=83, method=4)


def sync_slides(session, entry, old):
    fid = entry["id"]
    name = entry["name"]
    modified = entry.get("modifiedTime", "")
    src = old.get(fid, {})
    page_name = f"slides-{fid}.html"
    base = SLIDE_ASSET_ROOT / fid
    previous = int(src.get("slides", 0))
    cached = bool(
        modified and src.get("modifiedTime") == modified and previous
        and all((base / f"slide-{i}.webp").is_file() for i in range(1, previous + 1))
    )
    if cached:
        total = previous
    else:
        doc = api_json(
            session, f"https://slides.googleapis.com/v1/presentations/{fid}",
            params={"fields": "title,slides(objectId)"},
        )
        slide_ids = [slide["objectId"] for slide in doc.get("slides", [])]
        total = len(slide_ids)
        if not total:
            raise RuntimeError("Presentation contains no slides")
        for i, slide_id in enumerate(slide_ids, 1):
            time.sleep(1.5)  # Throttle Slides API expensive-read quota.
            thumb = api_json(
                session,
                f"https://slides.googleapis.com/v1/presentations/{fid}/pages/{quote(slide_id, safe='')}/thumbnail",
                params={
                    "thumbnailProperties.mimeType": "PNG",
                    "thumbnailProperties.thumbnailSize": "LARGE",
                },
            )
            if not thumb.get("contentUrl"):
                raise RuntimeError(f"No image URL for slide {i}")
            download_slide_image(thumb["contentUrl"], base / f"slide-{i}.webp")
        for extra in base.glob("slide-*.webp"):
            try:
                if int(extra.stem.split("-")[-1]) > total:
                    extra.unlink()
            except ValueError:
                pass
    figures = []
    for i in range(1, total + 1):
        figures.append(
            f'<figure class="slide-figure"><img loading="lazy" '
            f'src="assets/slides/{fid}/slide-{i}.webp" '
            f'alt="{esc(name)}: slide {i}"><figcaption>Slide {i}</figcaption></figure>'
        )
    page_body = '<div class="slide-gallery">' + "\n".join(figures) + "</div>"
    return page_name, name, page_body, {"modifiedTime": modified, "slides": total}


def render_pdf_pages(pdf_path, modified, previous, max_pages=4):
    """Generate cached, browser-readable JPG previews without changing PDF bytes."""
    import pymupdf
    from PIL import Image

    directory = pdf_path.parent / "pdf-pages"
    found = sorted(directory.glob("page-*.jpg")) if directory.exists() else []
    if previous.get("modifiedTime") == modified and found:
        with pymupdf.open(pdf_path) as pdf:
            return found[:min(len(pdf), max_pages)], len(pdf)
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(pdf_path) as pdf:
        count = min(len(pdf), max_pages)
        for number in range(count):
            page = pdf[number]
            longest = max(page.rect.width, page.rect.height)
            scale = min(1.9, 1600.0 / max(longest, 1))
            bitmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale),
                colorspace=pymupdf.csRGB, alpha=False,
            )
            target = directory / f"page-{number + 1:03}.jpg"
            Image.frombytes(
                "RGB", (bitmap.width, bitmap.height), bitmap.samples
            ).save(target, "JPEG", quality=84, optimize=True)
        return sorted(directory.glob("page-*.jpg")), len(pdf)


def sync_binary(session, entry, old):
    fid = entry["id"]
    modified = entry.get("modifiedTime", "")
    mimetype = entry.get("mimeType", "application/octet-stream")
    size = int(entry.get("size", "0") or "0")
    name = entry["name"]
    if size > MAX_BINARY_BYTES:
        return None, "File exceeds the 40 MB automatic-copy limit"
    extension = mimetypes.guess_extension(mimetype) or ""
    filename = safe_filename(name, fid)
    if "." not in filename and extension:
        filename += extension
    output = BINARY_ASSET_ROOT / fid / filename
    cached = old.get(fid, {}).get("modifiedTime") == modified and output.exists()
    if not cached:
        url = f"https://www.googleapis.com/drive/v3/files/{fid}"
        with session.get(url, params={"alt": "media"}, stream=True, timeout=90) as response:
            if not response.ok:
                raise RuntimeError(f"Download HTTP {response.status_code}")
            output.parent.mkdir(parents=True, exist_ok=True)
            copied = 0
            with output.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    copied += len(chunk)
                    if copied > MAX_BINARY_BYTES:
                        handle.close()
                        output.unlink(missing_ok=True)
                        raise RuntimeError("Download exceeds 40 MB limit")
                    handle.write(chunk)
    asset = str(output)
    if mimetype.startswith("image/"):
        body = f'<figure class="drive-figure"><img src="{esc(asset)}" alt="{esc(name)}"></figure>'
    elif mimetype == "application/pdf":
        # A browser's PDF plug-in can be unavailable (notably in embedded views).
        # Publish image previews alongside the full unchanged PDF for reliable reading.
        preview_limit = 10 if "05 Student Evidence - Anonymised" in entry.get("path", []) else 4
        try:
            page_images, total_pages = render_pdf_pages(
                output, modified, old.get(fid, {}), preview_limit
            )
        except Exception as exc:
            print(f"Could not render PDF page images for {name}: {exc}", flush=True)
            page_images, total_pages = [], 0
        download = (
            f'<p class="pdf-file-actions">'
            f'<a href="{esc(asset)}" target="_blank" rel="noopener">Open full PDF</a>'
            f' · <a href="{esc(asset)}" download>Download PDF</a></p>'
        )
        if page_images:
            cards = "".join(
                f'<figure class="pdf-page-card"><img loading="lazy" decoding="async" '
                f'src="{esc(str(p))}" alt="{esc(name)} - page {n}" />'
                f'<figcaption>Page {n}</figcaption></figure>'
                for n, p in enumerate(page_images, start=1)
            )
            remainder = (
                f'<p class="pdf-pages-more">Showing {len(page_images)} of {total_pages} '
                'pages. Use the full PDF link to see the remaining pages.</p>'
                if total_pages > len(page_images) else ""
            )
            body = download + (
                '<div class="pdf-page-previews" aria-label="PDF page previews">'
                + cards + '</div>' + remainder
            )
        else:
            body = download + (
                f'<iframe title="{esc(name)}" class="pdf-preview" '
                f'src="{esc(asset)}"></iframe>'
            )
    elif mimetype.startswith("video/"):
        import subprocess
        from evidence_media import video_card
        poster = output.parent / 'poster.jpg'
        if not cached or not poster.is_file():
            try:
                subprocess.run([
                    'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-i', str(output), '-frames:v', '1',
                    '-vf', 'scale=960:-2', '-q:v', '3', str(poster)
                ], check=True, timeout=90)
            except (OSError, subprocess.SubprocessError) as error:
                print(f'Video poster unavailable for {name}: {error}', flush=True)
        body = video_card(asset, str(poster) if poster.is_file() else '', name)
    elif mimetype.startswith("audio/"):
        body = f'<audio controls preload="metadata" src="{esc(asset)}"></audio>'
    else:
        body = f'<p><a href="{esc(asset)}" download>Download this file</a></p>'
    return body, None


def _object_ids(blocks):
    found = []
    for block in blocks:
        if "paragraph" in block:
            for element in block["paragraph"].get("elements", []):
                obj = element.get("inlineObjectElement", {}).get("inlineObjectId")
                if obj:
                    found.append(obj)
        if "table" in block:
            for row in block["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    found.extend(_object_ids(cell.get("content", [])))
    return found


def _doc_blocks_for_images(doc, published_only):
    tabs = []
    def visit(tab):
        tabs.append(tab)
        for child in tab.get("childTabs", []):
            visit(child)
    for tab in doc.get("tabs", []):
        visit(tab)
    if not tabs:
        blocks = doc.get("body", {}).get("content", [])
        if published_only:
            from sync_reflections import _published_blocks
            return [_published_blocks(blocks)]
        return [blocks]
    if published_only:
        from sync_reflections import _published_blocks
        selected = [
            tab for tab in tabs
            if tab.get("tabProperties", {}).get("title", "").strip().casefold()
            in ("published version", "formal reflection")
        ]
        if selected:
            return [
                _published_blocks(selected[0].get("documentTab", {}).get("body", {}).get("content", []))
            ]
        if len(tabs) == 1:
            return [_published_blocks(tabs[0].get("documentTab", {}).get("body", {}).get("content", []))]
        return []
    return [tab.get("documentTab", {}).get("body", {}).get("content", []) for tab in tabs]


def sync_doc_images(doc, rendered, file_id, modified, previous, published_only=False):
    """Substitute embedded-object placeholders with locally mirrored images."""
    marker = "<em>[Embedded image or object in Google Doc]</em>"
    if marker not in rendered:
        return rendered, []
    source_ids = []
    for content in _doc_blocks_for_images(doc, published_only):
        source_ids.extend(_object_ids(content))
    objects = dict(doc.get("inlineObjects", {}))
    def collect_objects(tab):
        objects.update(tab.get("documentTab", {}).get("inlineObjects", {}))
        for child in tab.get("childTabs", []):
            collect_objects(child)
    for tab in doc.get("tabs", []):
        collect_objects(tab)
    asset_dir = Path("assets/doc-images") / file_id
    warnings = []
    image_cache_valid = previous.get("modifiedTime") == modified
    used = set()
    for object_id in source_ids:
        if marker not in rendered:
            break
        image = (
            objects.get(object_id, {})
            .get("inlineObjectProperties", {})
            .get("embeddedObject", {})
            .get("imageProperties", {})
            .get("contentUri")
        )
        if not image:
            warnings.append(f"Image/drawing {object_id}: no accessible content URI")
            rendered = rendered.replace(marker, '<em>[Image unavailable]</em>', 1)
            continue
        safe_id = safe_filename(object_id, "object")
        output = asset_dir / f"{safe_id}.webp"
        used.add(output.name)
        if not image_cache_valid or not output.exists():
            try:
                from PIL import Image
                from io import BytesIO
                response = requests.get(image, timeout=75)
                response.raise_for_status()
                illustration = Image.open(BytesIO(response.content)).convert("RGB")
                illustration.thumbnail((1600, 1600))
                output.parent.mkdir(parents=True, exist_ok=True)
                illustration.save(output, "WEBP", quality=85, method=4)
            except Exception as err:
                warnings.append(f"Image/drawing {object_id}: {type(err).__name__}")
                rendered = rendered.replace(marker, '<em>[Image unavailable]</em>', 1)
                continue
        rendered = rendered.replace(
            marker,
            f'<img class="document-image" loading="lazy" '
            f'src="assets/doc-images/{file_id}/{safe_id}.webp" '
            f'alt="Illustration from the source document">',
            1,
        )
    if marker in rendered:
        warnings.append("Some embedded objects were not accessible for conversion")
    return rendered, warnings

