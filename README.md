# Markdown Localizer

Create a local, self-contained copy of Markdown file(s) by downloading inline image links and rewriting them to a local `assets/` folder. The original Markdown remains untouched. Works with Confluence exports and any other Markdown that uses standard image syntax `![alt](url)`.

## Requirements
- Python 3.9+ (stdlib only; no extra packages)

## Quick start
```bash
cd /path/to/your/docs
python ~/projects/markdown-localizer/markdown_localize.py "Sample document.md"
```
This will:
- Download matched images to `assets/` (created next to the source file)
- Write a cloned Markdown named `Sample document.local.md` (original untouched)

## Options
- `--suffix .local` — suffix inserted before the Markdown extension for the cloned file.
- `--assets-dir assets` — target assets directory (relative to the Markdown file). Use `assets` to keep it clean (default). Change if you want a different folder per run.
- `--pattern <regex>` — regex applied to each image URL to decide whether to download. Default `https?://` (download any remote image). For Confluence-only: `--pattern 'media-cdn\\.atlassian\\.com'`.

Example with a custom assets folder and suffix:
```bash
python ~/projects/markdown-localizer/markdown_localize.py \
  "Sample document.md" \
  --suffix .local-copy \
  --assets-dir assets_custom
```

Batch mode (process all `*.md` under a directory, skipping already-generated `*.local.md`):
```bash
python ~/projects/markdown-localizer/markdown_localize.py /path/to/dir --pattern 'https?://'
```

## Notes
- The script deduplicates URLs and auto-renames files when names collide (adds `_1`, `_2`, …).
- Filenames prefer the image alt text; if missing, the URL basename is used. Non-alphanumeric characters are replaced with `_`.
- Existing files in the assets folder are preserved; new downloads use unique names.
- Only the cloned Markdown has links rewritten; the source stays unchanged. Normalize it safely to `*.local.md` to keep diffs and recovery simple.
