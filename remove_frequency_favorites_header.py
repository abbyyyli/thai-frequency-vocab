#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remove_frequency_favorites_header.py

批次移除 Thai Frequency HTML 的 Favorites tab 裡這段文字：

Favorites｜輕量複習字卡
預設只放重點；忘記時再展開 Usage / Collocations / Examples。

也會移除較短版本：
預設只放重點；忘記時再展開。

其他功能不動。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TARGET_FILES_PATTERN = "thai-frequency-rank*-notes-audio.html"


def remove_favorites_header(html: str) -> str:
    # 目標：把 toolbar 裡左側標題說明整塊拿掉，只保留收藏數量。
    replacement = '''<div class="tf-favs-toolbar">
        <div class="tf-favs-count">已收藏 ${cards.length} 字</div>
      </div>'''

    patterns = [
        # 大卡版：完整說明
        r'''<div\s+class=["']tf-favs-toolbar["']>\s*
\s*<div>\s*
\s*<h2\s+style=["']margin:0;["']>\s*Favorites｜輕量複習字卡\s*</h2>\s*
\s*<div\s+class=["']subtitle["']>\s*預設只放重點；忘記時再展開 Usage / Collocations / Examples。\s*</div>\s*
\s*</div>\s*
\s*<div\s+class=["']tf-favs-count["']>\s*已收藏\s*\$\{cards\.length\}\s*字\s*</div>\s*
\s*</div>''',

        # compact 版：短說明
        r'''<div\s+class=["']tf-favs-toolbar["']>\s*
\s*<div>\s*
\s*<h2\s+style=["']margin:0;["']>\s*Favorites｜輕量複習字卡\s*</h2>\s*
\s*<div\s+class=["']subtitle["']>\s*預設只放重點；忘記時再展開。\s*</div>\s*
\s*</div>\s*
\s*<div\s+class=["']tf-favs-count["']>\s*已收藏\s*\$\{cards\.length\}\s*字\s*</div>\s*
\s*</div>''',
    ]

    for pattern in patterns:
        html = re.sub(pattern, replacement, html, flags=re.MULTILINE)

    # 保險：如果只剩單獨標題/說明，也移除
    standalone_patterns = [
        r'''\s*<h2\s+style=["']margin:0;["']>\s*Favorites｜輕量複習字卡\s*</h2>\s*''',
        r'''\s*<div\s+class=["']subtitle["']>\s*預設只放重點；忘記時再展開 Usage / Collocations / Examples。\s*</div>\s*''',
        r'''\s*<div\s+class=["']subtitle["']>\s*預設只放重點；忘記時再展開。\s*</div>\s*''',
    ]

    for pattern in standalone_patterns:
        html = re.sub(pattern, "", html, flags=re.MULTILINE)

    # 保險：如果留下空 wrapper，就清掉空 wrapper
    empty_left_pattern = r'''<div\s+class=["']tf-favs-toolbar["']>\s*
\s*<div>\s*</div>\s*
\s*(<div\s+class=["']tf-favs-count["']>\s*已收藏\s*\$\{cards\.length\}\s*字\s*</div>)\s*
\s*</div>'''

    html = re.sub(
        empty_left_pattern,
        '''<div class="tf-favs-toolbar">
        \1
      </div>''',
        html,
        flags=re.MULTILINE,
    )

    return html


def patch_file(path: Path, dry_run: bool = False, backup: bool = True) -> str:
    original = path.read_text(encoding="utf-8")
    patched = remove_favorites_header(original)

    if patched == original:
        return "OK no change"

    if dry_run:
        return "WOULD CLEAN"

    if backup:
        backup_path = path.with_suffix(path.suffix + ".before-remove-fav-header.bak")
        if not backup_path.exists():
            backup_path.write_text(original, encoding="utf-8")

    path.write_text(patched, encoding="utf-8")
    return "CLEANED"


def find_files(base_dir: Path) -> list[Path]:
    return sorted(base_dir.glob(TARGET_FILES_PATTERN))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="HTML 檔案所在資料夾")
    parser.add_argument("--dry-run", action="store_true", help="只預覽，不修改")
    parser.add_argument("--no-backup", action="store_true", help="不要產生 .bak 備份")
    args = parser.parse_args()

    base_dir = Path(args.dir).expanduser().resolve()
    files = find_files(base_dir)

    if not files:
        print(f"找不到檔案：{base_dir}/{TARGET_FILES_PATTERN}")
        return

    for file in files:
        try:
            status = patch_file(file, dry_run=args.dry_run, backup=not args.no_backup)
            print(f"{status:12} {file.name}")
        except Exception as e:
            print(f"ERROR       {file.name}: {e}")

    if args.dry_run:
        print("\nDry run 完成：尚未修改檔案。確認沒問題後執行：python3 remove_frequency_favorites_header.py")
    else:
        print("\n完成。Favorites tab 裡的標題與說明已移除，其他功能保留。")


if __name__ == "__main__":
    main()
