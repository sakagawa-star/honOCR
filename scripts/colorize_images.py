"""図画像のカラー再切出スクリプト。

MinerU の content_list に記録された図ブロック（img_path キーを持つ要素）の
bbox・page_idx を使い、原本 TIF（600dpi カラー）から同じ領域をカラーで
切り出して保存する。詳細は
docs/issues/feat-007-colorize-images/design.md を参照。
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
JPEG_QUALITY: int = 95
DEFAULT_SCALE: float = 1 / 3


def load_image_blocks(content_list: Path) -> list[dict]:
    """content_list を読み込み、img_path キーを持つ図ブロックを抽出する。"""
    data = json.loads(content_list.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"content list is not an array: {content_list}")
    return [block for block in data if isinstance(block, dict) and "img_path" in block]


def list_tifs(d: Path) -> list[Path]:
    """TIF 列（TIF_PATTERNS）を辞書順に列挙する。"""
    files: list[Path] = []
    for pattern in TIF_PATTERNS:
        files.extend(d.glob(pattern))
    return sorted(files, key=lambda p: p.name)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(
    blocks: list[dict], tifs: list[Path], outdir: Path, overwrite: bool, scale: float
) -> list[str]:
    """§4.2 の検証を行い、エラーメッセージのリストを返す（空 = 合格）。"""
    errors: list[str] = []
    n_tifs = len(tifs)

    if not isinstance(scale, (int, float)) or isinstance(scale, bool) or math.isnan(scale) or math.isinf(scale) or scale <= 0:
        errors.append(f"--scale invalid: {scale!r}")

    for i, block in enumerate(blocks):
        page_idx = block.get("page_idx")
        if not isinstance(page_idx, int) or isinstance(page_idx, bool):
            errors.append(f"block {i}: page_idx invalid: {page_idx!r}")
        elif not (0 <= page_idx < n_tifs):
            errors.append(
                f"block {i}: page_idx out of range: {page_idx} (tifs={n_tifs})"
            )

        bbox = block.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            errors.append(f"block {i}: bbox invalid: {bbox!r}")
            continue
        if not all(_is_number(v) for v in bbox):
            errors.append(f"block {i}: bbox not numeric: {bbox!r}")
            continue

        x0, y0, x1, y1 = bbox
        if x0 >= x1 or y0 >= y1:
            errors.append(f"block {i}: bbox order invalid: {bbox!r}")
        if not all(0 <= v <= BBOX_SCALE for v in bbox):
            errors.append(f"block {i}: bbox out of range [0,{BBOX_SCALE}]: {bbox!r}")

    if not overwrite:
        seen: set[str] = set()
        for block in blocks:
            img_path = block.get("img_path")
            if not img_path:
                continue
            name = Path(img_path).name
            if name in seen:
                continue
            seen.add(name)
            out_path = outdir / name
            if out_path.exists():
                errors.append(f"output exists: {out_path} (use --overwrite)")

    return errors


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


def colorize(
    blocks: list[dict], tifs: list[Path], outdir: Path, scale: float = DEFAULT_SCALE
) -> int:
    """図ブロックを切り出して保存する。生成ファイル数を返す。"""
    outdir.mkdir(parents=True, exist_ok=True)

    tif_cache: dict[int, Image.Image] = {}
    seen: set[str] = set()
    count = 0

    for block in blocks:
        name = Path(block["img_path"]).name
        if name in seen:
            continue
        seen.add(name)

        page_idx = block["page_idx"]
        if page_idx not in tif_cache:
            tif_cache[page_idx] = Image.open(tifs[page_idx])
        tif = tif_cache[page_idx]

        px = bbox_to_pixels(block["bbox"], tif.size)
        cropped = tif.crop(px)
        if scale != 1.0:
            w, h = cropped.size
            new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
            cropped = cropped.resize(new_size, Image.LANCZOS)
        cropped = cropped.convert("RGB")
        cropped.save(outdir / name, format="JPEG", quality=JPEG_QUALITY)
        count += 1

    return count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="図画像のカラー再切出スクリプト（content_list の bbox で原本 TIF から切り出す）"
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
        "--overwrite",
        action="store_true",
        help="出力先の同名ファイルが既存でも上書きする（既定は拒否）",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_SCALE,
        help=f"出力の縮小率（既定 {DEFAULT_SCALE}）。1.0 で原寸。0以下は不可",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体制御。終了コードを返す。"""
    args = parse_args(argv)
    content_list: Path = args.content_list
    tif_dir: Path = args.tif_dir
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite
    scale: float = args.scale

    if not content_list.is_file():
        print(f"content list not found: {content_list}", file=sys.stderr)
        return 1

    try:
        blocks = load_image_blocks(content_list)
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

    errors = validate(blocks, tifs, outdir, overwrite, scale)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    try:
        count = colorize(blocks, tifs, outdir, scale)
    except OSError as exc:
        print(f"crop/save failed: {exc}", file=sys.stderr)
        return 1

    print(f"blocks={len(blocks)} unique={count} outdir={outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
