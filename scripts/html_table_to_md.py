"""HTML 表 → Markdown パイプテーブル変換スクリプト。

MinerU 出力（正規化済み Markdown）内の HTML 表（`<table>…</table>` が
1 行で完結しているもの）を GFM パイプテーブルに変換する。詳細は
docs/issues/feat-008-html-table-to-md/design.md を参照。
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import normalize_punct

TAG_SPLIT_RE = re.compile(
    r"(</?(?:table|thead|tbody|tr|td|th)\b[^>]*>)", re.IGNORECASE
)
TAG_MATCH_RE = re.compile(r"<(/?)([A-Za-z]+)([^>]*)>")
UNSUPPORTED_TAG_RE = re.compile(r"</?[A-Za-z]+(\s[^<>]*)?>")


def convert_table(table_html: str) -> tuple[list[str], str | None]:
    """1 個の HTML 表文字列をパイプテーブル行のリストに変換する。

    戻り値は (lines, None)（成功）または ([], reason)（スキップ）。
    """
    parts = TAG_SPLIT_RE.split(table_html)

    rows: list[list[str]] = []
    current_row: list[str] | None = None
    cell: list[str] | None = None

    for i, part in enumerate(parts):
        if i % 2 == 1:
            m = TAG_MATCH_RE.fullmatch(part)
            is_close = m.group(1) == "/"
            name = m.group(2).lower()
            attrs = m.group(3)

            if attrs.strip() != "":
                return [], f"attribute on <{name}>"

            if name in ("table", "thead", "tbody"):
                continue

            if name == "tr":
                if not is_close:
                    current_row = []
                else:
                    if current_row is None:
                        return [], "malformed structure"
                    rows.append(current_row)
                    current_row = None
            elif name in ("td", "th"):
                if not is_close:
                    if current_row is None:
                        return [], "malformed structure"
                    cell = []
                else:
                    if cell is None:
                        return [], "malformed structure"
                    s = html.unescape("".join(cell)).strip()
                    if UNSUPPORTED_TAG_RE.search(s):
                        return [], "unsupported tag in cell"
                    current_row.append(s)
                    cell = None
        else:
            if cell is not None:
                cell.append(part)
            elif part.strip() != "":
                return [], "text outside cell"

    if current_row is not None or cell is not None:
        return [], "malformed structure"

    if len(rows) == 0:
        return [], "no rows"

    n = len(rows[0])
    if n == 0:
        return [], "no columns"
    for row in rows:
        if len(row) != n:
            return [], "ragged rows"

    for row in rows:
        for c in row:
            if "|" in c:
                return [], "pipe in cell"

    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("|" + " --- |" * n)
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return lines, None


def convert_text(text: str, name: str) -> tuple[str, int, int, list[str]]:
    """Markdown 全文を変換する。

    戻り値は (変換後テキスト, 変換件数, スキップ件数, 警告メッセージのリスト)。
    """
    lines = text.split("\n")
    out: list[str] = []
    converted = 0
    skipped = 0
    warnings: list[str] = []

    n_lines = len(lines)
    for i in range(n_lines):
        line = lines[i]
        body = line.rstrip("\r")
        cr = line[len(body):]
        stripped = body.strip()

        if stripped.startswith("<table") and stripped.endswith("</table>"):
            table_lines, reason = convert_table(stripped)
            if reason is not None:
                out.append(line)
                skipped += 1
                warnings.append(f"{name}:{i + 1}: skipped ({reason})")
            else:
                if out and out[-1].strip() != "":
                    out.append(cr)
                for table_line in table_lines:
                    out.append(table_line + cr)
                if i + 1 < n_lines and lines[i + 1].strip() != "":
                    out.append(cr)
                converted += 1
        elif "<table" in line:
            out.append(line)
            skipped += 1
            warnings.append(f"{name}:{i + 1}: skipped (multi-line table)")
        else:
            out.append(line)

    return "\n".join(out), converted, skipped, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="HTML表 → Markdown パイプテーブル変換スクリプト"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="入力ファイル（UTF-8 テキスト。Markdown を想定）",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        required=True,
        help="出力ディレクトリ（同じベース名で書き出す）",
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
    files: list[Path] = args.files
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite

    errors = normalize_punct.validate_inputs(files, outdir, overwrite)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    total_converted = 0
    total_skipped = 0
    for file_path in files:
        text = file_path.read_bytes().decode("utf-8")
        converted_text, converted, skipped, warnings = convert_text(
            text, file_path.name
        )
        output_path = outdir / file_path.name

        for warning in warnings:
            print(warning, file=sys.stderr)

        try:
            normalize_punct.write_text_atomic(converted_text, output_path, overwrite)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(f"{file_path.name}: {converted} converted, {skipped} skipped")
        total_converted += converted
        total_skipped += skipped

    print(
        f"total: {total_converted} converted, {total_skipped} skipped "
        f"in {len(files)} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
