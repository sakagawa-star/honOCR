"""成果物 md から数式マークアップ外の候補（候補G・候補L・候補C）を抽出する CLI。

候補の定義は `docs/issues/feat-024-inline-math-markup-survey/survey_notes.md` §3 が正。
本ファイルはその実装。判定（欠落かどうか）は行わない。詳細は
`docs/issues/feat-024-inline-math-markup-survey/m1-scan-cli/design.md` を参照。
"""

from __future__ import annotations

import argparse
import bisect
import os
import re
import sys
import tempfile
from pathlib import Path

# --- 候補の定義に使う定数（survey_notes.md §3 手順4・5） -----------------

GREEK_LOW: int = 0x0370
GREEK_HIGH: int = 0x03FF

HIRAGANA_LOW: int = 0x3041
HIRAGANA_HIGH: int = 0x309F
KATAKANA_LOW: int = 0x30A0
KATAKANA_HIGH: int = 0x30FF
CJK_LOW: int = 0x4E00
CJK_HIGH: int = 0x9FFF

JAPANESE_PUNCTUATION: str = "、。，．・「」（）"

# --- 除外領域・インライン数式の正規表現（survey_notes.md §3 手順1〜3） ----

CODE_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
MATH_BLOCK_RE = re.compile(r"^\$\$.*?^\$\$", re.MULTILINE | re.DOTALL)
IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
INLINE_MATH_RE = re.compile(r"\$[^$\n]+\$")

# --- TSV の出力形式（design.md §3.2） -------------------------------------

TSV_HEADER: str = "chapter\tline\toffset\tkind\tlocation\tsymbol\tcontext"
CONTEXT_MARGIN: int = 15


def is_japanese(ch: str) -> bool:
    """../survey_notes.md §3 手順5 の日本語文字の定義に合致するかを返す。"""
    cp = ord(ch)
    if HIRAGANA_LOW <= cp <= HIRAGANA_HIGH:
        return True
    if KATAKANA_LOW <= cp <= KATAKANA_HIGH:
        return True
    if CJK_LOW <= cp <= CJK_HIGH:
        return True
    return ch in JAPANESE_PUNCTUATION


def is_greek(ch: str) -> bool:
    """コードポイントが U+0370〜U+03FF かを返す。"""
    return GREEK_LOW <= ord(ch) <= GREEK_HIGH


def _zero_out(m: re.Match) -> str:
    return "\x00" * len(m.group())


def mask_regions(md: str) -> tuple[str, list[tuple[int, str]]]:
    """§4.1 手順1〜3 を適用し、(マスク文字列, [(開始オフセット, インライン数式の全文), ...]) を返す。
    マスク文字列の長さは md と等しい。"""
    masked = CODE_FENCE_RE.sub(_zero_out, md)
    masked = MATH_BLOCK_RE.sub(_zero_out, masked)
    masked = IMAGE_REF_RE.sub(_zero_out, masked)

    inline_math: list[tuple[int, str]] = []
    matches = list(INLINE_MATH_RE.finditer(masked))
    if matches:
        chars = list(masked)
        for m in matches:
            inline_math.append((m.start(), m.group()))
            chars[m.start() : m.end()] = "\x00" * (m.end() - m.start())
        masked = "".join(chars)

    return masked, inline_math


def line_starts(md: str) -> list[int]:
    """各行の開始オフセットの配列を返す（bisect 用。先頭要素は 0）。"""
    starts = [0]
    for i, ch in enumerate(md):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def classify_location(md: str, starts: list[int], offset: int) -> str:
    """候補の所在（"body" / "footnote" / "table"）を返す。"""
    idx = bisect.bisect_right(starts, offset) - 1
    line_start = starts[idx]
    line_end = starts[idx + 1] - 1 if idx + 1 < len(starts) else len(md)
    line = md[line_start:line_end]
    stripped = line.strip()
    if stripped.startswith("|"):
        return "table"
    if stripped.startswith(">"):
        return "footnote"
    return "body"


def _left_ok(s: str, i: int) -> bool:
    if i - 1 < 0:
        return False
    prev = s[i - 1]
    if is_japanese(prev):
        return True
    if prev.isspace() and i - 2 >= 0 and is_japanese(s[i - 2]):
        return True
    return False


def _right_ok(s: str, i: int) -> bool:
    n = len(s)
    if i + 1 >= n:
        return False
    nxt = s[i + 1]
    if is_japanese(nxt):
        return True
    if nxt.isspace() and i + 2 < n and is_japanese(s[i + 2]):
        return True
    return False


def find_candidates(md: str) -> list[tuple[str, int, str]]:
    """md 全文から候補を抽出し、(kind, offset, symbol) の一覧を返す。
    kind は "G" / "L" / "C"。順序は問わない（呼び出し側でソートする）。"""
    masked, inline_math = mask_regions(md)

    candidates: list[tuple[str, int, str]] = []
    for offset, symbol in inline_math:
        candidates.append(("C", offset, symbol))

    for i, ch in enumerate(masked):
        if is_greek(ch):
            candidates.append(("G", i, ch))
            continue
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            if _left_ok(masked, i) and _right_ok(masked, i):
                candidates.append(("L", i, ch))

    return candidates


def _sanitize(s: str) -> str:
    return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def scan_md(path: Path, kinds: set[str]) -> list[dict]:
    """1つの md を走査し、§3.2 の列をキーに持つ dict の一覧を返す。"""
    md = path.read_text(encoding="utf-8")
    chapter = path.parent.name
    starts = line_starts(md)

    rows: list[dict] = []
    for kind, offset, symbol in find_candidates(md):
        if kind not in kinds:
            continue
        line = bisect.bisect_right(starts, offset)
        location = classify_location(md, starts, offset)
        context = md[max(0, offset - CONTEXT_MARGIN) : offset + len(symbol) + CONTEXT_MARGIN]
        rows.append(
            {
                "chapter": chapter,
                "line": line,
                "offset": offset,
                "kind": kind,
                "location": location,
                "symbol": _sanitize(symbol),
                "context": _sanitize(context),
            }
        )
    return rows


def _format_tsv(rows: list[dict]) -> str:
    lines = [TSV_HEADER]
    for r in rows:
        lines.append(
            "\t".join(
                [
                    str(r["chapter"]),
                    str(r["line"]),
                    str(r["offset"]),
                    str(r["kind"]),
                    str(r["location"]),
                    str(r["symbol"]),
                    str(r["context"]),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def write_tsv_atomic(rows: list[dict], out: Path) -> None:
    """§5.1 の手順で TSV を出力する。同一ディレクトリの一時ファイルに書き、
    os.replace で置換する。失敗時は一時ファイルを削除して例外を送出する。"""
    content = _format_tsv(rows)
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
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="成果物 md から数式マークアップ外の候補（候補G・候補L・候補C）を抽出する CLI"
    )
    parser.add_argument(
        "md",
        type=Path,
        nargs="+",
        help="成果物 md のパス（1個以上）",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="TSV の出力先（既定: 標準出力）",
    )
    parser.add_argument(
        "--kind",
        choices=["G", "L", "C", "all"],
        default="all",
        help="出力する候補の種別（既定: all）",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="--out の既存ファイルを上書きする（既定は拒否）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """終了コードを返す（0 = 成功、1 = エラー）。"""
    args = parse_args(argv)
    md_paths: list[Path] = args.md
    out: Path | None = args.out
    kind: str = args.kind
    overwrite: bool = args.overwrite

    kinds: set[str] = {"G", "L", "C"} if kind == "all" else {kind}

    all_rows: list[dict] = []
    total_chars = 0

    for path in md_paths:
        if not path.is_file():
            print(f"md not found: {path}", file=sys.stderr)
            return 1
        try:
            md = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            print(f"md unreadable: {path} ({exc})", file=sys.stderr)
            return 1
        total_chars += len(md)
        rows = scan_md(path, kinds)
        all_rows.extend(rows)

    all_rows.sort(key=lambda r: (r["chapter"], r["offset"], r["kind"]))

    if out is not None:
        if not out.parent.is_dir():
            print(f"output dir not found: {out.parent}", file=sys.stderr)
            return 1
        if out.exists() and not overwrite:
            print(f"output exists (use --overwrite): {out}", file=sys.stderr)
            return 1
        try:
            write_tsv_atomic(all_rows, out)
        except OSError as exc:
            print(f"write failed: {out} ({exc})", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(_format_tsv(all_rows))

    g = sum(1 for r in all_rows if r["kind"] == "G")
    l_ = sum(1 for r in all_rows if r["kind"] == "L")
    c = sum(1 for r in all_rows if r["kind"] == "C")
    total = len(all_rows)
    body = sum(1 for r in all_rows if r["location"] == "body")
    footnote = sum(1 for r in all_rows if r["location"] == "footnote")
    table = sum(1 for r in all_rows if r["location"] == "table")

    print(f"scanned {len(md_paths)} file(s), {total_chars} char(s)", file=sys.stderr)
    print(f"candidates: G={g} L={l_} C={c} total={total}", file=sys.stderr)
    print(f"location: body={body} footnote={footnote} table={table}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
