"""修正適用スクリプト。

OCR 誤りの手動修正を「修正前文字列（old）→ 修正後文字列（new）」のペアと
して記録した修正定義ファイル（JSON）を Markdown に機械適用する。詳細は
docs/issues/feat-010-apply-fixes/design.md を参照。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import normalize_punct


def validate_fixes(data: object, fixes_name: str) -> list[str]:
    """修正定義ファイルのスキーマ検証（design.md §4.2）。

    戻り値: エラーメッセージのリスト（空 = 合格）。
    """
    errors: list[str] = []

    if not isinstance(data, dict) or "fixes" not in data:
        errors.append(f"{fixes_name}: top level must be a dict with a 'fixes' key")
        return errors

    fixes = data["fixes"]
    if not isinstance(fixes, list):
        errors.append(f"{fixes_name}: 'fixes' must be a list")
        return errors

    seen_ids: set[str] = set()
    for i, fix in enumerate(fixes):
        if not isinstance(fix, dict):
            errors.append(f"{fixes_name}: fix[{i}] must be a dict")
            continue

        missing_or_bad_type = [
            k
            for k in ("id", "reason", "old", "new")
            if k not in fix or not isinstance(fix[k], str)
        ]
        if missing_or_bad_type:
            errors.append(
                f"{fixes_name}: fix[{i}] missing required string key(s): "
                f"{missing_or_bad_type}"
            )
            continue

        fid = fix["id"]
        old = fix["old"]
        new = fix["new"]

        if fid == "":
            errors.append(f"{fixes_name}: fix[{i}] id must be non-empty")
        elif fid in seen_ids:
            errors.append(f"{fixes_name}: fix[{i}] id is not unique: {fid!r}")
        else:
            seen_ids.add(fid)

        if old == "":
            errors.append(f"{fixes_name}: fix[{i}] ({fid!r}) old must be non-empty")

        if new == "":
            errors.append(f"{fixes_name}: fix[{i}] ({fid!r}) new must be non-empty")

        if old == new:
            errors.append(f"{fixes_name}: fix[{i}] ({fid!r}) old and new must differ")

    return errors


def apply_fixes(
    md: str, fixes: list[dict], fixes_name: str
) -> tuple[str, int, int, list[str]]:
    """修正定義を記載順に逐次適用する（design.md §4.3）。

    戻り値: (適用後md, applied, skipped, errors)。errors が非空のとき
    適用後md は使用しない。
    """
    applied = 0
    skipped = 0
    errors: list[str] = []

    for fix in fixes:
        fid = fix["id"]
        old = fix["old"]
        new = fix["new"]

        n_old = md.count(old)
        if n_old == 1:
            md = md.replace(old, new, 1)
            applied += 1
        elif n_old == 0:
            n_new = md.count(new)
            if n_new == 1:
                skipped += 1
            elif n_new == 0:
                errors.append(
                    f"{fixes_name}: {fid}: old not found (old[:40]={old[:40]!r})"
                )
            else:
                errors.append(
                    f"{fixes_name}: {fid}: ambiguous - new found {n_new} times"
                )
        else:
            errors.append(f"{fixes_name}: {fid}: old is not unique ({n_old} occurrences)")

    if not errors:
        # 最終不変条件（FR-003 規則 6）: 出力前に全 fix の
        # count(old) == 0 かつ count(new) == 1 を検査する。
        for fix in fixes:
            fid = fix["id"]
            old = fix["old"]
            new = fix["new"]

            n_old_final = md.count(old)
            n_new_final = md.count(new)

            if n_old_final != 0:
                errors.append(
                    f"{fixes_name}: {fid}: final invariant violated - "
                    f"old still present ({n_old_final} occurrences)"
                )
            if n_new_final != 1:
                errors.append(
                    f"{fixes_name}: {fid}: final invariant violated - "
                    f"new count is {n_new_final}"
                )

    return md, applied, skipped, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="修正適用スクリプト（修正定義ファイルの old→new ペアを md に機械適用する）"
    )
    parser.add_argument(
        "md",
        type=Path,
        help="入力 Markdown ファイル（UTF-8）",
    )
    parser.add_argument(
        "fixes",
        type=Path,
        help="修正定義ファイル（JSON）",
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
    fixes_path: Path = args.fixes
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite

    try:
        md_text = md_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"failed to read md: {md_path} ({exc})", file=sys.stderr)
        return 1

    try:
        data = json.loads(fixes_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"failed to read fixes: {fixes_path} ({exc})", file=sys.stderr)
        return 1

    validation_errors = validate_fixes(data, fixes_path.name)
    if validation_errors:
        for error in validation_errors:
            print(error, file=sys.stderr)
        return 1

    fixes = data["fixes"]
    result, applied, skipped, errors = apply_fixes(md_text, fixes, fixes_path.name)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    outdir.mkdir(parents=True, exist_ok=True)
    output_path = outdir / md_path.name

    try:
        normalize_punct.write_text_atomic(result, output_path, overwrite)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"{md_path.name}: {applied} applied, {skipped} skipped")
    print(f"total: {applied} applied, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
