"""TIF -> OCR用可逆PDF生成スクリプト。

補正済みスキャン原本の TIF 群を入力に、OCR（MinerU）への入力に適した
「300dpi グレースケール・Flate 可逆・複数ページ1ファイル」の PDF を生成する。

詳細は docs/issues/feat-002-tif-to-ocr-pdf/design.md を参照。
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
from pathlib import Path

import img2pdf
from PIL import Image

REDUCE_FACTOR: int = 2
OUT_DPI: int = 300
SUPPORTED_MODES: frozenset[str] = frozenset({"1", "L", "RGB"})


def convert_tif_to_png(tif_path: Path) -> bytes:
    """1ファイルをグレースケール・1/2縮小の PNG bytes に変換する。"""
    with Image.open(tif_path) as im:
        im.load()
        gray = im.convert("L")
        reduced = gray.reduce(REDUCE_FACTOR)
        buf = io.BytesIO()
        reduced.save(buf, format="PNG", dpi=(OUT_DPI, OUT_DPI))
        return buf.getvalue()


def validate_inputs(tifs: list[Path], output: Path, overwrite: bool) -> list[str]:
    """§4.3 の検証を行い、エラーメッセージのリストを返す（空 = 合格）。"""
    errors: list[str] = []

    if output.exists() and not overwrite:
        errors.append(f"output exists: {output} (use --overwrite)")

    for tif_path in tifs:
        if not tif_path.is_file():
            errors.append(f"not found: {tif_path}")
            continue

        try:
            with Image.open(tif_path) as im:
                mode = im.mode
                if mode not in SUPPORTED_MODES:
                    errors.append(f"unsupported image: {tif_path} (mode={mode})")
                    continue
                im.load()
        except Exception:
            errors.append(f"unreadable image: {tif_path}")

    return errors


def build_pdf(pages: list[bytes]) -> bytes:
    """PNG bytes のリストから PDF bytes を生成する。"""
    return img2pdf.convert(pages)


def write_pdf_atomic(pdf_bytes: bytes, output: Path, overwrite: bool) -> None:
    """§4.1 手順5 の原子的書き込み。

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
        tmp_file.write(pdf_bytes)
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
        description="TIF -> OCR用可逆PDF生成スクリプト"
    )
    parser.add_argument(
        "tifs",
        nargs="+",
        type=Path,
        help="入力 TIF ファイル（このページ順で PDF に格納する）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="出力 PDF パス",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="出力パスが既存でも上書きする（既定は拒否）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体制御。終了コードを返す。"""
    args = parse_args(argv)
    tifs: list[Path] = args.tifs
    output: Path = args.output
    overwrite: bool = args.overwrite

    errors = validate_inputs(tifs, output, overwrite)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    pages: list[bytes] = []
    total = len(tifs)
    for i, tif_path in enumerate(tifs, start=1):
        png_bytes = convert_tif_to_png(tif_path)
        with Image.open(io.BytesIO(png_bytes)) as im:
            width, height = im.size
        print(f"[{i}/{total}] {tif_path} -> {width}x{height}")
        pages.append(png_bytes)

    try:
        pdf_bytes = build_pdf(pages)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        write_pdf_atomic(pdf_bytes, output, overwrite)
    except FileExistsError:
        print(f"output exists: {output} (use --overwrite)", file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    size_mb = len(pdf_bytes) / (1024 * 1024)
    print(f"wrote {output} ({len(pages)} pages, {size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
