#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_collocations_audio_no_bs4.py

Purpose:
  Convert plain-text Collocations rows in Thai frequency HTML notes into playable
  collocation chips, matching the newer 101–200 style.

No external packages required.
Only uses Python standard library.

Usage:
  # dry run in current folder
  python3 fix_collocations_audio_no_bs4.py --dry-run

  # actually modify files and create .bak backups
  python3 fix_collocations_audio_no_bs4.py --backup

  # fix one file only
  python3 fix_collocations_audio_no_bs4.py thai-frequency-rank301-400-notes-audio.html --backup

  # scan subfolders
  python3 fix_collocations_audio_no_bs4.py --root ./thai-notes --recursive --backup
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import Iterable, Tuple


DEFAULT_PATTERN = "thai-frequency-rank*-notes-audio*.html"

COLLOC_CHIP_CSS = (
    ".colloc-chip{display:inline-flex;align-items:center;gap:4px;"
    "border:.5px solid rgba(120,130,140,.22);border-radius:999px;"
    "padding:3px 8px;margin:3px 5px 3px 0;background:rgba(255,255,255,.55)}"
)


def iter_files(root: Path, recursive: bool, pattern: str) -> Iterable[Path]:
    if recursive:
        yield from root.rglob(pattern)
    else:
        yield from root.glob(pattern)


def split_collocations(text: str) -> list[str]:
    """
    Split plain collocation text into items.
    Handles comma, Chinese comma, Thai/English semicolon, slash-like separators.
    Keeps useful phrases such as "นอกจาก...แล้ว".
    """
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" ,，;；|/、")
    if not text:
        return []

    parts = re.split(r"\s*(?:,|，|;|；|、|\|)\s*", text)
    out: list[str] = []
    seen = set()

    for p in parts:
        p = p.strip()
        p = re.sub(r"\s+", " ", p)
        p = p.strip(" ,，;；|/、")
        if not p:
            continue

        # Avoid accidentally using obvious explanations as collocations.
        if len(p) > 80:
            continue

        # Remove trailing punctuation only.
        p = p.rstrip(".。")

        if p and p not in seen:
            seen.add(p)
            out.append(p)

    return out


def make_chip(item: str) -> str:
    safe_item = html.escape(item, quote=False)
    safe_attr = html.escape(item, quote=True)
    return (
        f'<span class="colloc-chip">'
        f'<button class="speak mini" type="button" data-thai="{safe_attr}" aria-label="play">🔊</button>'
        f'<span class="thai">{safe_item}</span>'
        f'</span>'
    )


def convert_colloc_block(match: re.Match[str]) -> Tuple[str, bool]:
    """
    Convert one <div class="colloc">...</div> block if it has plain text after
    the Collocations tag. Returns (new_block, changed).
    """
    full = match.group(0)
    open_tag = match.group(1)
    inner = match.group(2)
    close_tag = match.group(3)

    # Already fixed.
    if "colloc-chip" in inner:
        return full, False

    tag_match = re.search(
        r'(<span\b[^>]*class=["\'][^"\']*\b(?:tag|badge)\b[^"\']*\bblue\b[^"\']*["\'][^>]*>\s*Collocations\s*</span>)',
        inner,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not tag_match:
        return full, False

    tag_html = tag_match.group(1)
    before = inner[: tag_match.end()]
    after = inner[tag_match.end():]

    # Strip any remaining HTML tags from the plain list area.
    plain_after = re.sub(r"<[^>]+>", " ", after)
    items = split_collocations(plain_after)

    if not items:
        return full, False

    chips = "".join(make_chip(item) for item in items)
    new_inner = before + chips
    return open_tag + new_inner + close_tag, True


def convert_collocations(content: str) -> Tuple[str, int]:
    """
    Convert all plain collocation blocks.
    """
    pattern = re.compile(
        r'(<div\b[^>]*class=["\'][^"\']*\bcolloc\b[^"\']*["\'][^>]*>)(.*?)(</div>)',
        flags=re.IGNORECASE | re.DOTALL,
    )

    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        new_block, changed = convert_colloc_block(match)
        if changed:
            count += 1
        return new_block

    new_content = pattern.sub(repl, content)
    return new_content, count


def ensure_colloc_chip_css(content: str) -> Tuple[str, bool]:
    """
    Add .colloc-chip CSS if missing.
    """
    if ".colloc-chip" in content:
        return content, False

    style_end = content.find("</style>")
    if style_end == -1:
        return content, False

    # Insert before </style>.
    content = content[:style_end] + COLLOC_CHIP_CSS + content[style_end:]
    return content, True


def process_file(path: Path, dry_run: bool, backup: bool) -> Tuple[int, bool]:
    content = path.read_text(encoding="utf-8", errors="replace")
    new_content, changed_blocks = convert_collocations(content)
    new_content, css_added = ensure_colloc_chip_css(new_content)

    changed = changed_blocks > 0 or css_added

    if changed and not dry_run:
        if backup:
            backup_path = path.with_suffix(path.suffix + ".bak")
            if not backup_path.exists():
                backup_path.write_text(content, encoding="utf-8")
        path.write_text(new_content, encoding="utf-8")

    return changed_blocks, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Thai notes plain Collocations into playable audio chips. No bs4 required."
    )
    parser.add_argument("files", nargs="*", help="Specific HTML files to process.")
    parser.add_argument("--root", default=".", help="Folder to scan if no files are provided.")
    parser.add_argument("--recursive", action="store_true", help="Scan subfolders recursively.")
    parser.add_argument("--pattern", default=DEFAULT_PATTERN, help=f"Glob pattern. Default: {DEFAULT_PATTERN}")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")
    parser.add_argument("--backup", action="store_true", help="Create .bak backup before modifying.")
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files]
    else:
        root = Path(args.root)
        files = sorted(iter_files(root, args.recursive, args.pattern))

    if not files:
        print("No matching HTML files found.")
        return

    total_blocks = 0
    changed_files = 0

    for path in files:
        if not path.exists() or path.suffix.lower() not in {".html", ".htm"}:
            print(f"SKIP {path}  (not an HTML file or not found)")
            continue

        blocks, changed = process_file(path, dry_run=args.dry_run, backup=args.backup)
        total_blocks += blocks

        if changed:
            changed_files += 1
            mode = "WOULD FIX" if args.dry_run else "FIXED"
            print(f"{mode} {path}  | collocation blocks converted: {blocks}")
        else:
            print(f"OK {path}  | already fixed or no plain collocations found")

    print("-" * 72)
    if args.dry_run:
        print(f"Dry run complete. Files that would change: {changed_files}; blocks: {total_blocks}")
    else:
        print(f"Done. Files changed: {changed_files}; blocks converted: {total_blocks}")


if __name__ == "__main__":
    main()
