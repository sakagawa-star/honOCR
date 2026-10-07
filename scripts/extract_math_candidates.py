"""成果物 Markdown から、数式マークアップの外側にあるギリシャ文字・数学記号を
1 文字 1 件の候補レコードとして抽出する CLI。

候補の定義（対象文字集合・数式マークアップの範囲）は
`docs/issues/feat-025-inline-math-markup-survey/roadmap.md` §6 が正。
本ファイルはその実装。候補が真の欠落かどうかの判定は行わない。詳細は
`docs/issues/feat-025-inline-math-markup-survey/m1-extract-smoke/design.md` を参照。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# --- 数式マークアップの範囲（design.md §1.4.1） ---------------------------

MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]*?\$", re.DOTALL)
MASK_CHAR = "\x00"

# --- 対象文字集合（design.md §1.4.2 / roadmap.md §6 の転記） --------------

GREEK_LOW = 0x0370
GREEK_HIGH = 0x03FF
MATH_SYMBOLS = "≤≥≠≈≡∝∈∉⊂⊆⊃⊇∪∩∑∏∫√∞±∀∃¬∧∨∂∇⋯∼≪≫∅"  # 32 文字

# --- 候補レコードの文脈の長さ（design.md §1.4.3） --------------------------

CONTEXT_LEN = 40


def mask_math(md: str) -> str:
    """数式マークアップ（`$$…$$`・`$…$`）の範囲を、同じ文字数の `MASK_CHAR` に
    置き換えた文字列を返す（design.md §1.4.1）。長さは `md` と同じ。"""
    return MATH_RE.sub(lambda m: MASK_CHAR * len(m.group(0)), md)


def is_candidate_char(ch: str) -> bool:
    """`ch` が候補の対象文字集合に属するかを返す（design.md §1.4.2）。
    ギリシャ文字ブロック（U+0370〜U+03FF）または `MATH_SYMBOLS` に属する文字が真。"""
    cp = ord(ch)
    if GREEK_LOW <= cp <= GREEK_HIGH:
        return True
    return ch in MATH_SYMBOLS


def find_offsets(masked: str) -> list[int]:
    """マスク後の文字列から候補の開始位置を昇順で返す（design.md §1.4.2）。"""
    return [i for i, ch in enumerate(masked) if is_candidate_char(ch)]


def make_record(md: str, chapter: str, offset: int) -> dict[str, object]:
    """候補 1 件分のレコードを作る（design.md §1.4.3）。文脈はマスク前の
    原文 `md` から切り出す。前後 `CONTEXT_LEN` 文字を超えない範囲で、
    不足分は埋めない。"""
    return {
        "chapter": chapter,
        "offset": offset,
        "char": md[offset],
        "before": md[max(0, offset - CONTEXT_LEN):offset],
        "after": md[offset + 1:offset + 1 + CONTEXT_LEN],
    }


def scan_file(path: Path) -> list[dict[str, object]]:
    """1 ファイル分の候補レコードを生成する（design.md §1.4.5 手順 4-1〜4-3）。
    UTF-8 で読めない場合は `UnicodeDecodeError` を送出する（呼び出し側で処理）。"""
    md = path.read_text(encoding="utf-8")
    chapter = path.parent.name
    masked = mask_math(md)
    offsets = find_offsets(masked)
    return [make_record(md, chapter, offset) for offset in offsets]


def _check_output_writable(out: Path, overwrite: bool) -> None:
    """出力先の保護判定（design.md §1.4.4「出力先の判定」）。
    問題があれば書き込まずに例外を送出する。判定順序を厳守する。"""
    if out.exists() and not overwrite:
        raise FileExistsError(
            f"出力先が既に存在する: {out}（上書きするには --overwrite を付ける）"
        )
    if out.exists() and out.is_dir():
        raise IsADirectoryError(f"出力先がディレクトリである: {out}")


def write_jsonl(records: list[dict[str, object]], out: Path, overwrite: bool) -> None:
    """候補レコードを JSONL として原子的に書き込む（design.md §1.4.4）。
    出力先の保護判定に掛かった場合は書き込まずに例外を送出する。
    `records` が空でも 0 バイトのファイルを作る。"""
    _check_output_writable(out, overwrite)

    out.parent.mkdir(parents=True, exist_ok=True)

    content = "".join(
        json.dumps(rec, ensure_ascii=False) + "\n" for rec in records
    )

    fd, tmp_name = tempfile.mkstemp(dir=out.parent, prefix=f".{out.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp_path, out)
    except OSError:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析（design.md §1.4.5）。"""
    parser = argparse.ArgumentParser(
        description=(
            "成果物 Markdown から数式マークアップ外のギリシャ文字・数学記号の"
            "候補を抽出する CLI"
        )
    )
    parser.add_argument(
        "md_files",
        type=Path,
        nargs="+",
        help="入力 Markdown のパス（1個以上）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="出力先の JSONL のパス",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="出力先が存在するとき上書きする（既定は拒否）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体の制御。終了コードを返す（`sys.exit` を内部で呼ばない。design.md §1.7）。"""
    args = parse_args(argv)
    md_files: list[Path] = args.md_files
    out: Path = args.output
    overwrite: bool = args.overwrite

    # 手順2: すべての入力ファイルの存在と種類を先に確認する（1個目を処理する前に全件を確認する）
    for path in md_files:
        if path.is_file():
            continue
        if not path.exists():
            print(f"入力ファイルが存在しない: {path}", file=sys.stderr)
        else:
            print(f"入力がファイルではない: {path}", file=sys.stderr)
        return 1

    # 手順3: 出力先の判定
    try:
        _check_output_writable(out, overwrite)
    except (FileExistsError, IsADirectoryError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # 手順4: 入力ファイルを指定順に処理する
    all_records: list[dict[str, object]] = []
    for path in md_files:
        try:
            records = scan_file(path)
        except UnicodeDecodeError:
            print(f"UTF-8として読めない: {path}", file=sys.stderr)
            return 1
        print(f"{path}: {len(records)} 件", file=sys.stderr)
        all_records.extend(records)

    # 手順5: 出力
    write_jsonl(all_records, out, overwrite)

    # 手順6
    print(f"合計: {len(all_records)} 件 → {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
