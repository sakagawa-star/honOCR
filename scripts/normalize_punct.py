"""句読点正規化スクリプト。

MinerU 出力（Markdown・JSON）内の句読点「、」「。」を原本のスタイル
「，」「．」へ置換する（comma スタイル書籍向け）。また、MinerU が出力する
中国語字（簡体字・繁体字）を対応する日本語字へ常時置換し、規則化できない
残存 JIS 外漢字を警告する。詳細は
docs/issues/feat-004-punct-normalize/design.md および
docs/issues/feat-011-multi-book-normalization/design.md を参照。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

PUNCT_STYLES: tuple[str, ...] = ("comma", "touten")
DEFAULT_PUNCT_STYLE: str = "comma"

PUNCT_REPLACEMENTS: dict[str, dict[str, str]] = {
    "comma": {"、": "，", "。": "．"},
    "touten": {},
}

CJK_REPLACEMENTS: dict[str, str] = {
    "值": "値",
    "变": "変",
    "单": "単",
    "对": "対",
    "图": "図",
    "换": "換",
    "徵": "徴",
    "樣": "様",
}

CJK_RE: re.Pattern[str] = re.compile(r"[一-鿿]")
CONTEXT_CHARS: int = 25


def build_replacements(punct_style: str = DEFAULT_PUNCT_STYLE) -> dict[str, str]:
    """句読点置換（スタイル依存）と字形置換（常時）を合成した置換表を返す。"""
    return PUNCT_REPLACEMENTS[punct_style] | CJK_REPLACEMENTS


def normalize_text(
    text: str, punct_style: str = DEFAULT_PUNCT_STYLE
) -> tuple[str, int]:
    """置換後テキストと置換件数を返す。"""
    replacements = build_replacements(punct_style)
    count = sum(text.count(src) for src in replacements)
    normalized = text.translate(str.maketrans(replacements))
    return normalized, count


def is_jis_x0208(ch: str) -> bool:
    """文字が JIS X 0208 で表現できるかを返す。"""
    try:
        ch.encode("shift_jis")
    except UnicodeEncodeError:
        return False
    return True


def find_non_jis_kanji(text: str) -> dict[str, tuple[int, str]]:
    """JIS 外漢字 -> (出現件数, 最初の出現箇所の文脈) を返す。"""
    chars = set(CJK_RE.findall(text))
    found: dict[str, tuple[int, str]] = {}
    for ch in chars:
        if is_jis_x0208(ch):
            continue
        count = text.count(ch)
        pos = text.find(ch)
        context = text[max(0, pos - CONTEXT_CHARS):pos + CONTEXT_CHARS + 1]
        context = context.replace("\n", " ").replace("\r", " ")
        found[ch] = (count, context)
    return found


def format_non_jis_warning(name: str, found: dict[str, tuple[int, str]]) -> list[str]:
    """警告行のリストを返す（found が空なら空リスト）。"""
    if not found:
        return []

    total = sum(count for count, _ in found.values())
    lines = [f"{name}: JIS外漢字 {len(found)} 種 {total} 件"]
    for ch in sorted(found):
        count, context = found[ch]
        lines.append(f"  '{ch}' x{count}: ...{context}...")
    return lines


def validate_inputs(files: list[Path], outdir: Path, overwrite: bool) -> list[str]:
    """§4.2 の検証を行い、エラーメッセージのリストを返す（空 = 合格）。"""
    errors: list[str] = []

    for file_path in files:
        if not file_path.is_file():
            errors.append(f"not found: {file_path}")
            continue

        try:
            file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"not utf-8: {file_path}")

    basename_counts: dict[str, int] = {}
    for file_path in files:
        basename_counts[file_path.name] = basename_counts.get(file_path.name, 0) + 1
    for name, count in basename_counts.items():
        if count > 1:
            errors.append(f"duplicate basename: {name}")

    if not overwrite:
        for file_path in files:
            output_path = outdir / file_path.name
            if output_path.exists():
                errors.append(f"output exists: {output_path} (use --overwrite)")

    return errors


def write_text_atomic(text: str, output: Path, overwrite: bool) -> None:
    """原子的書き込み（feat-002 の write_pdf_atomic と同方式・テキスト版）。

    一時ファイル → fsync → 確定（overwrite=False: os.link による
    no-clobber / overwrite=True: os.replace）。失敗時（出力既存の
    FileExistsError を含む）は一時ファイルを削除して例外を送出する。
    """
    output.parent.mkdir(parents=True, exist_ok=True)

    tmp_file = tempfile.NamedTemporaryFile(
        dir=output.parent, suffix=".tmp", delete=False
    )
    tmp_path = Path(tmp_file.name)
    try:
        tmp_file.write(text.encode("utf-8"))
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_file.close()

        if overwrite:
            os.replace(tmp_path, output)
        else:
            os.link(tmp_path, output)
            os.unlink(tmp_path)
    except BaseException:
        tmp_file.close()
        if tmp_path.exists():
            os.unlink(tmp_path)
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="句読点正規化スクリプト（、。→，．）"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="入力ファイル（UTF-8 テキスト。Markdown / JSON を想定）",
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
    parser.add_argument(
        "--punct-style",
        choices=PUNCT_STYLES,
        default=DEFAULT_PUNCT_STYLE,
        help="句読点スタイル（comma: 、。→，．に置換 / touten: 句読点を置換しない。既定 comma）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体制御。終了コードを返す。"""
    args = parse_args(argv)
    files: list[Path] = args.files
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite

    errors = validate_inputs(files, outdir, overwrite)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    total = 0
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        normalized, count = normalize_text(text, args.punct_style)
        output_path = outdir / file_path.name

        try:
            write_text_atomic(normalized, output_path, overwrite)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

        for warning_line in format_non_jis_warning(file_path.name, find_non_jis_kanji(normalized)):
            print(warning_line, file=sys.stderr)

        print(f"{file_path.name}: {count} replaced")
        total += count

    print(f"total: {total} replaced in {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
