"""feat-024 M2-1: 候補 TSV から層ごとの母集団を無作為抽出する CLI。

仕様は次の文書を参照する。
- docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/requirements.md（FR-M2-1-001）
- docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/design.md（§4）

本スクリプトは feat-024 の案件固有の実験コードであり、プロダクトコードではない（design.md ADR-M2-1-1）。
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import tempfile
from pathlib import Path

TSV_HEADER: str = "chapter\tline\toffset\tkind\tlocation\tsymbol\tcontext"


def load_candidates_tsv(path: Path) -> list[dict]:
    """候補 TSV を読み、line/offset を int 化した行の一覧を返す。"""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            row["line"] = int(row["line"])
            row["offset"] = int(row["offset"])
            rows.append(row)
    return rows


def select_population(rows: list[dict], kind: str) -> list[dict]:
    """`location != "table"` かつ `kind == 指定の層` の行を、(chapter, offset) 昇順で返す。"""
    population = [r for r in rows if r["location"] != "table" and r["kind"] == kind]
    population.sort(key=lambda r: (r["chapter"], r["offset"]))
    return population


def sample_rows(population: list[dict], size: int, seed: int) -> list[dict]:
    """母集団（正準順序）から size 件を無作為抽出し、(chapter, offset) 昇順で返す。"""
    rng = random.Random(seed)
    sampled = rng.sample(population, size)
    sampled.sort(key=lambda r: (r["chapter"], r["offset"]))
    return sampled


def write_tsv_atomic(rows: list[dict], out: Path) -> None:
    """§3.2 の手順で TSV を出力する。同一ディレクトリの一時ファイルに書き、
    os.replace で置換する。失敗時は一時ファイルを削除して例外を送出する。"""
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
        description="候補 TSV から層ごとの母集団を無作為抽出する CLI"
    )
    parser.add_argument("--candidates", type=Path, required=True, help="候補 TSV のパス")
    parser.add_argument("--kind", choices=["G", "L", "C"], required=True, help="層")
    parser.add_argument("--size", type=int, required=True, help="抽出件数")
    parser.add_argument("--seed", type=int, required=True, help="乱数シード")
    parser.add_argument("-o", "--out", type=Path, required=True, help="出力 TSV のパス")
    parser.add_argument("--overwrite", action="store_true", help="出力先が既存でも上書きする")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """終了コードを返す（0 = 成功、1 = エラー）。"""
    args = parse_args(argv)
    candidates_path: Path = args.candidates
    kind: str = args.kind
    size: int = args.size
    seed: int = args.seed
    out: Path = args.out
    overwrite: bool = args.overwrite

    if size <= 0:
        print(f"size must be positive: {size}", file=sys.stderr)
        return 1

    if not candidates_path.is_file():
        print(f"candidates tsv not found: {candidates_path}", file=sys.stderr)
        return 1

    if not out.parent.is_dir():
        print(f"output dir not found: {out.parent}", file=sys.stderr)
        return 1
    if out.exists() and not overwrite:
        print(f"output exists (use --overwrite): {out}", file=sys.stderr)
        return 1

    try:
        rows = load_candidates_tsv(candidates_path)
    except (OSError, UnicodeDecodeError, csv.Error, KeyError, ValueError) as exc:
        print(f"candidates tsv unreadable: {candidates_path} ({exc})", file=sys.stderr)
        return 1

    population = select_population(rows, kind)

    if size > len(population):
        print(
            f"size {size} exceeds population size {len(population)} for kind {kind}",
            file=sys.stderr,
        )
        return 1

    sampled = sample_rows(population, size, seed)

    try:
        write_tsv_atomic(sampled, out)
    except OSError as exc:
        print(f"write failed: {out} ({exc})", file=sys.stderr)
        return 1

    print(
        f"sampled: kind={kind} size={size} population={len(population)} seed={seed}",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
