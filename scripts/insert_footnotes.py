"""脚注挿入スクリプト。

MinerU の content_list.json に含まれる page_footnote 型ブロック
（脚注・訳注）を、対応する Markdown の該当ページ末尾位置に blockquote
として挿入する。詳細は
docs/issues/feat-009-insert-footnotes/design.md を参照。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import html_table_to_md
import normalize_punct

NUM_PREFIX_RE = re.compile(
    r"^(?:"
    r"\d+"                        # 例: "4 "
    r"|[⁰¹²³⁴⁵⁶⁷⁸⁹]+"            # 例: "⁴ "
    r"|\\?\*\d+"                  # 例: "*4 " / "\*4 "（Markdown エスケープ）
    r"|\$\^\{\*?\d+\}\$"          # 例: "$^{3}$ " / "$^{*4}$ "
    r")\s"
)

KEY_STRIP_RE = re.compile(r"[\s$\\]+")


def comparison_key(text: str) -> str:
    """断片判定に用いる比較キー（空白・`$`・`\\` を除去した文字列）を返す。"""
    return KEY_STRIP_RE.sub("", text)

TEXT_LIKE_TYPES = ("text", "ref_text", "equation")
IMAGE_LIKE_TYPES = ("image", "chart")


def _needles_for_block(block: dict) -> list[str]:
    """ブロックの型に応じた検索文字列の候補リストを返す（優先順）。"""
    block_type = block.get("type")

    if block_type in TEXT_LIKE_TYPES:
        text = block.get("text")
        return [text] if text else []

    if block_type in IMAGE_LIKE_TYPES:
        img_path = block.get("img_path")
        return [img_path] if img_path else []

    if block_type == "table":
        needles: list[str] = []
        table_body = (block.get("table_body") or "").strip()
        if table_body:
            needles.append(table_body)
            lines, reason = html_table_to_md.convert_table(table_body)
            if reason is None:
                needles.append("\n".join(lines))
        img_path = block.get("img_path")
        if img_path:
            needles.append(img_path)
        return needles

    return []


def locate_blocks(content_list: list, md: str) -> dict[int, tuple[int, int]]:
    """content_list の各ブロックの md 内出現位置を単調増加カーソルで探す。

    戻り値: ブロックインデックス -> (開始位置, 終了位置)。
    発見できないブロックはキーに含めない。
    """
    located: dict[int, tuple[int, int]] = {}
    cursor = 0

    for i, block in enumerate(content_list):
        if not isinstance(block, dict):
            continue

        needles = _needles_for_block(block)

        found_pos = -1
        found_needle = ""
        for needle in needles:
            if not needle:
                continue
            pos = md.find(needle, cursor)
            if pos >= 0:
                found_pos = pos
                found_needle = needle
                break

        if found_pos < 0:
            continue

        located[i] = (found_pos, found_pos + len(found_needle))
        cursor = found_pos + len(found_needle)

    return located


def assemble_notes(blocks: list[dict]) -> list[str]:
    """1 ページ分の page_footnote ブロックを組み立て済み脚注のリストに変換する。

    blocks: 同一ページの page_footnote ブロックのリスト（content_list 内の出現順）。
    """
    items: list[dict] = []
    for block in blocks:
        text = block.get("text") or ""
        text = text.strip()
        text = text.replace("\n", " ")
        if text == "":
            continue

        bbox = block.get("bbox")
        if not isinstance(bbox, list) or len(bbox) < 4:
            bbox = [0, 0, 0, 0]

        items.append({"text": text, "bbox": bbox})

    n = len(items)
    keys = [comparison_key(it["text"]) for it in items]

    is_fragment = [False] * n
    for i in range(n):
        if keys[i] == "":          # 追加: 空キーは他の任意文字列の部分文字列になってしまう
            continue
        for j in range(n):
            if i == j:
                continue
            if keys[i] != keys[j] and keys[i] in keys[j]:
                is_fragment[i] = True
                break

    seen: set[str] = set()
    kept_indices: list[int] = []
    for i in range(n):
        if is_fragment[i]:
            continue
        key = keys[i]
        if key != "" and key in seen:
            continue
        if key != "":
            seen.add(key)
        kept_indices.append(i)

    kept = [items[i] for i in kept_indices]
    kept.sort(key=lambda it: (it["bbox"][1], it["bbox"][0]))

    notes: list[str] = []
    for it in kept:
        text = it["text"]
        if NUM_PREFIX_RE.match(text):
            notes.append(text)
        elif notes:
            notes[-1] = notes[-1] + " " + text
        else:
            notes.append(text)

    return notes


def insert_notes(
    md: str, md_name: str, content_list: list
) -> tuple[str, int, int, list[str]]:
    """脚注の探索・組み立て・挿入を一括して行う。

    戻り値: (挿入後md, inserted, skipped, warnings)。
    """
    located = locate_blocks(content_list, md)

    page_last_end: dict[int, int] = {}
    for i, (_, end) in located.items():
        block = content_list[i]
        page_idx = block.get("page_idx")
        if not isinstance(page_idx, int):
            continue
        if page_idx not in page_last_end or end > page_last_end[page_idx]:
            page_last_end[page_idx] = end

    footnote_blocks_by_page: dict[int, list[dict]] = {}
    for block in content_list:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "page_footnote":
            continue
        page_idx = block.get("page_idx")
        if not isinstance(page_idx, int):
            continue
        footnote_blocks_by_page.setdefault(page_idx, []).append(block)

    notes_by_page: dict[int, list[str]] = {
        page_idx: assemble_notes(blocks)
        for page_idx, blocks in footnote_blocks_by_page.items()
    }

    inserted = 0
    skipped = 0
    warnings: list[str] = []
    inserts: list[tuple[int, str]] = []

    for page_idx in sorted(notes_by_page):
        notes = notes_by_page[page_idx]
        if not notes:
            continue

        if page_idx not in page_last_end:
            skipped += len(notes)
            warnings.append(
                f"{md_name}: page {page_idx}: no anchor; {len(notes)} note(s) skipped"
            )
            continue

        pos = md.find("\n\n", page_last_end[page_idx])
        ins = pos if pos >= 0 else len(md)

        chunk = ""
        for note in notes:
            if ("> " + note) in md:
                skipped += 1
                continue
            chunk += "\n\n> " + note
            inserted += 1

        if chunk:
            inserts.append((ins, chunk))

    for pos, chunk in sorted(inserts, key=lambda x: -x[0]):
        md = md[:pos] + chunk + md[pos:]

    return md, inserted, skipped, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="脚注挿入スクリプト（page_footnote ブロックを blockquote として md に挿入）"
    )
    parser.add_argument(
        "md",
        type=Path,
        help="入力 Markdown ファイル（UTF-8）",
    )
    parser.add_argument(
        "content_list",
        type=Path,
        help="対応する content_list JSON ファイル",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        required=True,
        help="出力ディレクトリ（md と同じベース名で書き出す）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="出力先の同名ファイルが既存でも上書きする（既定は拒否）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体制御。終了コードを返す。"""
    args = parse_args(argv)
    md_path: Path = args.md
    content_list_path: Path = args.content_list
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite

    try:
        md_text = md_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"failed to read md: {md_path} ({exc})", file=sys.stderr)
        return 1

    try:
        content_list_text = content_list_path.read_text(encoding="utf-8")
        content_list = json.loads(content_list_text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(
            f"failed to read content list: {content_list_path} ({exc})",
            file=sys.stderr,
        )
        return 1

    if not isinstance(content_list, list):
        print(f"content list is not a list: {content_list_path}", file=sys.stderr)
        return 1

    result, inserted, skipped, warnings = insert_notes(
        md_text, md_path.name, content_list
    )

    for warning in warnings:
        print(warning, file=sys.stderr)

    output_path = outdir / md_path.name
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        normalize_punct.write_text_atomic(result, output_path, overwrite)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"{md_path.name}: {inserted} inserted, {skipped} skipped")
    print(f"total: {inserted} inserted, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
