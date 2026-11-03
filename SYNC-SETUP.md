# ProfEx 1 portfolio synchronisation

The website mirrors the contents of the **ProfEx 1 portfolio** Google Drive folder.

- Google Drive source folder: `13L9IMcA3-j3OjUWTHgB8YKwYKXbvHKX4`
- GitHub Actions workflow: `.github/workflows/sync-reflections.yml`
- Main publisher: `scripts/sync_workspace.py`
- Helpers: `scripts/sync_media.py`, `scripts/sync_reflections.py`
- Schedule: hourly at minute 17 UTC, plus manual runs, plus script/workflow changes.

## Google setup (existing service account)

In the existing Google Cloud project, enable these APIs:

1. [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
2. [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
3. [Google Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com)
4. Google Docs API (already enabled for the reflection-only workflow).

Keep the same read-only service account and the existing GitHub Actions
repository secret `GOOGLE_SERVICE_ACCOUNT_JSON`. Share the parent portfolio
folder with the service account as a Viewer. **Do not place the JSON key in
the repository.** The workflow never changes the source documents.

Once all APIs are enabled, open [the GitHub Actions workflow](https://github.com/haaris-jamil/haaris-jamil.github.io/actions/workflows/sync-reflections.yml),
choose **Run workflow**, then check its conclusion and the live site.

## Published content

The script recursively scans the source folder and its subfolders, generates
native webpages for Docs and Sheets, and renders Slides as compressed slide
images. It mirrors PDFs and other stored files up to 40 MB, preserving the
original filenames in local assets. Files above the limit are linked to Drive.

The weekly reflection pages use only the explicitly labelled **Published
version** tab or content preceding a **Rough notes** heading. Other source
documents are imported in full. No anonymisation or redaction is performed.

## Audit

Each successful scan writes:

- `sync-audit.html`: files that could not update, files not copied
  automatically, and limitations such as inaccessible embedded objects.
- `.sync-manifest/portfolio.json`: machine-readable status and cache.
- `portfolio-sources.html`: files stored at the root of the source folder.

A failed API request for one file does not stop the other files from being
published, and earlier successful pages are retained where possible. A failed
root Drive listing aborts the run rather than publishing an empty site.

### Notes

- Changes normally appear after the next successful hourly run and Pages
  deployment, not instantly.
- GitHub Pages and the repository are public. **The site content becomes
  publicly accessible even if the URL has not been shared.**
- Images in Slides are stored locally as WebP files. Complex Google Docs
  objects unsupported by the API converter are listed in the audit.
- Google Sheets are represented as formatted-value tables; macros, charts and
  editing controls are not mirrored as interactive spreadsheet features.
- A hyperlink to an external document does not copy the linked document unless
  that document is inside the scanned portfolio folder.
