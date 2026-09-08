"""feat-024 M2-1: 層ごとの計数から母比率・Wilson 区間・推定件数を算出する CLI。

仕様は次の文書を参照する。
- docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/requirements.md（FR-M2-1-003）
- docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/design.md（§6）
- docs/issues/feat-024-inline-math-markup-survey/survey_notes.md（§9.1。式の典拠）

本スクリプトは feat-024 の案件固有の実験コードであり、プロダクトコードではない（design.md ADR-M2-1-1）。
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import tempfile
from pathlib import Path

Z: float = 1.959964

TSV_HEADER: str = "layer\tpopulation\tk\tn_eff\tp_hat\tci_lo\tci_hi\test_count\test_lo\test_hi"


def load_counts_tsv(path: Path) -> list[dict]:
    """計数 TSV を読み、population/k/n_eff を int 化した行の一覧を返す。"""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            row["population"] = int(row["population"])
            row["k"] = int(row["k"])
            row["n_eff"] = int(row["n_eff"])
            rows.append(row)
    return rows


def wilson_interval(k: int, n_eff: int, population: int) -> tuple[float, float, float]:
    """(p_hat, ci_lo, ci_hi) を返す（design.md §6.3。有限母集団修正込み）。"""
    p_hat = k / n_eff
    z2 = Z * Z
    center = (p_hat + z2 / (2 * n_eff)) / (1 + z2 / n_eff)
    half = (Z / (1 + z2 / n_eff)) * math.sqrt(p_hat * (1 - p_hat) / n_eff + z2 / (4 * n_eff**2))
    fpc = math.sqrt((population - n_eff) / (population - 1))
    half = half * fpc
    ci_lo = max(0.0, center - half)
    ci_hi = min(1.0, center + half)
    return p_hat, ci_lo, ci_hi


def write_tsv_atomic(rows: list[dict], out: Path) -> None:
    """§3.2 の手順で TSV を出力する。同一ディレクトリの一時ファイルに書き、
    os.replace で置換する。失敗時は一時ファイルを削除して例外を送出する。"""
    lines = [TSV_HEADER]
    for r in rows:
        lines.append(
            "\t".join(
                [
                    str(r["layer"]),
                    str(r["population"]),
                    str(r["k"]),
                    str(r["n_eff"]),
                    r["p_hat"],
                    r["ci_lo"],
                    r["ci_hi"],
                    r["est_count"],
                    r["est_lo"],
                    r["est_hi"],
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
        description="層ごとの計数から母比率・Wilson 区間・推定件数を算出する CLI"
    )
    parser.add_argument("--counts", type=Path, required=True, help="計数 TSV のパス")
    parser.add_argument("-o", "--out", type=Path, required=True, help="出力 TSV のパス")
    parser.add_argument("--overwrite", action="store_true", help="出力先が既存でも上書きする")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """終了コードを返す（0 = 成功、1 = エラー）。"""
    args = parse_args(argv)
    counts_path: Path = args.counts
    out: Path = args.out
    overwrite: bool = args.overwrite

    if not counts_path.is_file():
        print(f"counts tsv not found: {counts_path}", file=sys.stderr)
        return 1

    if not out.parent.is_dir():
        print(f"output dir not found: {out.parent}", file=sys.stderr)
        return 1
    if out.exists() and not overwrite:
        print(f"output exists (use --overwrite): {out}", file=sys.stderr)
        return 1

    try:
        rows = load_counts_tsv(counts_path)
    except (OSError, UnicodeDecodeError, csv.Error, KeyError, ValueError) as exc:
        print(f"counts tsv unreadable: {counts_path} ({exc})", file=sys.stderr)
        return 1

    if not rows:
        print(f"counts tsv has no data row: {counts_path}", file=sys.stderr)
        return 1

    for row in rows:
        layer = row["layer"]
        population = row["population"]
        k = row["k"]
        n_eff = row["n_eff"]
        if n_eff < 1:
            print(f"invalid row (n_eff must be >= 1): layer={layer}", file=sys.stderr)
            return 1
        if k < 0 or k > n_eff:
            print(f"invalid row (require 0 <= k <= n_eff): layer={layer}", file=sys.stderr)
            return 1
        if n_eff > population or population < 2:
            print(
                f"invalid row (require 2 <= population and n_eff <= population): layer={layer}",
                file=sys.stderr,
            )
            return 1

    out_rows: list[dict] = []
    for row in rows:
        population = row["population"]
        k = row["k"]
        n_eff = row["n_eff"]
        p_hat, ci_lo, ci_hi = wilson_interval(k, n_eff, population)
        est_count = population * p_hat
        est_lo = population * ci_lo
        est_hi = population * ci_hi
        out_rows.append(
            {
                "layer": row["layer"],
                "population": population,
                "k": k,
                "n_eff": n_eff,
                "p_hat": f"{p_hat:.12f}",
                "ci_lo": f"{ci_lo:.12f}",
                "ci_hi": f"{ci_hi:.12f}",
                "est_count": f"{est_count:.6f}",
                "est_lo": f"{est_lo:.6f}",
                "est_hi": f"{est_hi:.6f}",
            }
        )

    try:
        write_tsv_atomic(out_rows, out)
    except OSError as exc:
        print(f"write failed: {out} ({exc})", file=sys.stderr)
        return 1

    print(f"estimated: {len(out_rows)} layer(s)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
