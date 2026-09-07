"""feat-024 M2 検査2: feat-021 の D4（数式の不一致）16件が母集団に含まれるかを確認する。

判定基準・手順は次の文書を参照する。
- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/requirements.md（FR-M2-002）
- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/design.md（§5）

本スクリプトは feat-024 の案件固有の検査スクリプトであり、プロダクトコードではない
（design.md ADR-M2-2 と同じ扱い）。判定（Go/No-Go）は行わない。
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from pathlib import Path

D4_TARGETS: tuple[tuple[str, str], ...] = (
    ("chap02", "2.1"), ("chap02", "2.4"), ("chap02", "2.7"), ("chap02", "2.12"),
    ("chap03", "3.3"),
    ("chap04", "4.5"), ("chap04", "4.8"),
    ("chap05", "5.1"), ("chap05", "5.6"),
    ("chap07", "7.1"), ("chap07", "7.3"), ("chap07", "7.4"),
    ("chap08", "8.4"), ("chap08", "8.7"),
    ("chap09", "A.2"), ("chap09", "B.1"),
)

TSV_HEADER: str = (
    "chapter\tnumber\theading_line\tstatus\tn_candidates\tkinds\tlocation\t"
    "not_covered_reason\theading_text"
)


def _sanitize(s: str) -> str:
    return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def load_candidate_index(candidates_path: Path) -> dict[tuple[str, int], list[dict]]:
    """候補 TSV を読み、(chapter, line) をキーに候補をまとめる（design.md §5.2 手順1）。"""
    index: dict[tuple[str, int], list[dict]] = {}
    with candidates_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            key = (row["chapter"], int(row["line"]))
            index.setdefault(key, []).append(row)
    return index


def find_heading_line(md_lines: list[str], number: str) -> int:
    """見出し行を探す（design.md §5.2 手順2-1）。
    ちょうど1行なら行番号（1始まり）、0行または2行以上なら -1 を返す。"""
    pattern = re.compile(r"^##\s+\?\s*" + re.escape(number) + r"(\s|$)")
    matches = [i + 1 for i, line in enumerate(md_lines) if pattern.match(line)]
    if len(matches) == 1:
        return matches[0]
    return -1


def check_target(
    chapter: str,
    number: str,
    md_lines: list[str],
    index: dict[tuple[str, int], list[dict]],
) -> dict:
    """D4_TARGETS の1件を検査し、出力行（dict）を返す（design.md §5.2・§5.3）。"""
    heading_line = find_heading_line(md_lines, number)
    if heading_line == -1:
        return {
            "chapter": chapter,
            "number": number,
            "heading_line": -1,
            "status": "heading_not_found",
            "n_candidates": 0,
            "kinds": "G=0,L=0,C=0",
            "location": "",
            "not_covered_reason": "",
            "heading_text": "",
        }

    heading_text = md_lines[heading_line - 1]
    all_cands = index.get((chapter, heading_line), [])
    pop_cands = [r for r in all_cands if r["location"] != "table"]

    n_g = sum(1 for r in all_cands if r["kind"] == "G")
    n_l = sum(1 for r in all_cands if r["kind"] == "L")
    n_c = sum(1 for r in all_cands if r["kind"] == "C")
    kinds = f"G={n_g},L={n_l},C={n_c}"
    location = ";".join(sorted({r["location"] for r in all_cands}))

    if len(pop_cands) >= 1:
        status = "covered"
        not_covered_reason = ""
    elif len(all_cands) == 0:
        status = "not_covered"
        not_covered_reason = "no_symbol"
    else:
        status = "not_covered"
        not_covered_reason = "table_only"

    return {
        "chapter": chapter,
        "number": number,
        "heading_line": heading_line,
        "status": status,
        "n_candidates": len(all_cands),
        "kinds": kinds,
        "location": location,
        "not_covered_reason": not_covered_reason,
        "heading_text": _sanitize(heading_text),
    }


def write_tsv_atomic(rows: list[dict], out: Path) -> None:
    """§5.3 の TSV を出力する。同一ディレクトリの一時ファイルに書き、
    os.replace で置換する（../m1-scan-cli/design.md §5.1 と同じ手順）。"""
    lines = [TSV_HEADER]
    for r in rows:
        lines.append(
            "\t".join(
                [
                    str(r["chapter"]),
                    str(r["number"]),
                    str(r["heading_line"]),
                    str(r["status"]),
                    str(r["n_candidates"]),
                    str(r["kinds"]),
                    str(r["location"]),
                    str(r["not_covered_reason"]),
                    str(r["heading_text"]),
                ]
            )
        )
    content = "\n".join(lines) + "\n"

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
        description="feat-021 の D4（数式の不一致）16件が母集団に含まれるかを確認する検査スクリプト"
    )
    parser.add_argument("--candidates", type=Path, required=True, help="候補 TSV のパス")
    parser.add_argument(
        "--final-root", type=Path, required=True, help="{BASE2}/ocr/final（章ディレクトリの親）"
    )
    parser.add_argument("-o", "--out", type=Path, required=True, help="出力 TSV のパス")
    parser.add_argument("--overwrite", action="store_true", help="既存ファイルの上書きを許可する")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """終了コードを返す（0 = 成功、1 = エラー）。"""
    args = parse_args(argv)
    candidates_path: Path = args.candidates
    final_root: Path = args.final_root
    out: Path = args.out
    overwrite: bool = args.overwrite

    if not candidates_path.is_file():
        print(f"candidates tsv not found: {candidates_path}", file=sys.stderr)
        return 1
    try:
        index = load_candidate_index(candidates_path)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"candidates tsv unreadable: {candidates_path} ({exc})", file=sys.stderr)
        return 1

    if not final_root.is_dir():
        print(f"final-root not found: {final_root}", file=sys.stderr)
        return 1

    if not out.parent.is_dir():
        print(f"output dir not found: {out.parent}", file=sys.stderr)
        return 1
    if out.exists() and not overwrite:
        print(f"output exists (use --overwrite): {out}", file=sys.stderr)
        return 1

    rows: list[dict] = []
    for chapter, number in D4_TARGETS:
        md_path = final_root / chapter / f"{chapter}_gray300.md"
        if not md_path.is_file():
            print(f"md not found: {md_path}", file=sys.stderr)
            return 1
        try:
            md_text = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            print(f"md unreadable: {md_path} ({exc})", file=sys.stderr)
            return 1
        md_lines = md_text.split("\n")
        rows.append(check_target(chapter, number, md_lines, index))

    try:
        write_tsv_atomic(rows, out)
    except OSError as exc:
        print(f"write failed: {out} ({exc})", file=sys.stderr)
        return 1

    covered = sum(1 for r in rows if r["status"] == "covered")
    not_covered = sum(1 for r in rows if r["status"] == "not_covered")
    heading_not_found = sum(1 for r in rows if r["status"] == "heading_not_found")
    no_symbol = sum(1 for r in rows if r["not_covered_reason"] == "no_symbol")
    table_only = sum(1 for r in rows if r["not_covered_reason"] == "table_only")

    print(
        f"d4 coverage: covered={covered} not_covered={not_covered} "
        f"heading_not_found={heading_not_found} (total {len(rows)})",
        file=sys.stderr,
    )
    print(f"not_covered breakdown: no_symbol={no_symbol} table_only={table_only}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
