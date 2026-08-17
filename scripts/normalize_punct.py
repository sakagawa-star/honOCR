"""句読点正規化スクリプト。

MinerU 出力（Markdown・JSON）内の句読点「、」「。」を原本のスタイル
「，」「．」へ置換する。詳細は
docs/issues/feat-004-punct-normalize/design.md を参照。
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

REPLACEMENTS: dict[str, str] = {"、": "，", "。": "．"}
TRANSLATION_TABLE = str.maketrans(REPLACEMENTS)


def normalize_text(text: str) -> tuple[str, int]:
    """置換後テキストと置換件数を返す。"""
    count = sum(text.count(src) for src in REPLACEMENTS)
    normalized = text.translate(TRANSLATION_TABLE)
    return normalized, count


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
        normalized, count = normalize_text(text)
        output_path = outdir / file_path.name

        try:
            write_text_atomic(normalized, output_path, overwrite)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(f"{file_path.name}: {count} replaced")
        total += count

    print(f"total: {total} replaced in {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
