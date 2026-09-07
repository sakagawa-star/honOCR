"""feat-024 M2/M3 共通: 候補の原本ページ（content_list のブロック）への逆引きスクリプト。

判定基準・手順は次の文書を参照する。
- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/requirements.md（FR-M2-003）
- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/design.md（§6・§7）
- docs/issues/feat-024-inline-math-markup-survey/survey_notes.md（§7。正規化関数と予備実測）

本スクリプトは feat-024 の案件固有の検査・実験スクリプトであり、プロダクトコードではない
（design.md ADR-M2-2）。M2 では --sample-size で検査標本を無作為抽出して逆引きし、
M3 では --input-sample で既存の標本 TSV を逆引きする。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
import tempfile
from pathlib import Path

NORM_RE = re.compile(r"[\s#>|*\\_`\-:]+")

MAX_NEIGHBOR_SEARCH: int = 200
KEY_MARGIN_SHORT: int = 10
KEY_MARGIN_LONG: int = 30

TSV_HEADER: str = (
    "chapter\tline\toffset\tkind\tlocation\tsymbol\tcontext\t"
    "stage\tblock_index\tpage_idx\treason"
)


def norm(s: str) -> str:
    """md と content_list の表記差を吸収する正規化。
    正規表現 [\\s#>|*\\\\_`\\-:]+ にマッチする文字をすべて除去する。"""
    return NORM_RE.sub("", s)


def load_candidates_tsv(path: Path) -> list[dict]:
    """候補 TSV（または標本 TSV）を読み、line/offset を int 化した行の一覧を返す。"""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            row["line"] = int(row["line"])
            row["offset"] = int(row["offset"])
            rows.append(row)
    return rows


def load_blocks(content_list: Path) -> list[dict]:
    """content_list を読み、text を持つブロックを (index, norm(text), page_idx) で返す。"""
    with content_list.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"content_list is not an array: {content_list}")
    blocks: list[dict] = []
    for idx, block in enumerate(data):
        text = block.get("text")
        if text is None:
            continue
        blocks.append(
            {
                "index": idx,
                "norm_text": norm(text),
                "page_idx": block.get("page_idx"),
            }
        )
    return blocks


def find_block(
    md: str, blocks: list[dict], offset: int, symbol: str
) -> tuple[int, int, str] | None:
    """【1段階目のみ・非再帰】1件の候補について content_list のブロックを一意に特定する。
    成功時は (block_index, page_idx, key_kind) を返す。key_kind は "block_key10" / "block_key30"。
    一意に特定できなければ None を返す（複数一致・0件のいずれも None）。
    この関数はページ推定を行わず、自分自身も locate_candidate も呼ばない。"""
    end = offset + len(symbol)

    key10 = norm(md[max(0, offset - KEY_MARGIN_SHORT) : end + KEY_MARGIN_SHORT])
    matches10 = [b for b in blocks if key10 in b["norm_text"]]
    if len(matches10) == 1:
        b = matches10[0]
        return (b["index"], b["page_idx"], "block_key10")
    if len(matches10) >= 2:
        return None

    key30 = norm(md[max(0, offset - KEY_MARGIN_LONG) : end + KEY_MARGIN_LONG])
    matches30 = [b for b in blocks if key30 in b["norm_text"]]
    if len(matches30) == 1:
        b = matches30[0]
        return (b["index"], b["page_idx"], "block_key30")
    return None


def locate_candidate(
    md: str, blocks: list[dict], chapter_cands: list[dict], i: int
) -> tuple[str, int, int, str]:
    """【統括】章内候補列 chapter_cands の i 番目の候補を逆引きし、
    (stage, block_index, page_idx, reason) を返す。
    1段階目は find_block を1回呼ぶ。2段階目の近傍探索でも【find_block だけ】を呼び、
    locate_candidate を再帰的に呼ばない。特定できない値は -1 とする。"""
    cand = chapter_cands[i]
    result = find_block(md, blocks, cand["offset"], cand["symbol"])
    if result is not None:
        block_index, page_idx, key_kind = result
        return ("block", block_index, page_idx, key_kind)

    n = len(chapter_cands)
    n_fwd = n - i - 1
    n_bwd = i

    fwd_page_idx = None
    steps = 0
    j = i + 1
    while j < n and steps < MAX_NEIGHBOR_SEARCH:
        other = chapter_cands[j]
        r = find_block(md, blocks, other["offset"], other["symbol"])
        if r is not None:
            fwd_page_idx = r[1]
            break
        j += 1
        steps += 1

    bwd_page_idx = None
    steps = 0
    j = i - 1
    while j >= 0 and steps < MAX_NEIGHBOR_SEARCH:
        other = chapter_cands[j]
        r = find_block(md, blocks, other["offset"], other["symbol"])
        if r is not None:
            bwd_page_idx = r[1]
            break
        j -= 1
        steps += 1

    if fwd_page_idx is not None and bwd_page_idx is not None:
        if fwd_page_idx == bwd_page_idx:
            return ("page", -1, fwd_page_idx, "page_both")
        return ("none", -1, -1, "page_mismatch")
    if fwd_page_idx is not None and bwd_page_idx is None:
        if n_bwd == 0:
            return ("page", -1, fwd_page_idx, "page_head")
        return ("none", -1, -1, "search_exhausted")
    if fwd_page_idx is None and bwd_page_idx is not None:
        if n_fwd == 0:
            return ("page", -1, bwd_page_idx, "page_tail")
        return ("none", -1, -1, "search_exhausted")
    # fwd_page_idx is None and bwd_page_idx is None
    if n_fwd == 0 and n_bwd == 0:
        return ("none", -1, -1, "no_neighbor")
    return ("none", -1, -1, "search_exhausted")


def build_chapter_index(chapter_cands: list[dict]) -> dict[int, int]:
    """章内候補列（offset 昇順）の offset から、リスト内位置を引く索引を返す。"""
    return {cand["offset"]: pos for pos, cand in enumerate(chapter_cands)}


def write_tsv_atomic(rows: list[dict], out: Path) -> None:
    """§7.3 の TSV を出力する。同一ディレクトリの一時ファイルに書き、
    os.replace で置換する（../m1-scan-cli/design.md §5.1 と同じ手順）。"""
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
                    str(r["stage"]),
                    str(r["block_index"]),
                    str(r["page_idx"]),
                    str(r["reason"]),
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
        description="候補の原本ページ（content_list のブロック）への逆引きを行う"
    )
    parser.add_argument("--candidates", type=Path, required=True, help="候補 TSV のパス（母集団の抽出母体）")
    parser.add_argument(
        "--final-root", type=Path, required=True, help="{BASE2}/ocr/final（md と content_list の親）"
    )
    parser.add_argument(
        "--sample-size", type=int, default=None, help="指定時は母集団から無作為抽出する（検査3用）"
    )
    parser.add_argument("--seed", type=int, default=None, help="--sample-size と対で指定する乱数シード")
    parser.add_argument(
        "--input-sample", type=Path, default=None, help="既存の標本 TSV を入力にする（M3用。--sample-size と排他）"
    )
    parser.add_argument("-o", "--out", type=Path, required=True, help="出力 TSV のパス")
    parser.add_argument("--overwrite", action="store_true", help="既存ファイルの上書きを許可する")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """終了コードを返す（0 = 成功、1 = エラー）。"""
    args = parse_args(argv)
    candidates_path: Path = args.candidates
    final_root: Path = args.final_root
    sample_size: int | None = args.sample_size
    seed: int | None = args.seed
    input_sample: Path | None = args.input_sample
    out: Path = args.out
    overwrite: bool = args.overwrite

    if (sample_size is None) == (input_sample is None):
        print("specify exactly one of --sample-size or --input-sample", file=sys.stderr)
        return 1
    if sample_size is not None and seed is None:
        print("--seed is required with --sample-size", file=sys.stderr)
        return 1

    if not candidates_path.is_file():
        print(f"candidates tsv not found: {candidates_path}", file=sys.stderr)
        return 1
    try:
        all_candidates = load_candidates_tsv(candidates_path)
    except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
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

    # 章内候補列（table を含む全候補。offset 昇順）を章ごとに構築する（design.md §7.2）
    chapter_all: dict[str, list[dict]] = {}
    for row in all_candidates:
        chapter_all.setdefault(row["chapter"], []).append(row)
    for chapter in chapter_all:
        chapter_all[chapter].sort(key=lambda r: r["offset"])

    if sample_size is not None:
        population = [r for r in all_candidates if r["location"] != "table"]
        if sample_size > len(population):
            print(
                f"sample-size {sample_size} exceeds population size {len(population)}",
                file=sys.stderr,
            )
            return 1
        population_sorted = sorted(population, key=lambda r: (r["chapter"], r["offset"]))
        rng = random.Random(seed)
        working = rng.sample(population_sorted, sample_size)
        working.sort(key=lambda r: (r["chapter"], r["offset"]))
    else:
        assert input_sample is not None
        if not input_sample.is_file():
            print(f"input-sample tsv not found: {input_sample}", file=sys.stderr)
            return 1
        try:
            working = load_candidates_tsv(input_sample)
        except (OSError, UnicodeDecodeError, csv.Error, ValueError) as exc:
            print(f"input-sample tsv unreadable: {input_sample} ({exc})", file=sys.stderr)
            return 1

    md_cache: dict[str, str] = {}
    blocks_cache: dict[str, list[dict]] = {}
    index_cache: dict[str, dict[int, int]] = {}

    def get_md(chapter: str) -> str:
        if chapter not in md_cache:
            md_path = final_root / chapter / f"{chapter}_gray300.md"
            if not md_path.is_file():
                raise FileNotFoundError(f"md not found: {md_path}")
            md_cache[chapter] = md_path.read_text(encoding="utf-8")
        return md_cache[chapter]

    def get_blocks(chapter: str) -> list[dict]:
        if chapter not in blocks_cache:
            cl_path = final_root / chapter / f"{chapter}_gray300_content_list.json"
            if not cl_path.is_file():
                raise FileNotFoundError(f"content_list not found: {cl_path}")
            blocks_cache[chapter] = load_blocks(cl_path)
        return blocks_cache[chapter]

    def get_index(chapter: str) -> dict[int, int]:
        if chapter not in index_cache:
            index_cache[chapter] = build_chapter_index(chapter_all.get(chapter, []))
        return index_cache[chapter]

    results: list[dict] = []
    for row in working:
        chapter = row["chapter"]
        offset = row["offset"]
        try:
            md_text = get_md(chapter)
            blocks = get_blocks(chapter)
        except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

        chapter_cands = chapter_all.get(chapter, [])
        pos_index = get_index(chapter)
        if offset not in pos_index:
            print(
                f"candidate offset not found in chapter candidate list: {chapter} offset={offset}",
                file=sys.stderr,
            )
            return 1
        i = pos_index[offset]

        stage, block_index, page_idx, reason = locate_candidate(md_text, blocks, chapter_cands, i)
        results.append(
            {
                "chapter": row["chapter"],
                "line": row["line"],
                "offset": row["offset"],
                "kind": row["kind"],
                "location": row["location"],
                "symbol": row["symbol"],
                "context": row["context"],
                "stage": stage,
                "block_index": block_index,
                "page_idx": page_idx if page_idx is not None else -1,
                "reason": reason,
            }
        )

    try:
        write_tsv_atomic(results, out)
    except OSError as exc:
        print(f"write failed: {out} ({exc})", file=sys.stderr)
        return 1

    block_n = sum(1 for r in results if r["stage"] == "block")
    page_n = sum(1 for r in results if r["stage"] == "page")
    none_n = sum(1 for r in results if r["stage"] == "none")
    total = len(results)
    success = block_n + page_n
    rate = (success / total * 100) if total else 0.0

    page_mismatch = sum(1 for r in results if r["reason"] == "page_mismatch")
    search_exhausted = sum(1 for r in results if r["reason"] == "search_exhausted")
    no_neighbor = sum(1 for r in results if r["reason"] == "no_neighbor")

    page_both = sum(1 for r in results if r["reason"] == "page_both")
    page_head = sum(1 for r in results if r["reason"] == "page_head")
    page_tail = sum(1 for r in results if r["reason"] == "page_tail")

    def by_location(loc: str) -> tuple[int, int, int]:
        subset = [r for r in results if r["location"] == loc]
        b = sum(1 for r in subset if r["stage"] == "block")
        p = sum(1 for r in subset if r["stage"] == "page")
        n = sum(1 for r in subset if r["stage"] == "none")
        return (b, p, n)

    body_b, body_p, body_n = by_location("body")
    foot_b, foot_p, foot_n = by_location("footnote")

    print(f"located: block={block_n} page={page_n} none={none_n} total={total}", file=sys.stderr)
    print(f"success rate: {rate:.1f}%  (threshold 90%)", file=sys.stderr)
    print(
        f"none breakdown: page_mismatch={page_mismatch} search_exhausted={search_exhausted} "
        f"no_neighbor={no_neighbor}",
        file=sys.stderr,
    )
    print(
        f"page breakdown: page_both={page_both} page_head={page_head} page_tail={page_tail}",
        file=sys.stderr,
    )
    print(
        f"by location: body(block/page/none)={body_b}/{body_p}/{body_n}  "
        f"footnote={foot_b}/{foot_p}/{foot_n}",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
