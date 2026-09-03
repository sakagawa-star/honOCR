"""content_list の座標による原本 TIF の領域切り出しスクリプト。

MinerU の content_list に記録された任意のブロック（テキスト・数式・コードなど、
`type` を問わない）を `--index` で指定し、その `bbox`・`page_idx` を使って
原本 TIF から同じ領域をグレースケール PNG として切り出す。詳細は
docs/issues/feat-021-qa-heading-source-collation/design.md §5 を参照。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image

TIF_PATTERNS: tuple[str, ...] = ("page-*_1L.tif", "page-*_2R.tif")
BBOX_SCALE: int = 1000
DEFAULT_MARGIN: float = 8.0
DEFAULT_MAX_WIDTH: int = 1500


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_blocks(content_list: Path) -> list[dict]:
    """content_list を読み込み、全ブロックの配列を返す。"""
    data = json.loads(content_list.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"content list is not an array: {content_list}")
    return data


def list_tifs(d: Path) -> list[Path]:
    """TIF 列（TIF_PATTERNS）を辞書順に列挙する。"""
    files: list[Path] = []
    for pattern in TIF_PATTERNS:
        files.extend(d.glob(pattern))
    return sorted(files, key=lambda p: p.name)


def bbox_to_pixels(
    bbox: list[float], size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """0-1000 正規化 bbox をピクセル座標（round＋クランプ）に変換する。"""
    w, h = size
    x0, y0, x1, y1 = bbox

    px0 = round(x0 / BBOX_SCALE * w)
    py0 = round(y0 / BBOX_SCALE * h)
    px1 = round(x1 / BBOX_SCALE * w)
    py1 = round(y1 / BBOX_SCALE * h)

    px0 = max(0, min(px0, w))
    py0 = max(0, min(py0, h))
    px1 = max(0, min(px1, w))
    py1 = max(0, min(py1, h))

    return px0, py0, px1, py1


def _bump_to_min_one(lo: int, hi: int, limit: int) -> tuple[int, int]:
    """幅または高さが 0 になる場合、1 ピクセルに切り上げる。"""
    if hi > lo:
        return lo, hi
    if hi < limit:
        return lo, hi + 1
    return max(0, lo - 1), hi


def validate(
    blocks: list[dict],
    tifs: list[Path],
    indices: list[int],
    outdir: Path,
    overwrite: bool,
    margin: float,
    max_width: int,
    stem: str,
) -> list[str]:
    """§5.3 の検証フェーズを実行し、エラーメッセージのリストを返す（空 = 合格）。"""
    errors: list[str] = []
    n_blocks = len(blocks)
    n_tifs = len(tifs)

    # 4-0: --index の重複
    seen: set[int] = set()
    duplicated: set[int] = set()
    for idx in indices:
        if idx in seen:
            duplicated.add(idx)
        seen.add(idx)
    for idx in sorted(duplicated):
        errors.append(f"--index specified more than once: {idx}")

    # 4-5: --margin / --max-width
    if not _is_number(margin) or not math.isfinite(margin) or margin < 0:
        errors.append(f"--margin invalid: {margin!r}")
    if not isinstance(max_width, int) or isinstance(max_width, bool) or max_width < 1:
        errors.append(f"--max-width invalid: {max_width!r}")

    for idx in indices:
        # 4-1
        if not (0 <= idx < n_blocks):
            errors.append(f"--index out of range: {idx} (blocks={n_blocks})")
            continue

        block = blocks[idx]

        # 4-2, 4-3: bbox
        bbox = block.get("bbox") if isinstance(block, dict) else None
        if not isinstance(bbox, list) or len(bbox) != 4:
            errors.append(f"block {idx}: bbox invalid: {bbox!r}")
        elif not all(_is_number(v) and math.isfinite(v) for v in bbox):
            errors.append(f"block {idx}: bbox not finite numeric: {bbox!r}")
        else:
            x0, y0, x1, y1 = bbox
            if not all(0 <= v <= BBOX_SCALE for v in bbox):
                errors.append(f"block {idx}: bbox out of range [0,{BBOX_SCALE}]: {bbox!r}")
            if x0 > x1 or y0 > y1:
                errors.append(f"block {idx}: bbox order invalid: {bbox!r}")

        # 4-4: page_idx
        page_idx = block.get("page_idx") if isinstance(block, dict) else None
        page_idx_is_int = isinstance(page_idx, int) and not isinstance(page_idx, bool)
        page_idx_ok = page_idx_is_int and 0 <= page_idx < n_tifs
        if not page_idx_is_int:
            errors.append(f"block {idx}: page_idx invalid: {page_idx!r}")
        elif not page_idx_ok:
            errors.append(f"block {idx}: page_idx out of range: {page_idx} (tifs={n_tifs})")

        # 4-6: 出力先の既存チェック（page_idx が有効なときのみファイル名を確定できる）
        if page_idx_ok and not overwrite:
            out_path = outdir / f"{stem}_b{idx}_p{page_idx}.png"
            if out_path.exists():
                errors.append(f"output exists: {out_path} (use --overwrite)")

    return errors


def crop_blocks(
    blocks: list[dict],
    tifs: list[Path],
    indices: list[int],
    outdir: Path,
    stem: str,
    margin: float,
    max_width: int,
) -> int:
    """検証済みの --index を指定順に切り出して保存する。生成枚数を返す。"""
    outdir.mkdir(parents=True, exist_ok=True)

    tif_cache: dict[int, Image.Image] = {}
    count = 0

    for idx in indices:
        block = blocks[idx]
        page_idx = block["page_idx"]
        if page_idx not in tif_cache:
            tif_cache[page_idx] = Image.open(tifs[page_idx])
        tif = tif_cache[page_idx]

        x0, y0, x1, y1 = block["bbox"]
        margined = [x0 - margin, y0 - margin, x1 + margin, y1 + margin]
        px0, py0, px1, py1 = bbox_to_pixels(margined, tif.size)

        px0, px1 = _bump_to_min_one(px0, px1, tif.size[0])
        py0, py1 = _bump_to_min_one(py0, py1, tif.size[1])

        cropped = tif.crop((px0, py0, px1, py1))

        width, height = cropped.size
        if width > max_width:
            new_height = max(1, round(height * max_width / width))
            cropped = cropped.resize((max_width, new_height), Image.LANCZOS)

        cropped = cropped.convert("L")
        out_path = outdir / f"{stem}_b{idx}_p{page_idx}.png"
        cropped.save(out_path, format="PNG")
        count += 1

    return count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description=(
            "content_list の bbox で原本 TIF の領域を切り出す CLI"
            "（グレースケール PNG 出力）"
        )
    )
    parser.add_argument(
        "content_list",
        type=Path,
        help="content_list の JSON パス",
    )
    parser.add_argument(
        "tif_dir",
        type=Path,
        help="原本 TIF のディレクトリ",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        required=True,
        help="出力ディレクトリ（存在しなければ作成）",
    )
    parser.add_argument(
        "--index",
        type=int,
        action="append",
        required=True,
        help="切り出すブロック番号（0始まり。複数指定可。重複はエラー）",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=DEFAULT_MARGIN,
        help=f"bbox の四方に加える余白（0-1000正規化単位。既定 {DEFAULT_MARGIN}）",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help=f"出力画像の最大幅（ピクセル。既定 {DEFAULT_MAX_WIDTH}）",
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
    content_list: Path = args.content_list
    tif_dir: Path = args.tif_dir
    outdir: Path = args.outdir
    indices: list[int] = args.index
    margin: float = args.margin
    max_width: int = args.max_width
    overwrite: bool = args.overwrite

    if not content_list.is_file():
        print(f"content list not found: {content_list}", file=sys.stderr)
        return 1

    try:
        blocks = load_blocks(content_list)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"content list unreadable: {content_list} ({exc})", file=sys.stderr)
        return 1

    if not tif_dir.is_dir():
        print(f"tif dir not found: {tif_dir}", file=sys.stderr)
        return 1

    tifs = list_tifs(tif_dir)
    if not tifs:
        print(f"no tifs found: {tif_dir}", file=sys.stderr)
        return 1

    stem = content_list.stem

    errors = validate(blocks, tifs, indices, outdir, overwrite, margin, max_width, stem)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    try:
        count = crop_blocks(blocks, tifs, indices, outdir, stem, margin, max_width)
    except OSError as exc:
        print(f"crop/save failed: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {count} file(s) to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
