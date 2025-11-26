#!/usr/bin/env python3
"""
Create a local copy of a Markdown file with image links rewritten to local assets.

Usage:
  python markdown_localize.py /path/to/file.md [--suffix .local] [--assets-dir assets]
"""

import argparse
import pathlib
import re
import sys
import urllib.request
from typing import Dict, Iterable, List


IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone markdown file(s) with local asset links for images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "markdown",
        type=pathlib.Path,
        help="Path to the source markdown file (kept untouched) or directory (batch).",
    )
    parser.add_argument(
        "--suffix",
        default=".local",
        help="Suffix to append before the markdown extension for the cloned file.",
    )
    parser.add_argument(
        "--assets-dir",
        default="assets",
        help="Directory (relative to the markdown file) to store downloaded images.",
    )
    parser.add_argument(
        "--pattern",
        default=r"https?://",
        help="Regex to select which image URLs to download (applied to image link targets).",
    )
    return parser.parse_args()


def build_output_path(md_path: pathlib.Path, suffix: str) -> pathlib.Path:
    if suffix and not suffix.startswith("."):
        suffix = f".{suffix}"
    if md_path.suffix:
        return md_path.with_name(f"{md_path.stem}{suffix}{md_path.suffix}")
    return md_path.with_name(f"{md_path.name}{suffix}")


def unique_urls(urls: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


def sanitize_name(name: str) -> str:
    # Keep it simple: letters, digits, dash, underscore, dot.
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return cleaned or "image"


def derive_base_name(url: str, alt: str) -> str:
    if alt:
        return sanitize_name(alt)
    base = url.split("/")[-1].split("?")[0] or "image"
    return sanitize_name(base)


def allocate_filename(base_name: str, asset_dir: pathlib.Path, existing: Dict[str, str]) -> str:
    if "." in base_name:
        stem = ".".join(base_name.split(".")[:-1]) or "image"
        ext = "." + base_name.split(".")[-1]
    else:
        stem, ext = base_name, ""

    candidate = base_name
    idx = 1
    while (asset_dir / candidate).exists() or candidate in existing.values():
        candidate = f"{stem}_{idx}{ext}"
        idx += 1
    return candidate


def download(url: str, dest: pathlib.Path) -> None:
    with urllib.request.urlopen(url, timeout=30) as resp:
        dest.write_bytes(resp.read())


def is_clone_file(md_path: pathlib.Path, normalized_suffix: str) -> bool:
    return md_path.name.endswith(f"{normalized_suffix}{md_path.suffix}")


def process_markdown(
    md_path: pathlib.Path,
    selector: re.Pattern[str],
    suffix: str,
    assets_dir_name: str,
) -> int:
    text = md_path.read_text(encoding="utf-8")

    matches = [(m.group(1).strip(), m.group(2).strip()) for m in IMAGE_LINK_RE.finditer(text)]
    urls = unique_urls([url for _, url in matches if selector.search(url)])
    if not urls:
        print(f"[info] {md_path}: no matching image URLs found; nothing to download")
        return 0

    asset_dir = (md_path.parent / assets_dir_name).resolve()
    asset_dir.mkdir(parents=True, exist_ok=True)
    mapping: Dict[str, str] = {}

    alt_lookup = {url: alt for alt, url in matches if selector.search(url)}

    for url in urls:
        base = derive_base_name(url, alt_lookup.get(url, ""))
        filename = allocate_filename(base, asset_dir, mapping)
        download(url, asset_dir / filename)
        mapping[url] = filename
        print(f"[downloaded] {md_path}: {url} -> {asset_dir / filename}")

    new_text = text
    rel_assets = pathlib.Path(assets_dir_name)
    for url, fname in mapping.items():
        new_text = new_text.replace(url, str(rel_assets / fname))

    out_path = build_output_path(md_path, suffix)
    out_path.write_text(new_text, encoding="utf-8")
    print(f"[done] cloned markdown: {out_path}")
    print(f"[summary] downloaded {len(mapping)} file(s) to {asset_dir}")
    return len(mapping)


def main() -> int:
    args = parse_args()
    target: pathlib.Path = args.markdown.expanduser().resolve()
    if not target.exists():
        print(f"[error] path not found: {target}", file=sys.stderr)
        return 1

    selector = re.compile(args.pattern)
    normalized_suffix = args.suffix if args.suffix.startswith(".") else f".{args.suffix}"

    if target.is_dir():
        md_files = sorted(target.rglob("*.md"))
        if not md_files:
            print(f"[info] no markdown files under {target}")
            return 0

        total_downloaded = 0
        for md in md_files:
            if is_clone_file(md, normalized_suffix):
                print(f"[skip] {md} (looks like cloned output)")
                continue
            try:
                total_downloaded += process_markdown(md, selector, args.suffix, args.assets_dir)
            except Exception as exc:
                print(f"[error] {md}: {exc}", file=sys.stderr)
        print(f"[batch] processed {len(md_files)} markdown file(s).")
        return 0

    # Single file
    process_markdown(target, selector, args.suffix, args.assets_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
