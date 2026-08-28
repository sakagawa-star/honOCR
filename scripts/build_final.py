"""final ディレクトリ構築スクリプト。

正規化済みディレクトリ（run-NN-normalized。md・content_list.json・images/ を含む）
から最終成果物 final ディレクトリ（{root}/final/{name}/）を組み立て、検証する。
詳細は docs/issues/feat-012-build-final/design.md を参照。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

CONTENT_LIST_SUFFIX: str = "_content_list.json"
IMAGES_DIRNAME: str = "images"
IMAGE_REF_RE: re.Pattern[str] = re.compile(r"images/[^\s)\"'<>]+")


def find_pair(normalized_dir: Path) -> tuple[str, Path, Path]:
    """(ベース名, md パス, content_list パス) を返す。

    決定不能な場合は ValueError を送出する。
    """
    if not normalized_dir.is_dir():
        raise ValueError(f"not a directory: {normalized_dir}")

    content_lists = sorted(normalized_dir.glob(f"*{CONTENT_LIST_SUFFIX}"))
    if len(content_lists) == 0:
        raise ValueError(f"content list not found in {normalized_dir}")
    if len(content_lists) >= 2:
        raise ValueError(
            f"multiple content lists in {normalized_dir}: {len(content_lists)}"
        )

    content_list = content_lists[0]
    base = content_list.name[: -len(CONTENT_LIST_SUFFIX)]
    md = normalized_dir / f"{base}.md"
    if not md.is_file():
        raise ValueError(f"md not found: {md}")

    return base, md, content_list


def validate_inputs(
    normalized_dir: Path,
    md: Path,
    content_list: Path,
    outdir: Path,
    overwrite: bool,
) -> list[str]:
    """検証を行い、エラーメッセージのリストを返す（空 = 合格）。

    normalized_dir は検証6（重なり検査）と検証7（images の種別）に用いる。
    """
    errors: list[str] = []

    # 検証1・2: 空ファイル
    if md.stat().st_size == 0:
        errors.append(f"empty file: {md}")
    if content_list.stat().st_size == 0:
        errors.append(f"empty file: {content_list}")

    # 検証3・4: content_list が UTF-8 の JSON 配列として読めるか
    try:
        text = content_list.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"content list unreadable: {content_list} ({exc})")
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"content list unreadable: {content_list} ({exc})")
        else:
            if not isinstance(data, list):
                errors.append(f"content list is not an array: {content_list}")

    # 検証5: overwrite なしでの出力先既存チェック（md・content_list・images 直下）
    if not overwrite:
        existing: list[Path] = []
        md_out = outdir / md.name
        cl_out = outdir / content_list.name
        if md_out.exists():
            existing.append(md_out)
        if cl_out.exists():
            existing.append(cl_out)
        images_out = outdir / IMAGES_DIRNAME
        if images_out.is_dir():
            for entry in sorted(images_out.iterdir()):
                if entry.is_file():
                    existing.append(entry)
        for path in existing:
            errors.append(f"output exists: {path} (use --overwrite)")

    # 検証6: 出力先と入力ディレクトリの重なり検査
    nd = normalized_dir.resolve()
    od = outdir.resolve()
    overlap = (od == nd) or (nd in od.parents) or (od in nd.parents)
    if overlap:
        errors.append(f"outdir overlaps normalized_dir: {outdir}")

    # 検証7: normalized_dir/images がディレクトリでない
    images_src = normalized_dir / IMAGES_DIRNAME
    if images_src.exists() and not images_src.is_dir():
        errors.append(f"images is not a directory: {images_src}")

    # 検証8: outdir/images がディレクトリでない
    images_out = outdir / IMAGES_DIRNAME
    if images_out.exists() and not images_out.is_dir():
        errors.append(f"output images is not a directory: {images_out}")

    # 検証9: outdir がシンボリックリンク
    if outdir.exists() and outdir.is_symlink():
        errors.append(f"outdir must not be a symlink: {outdir}")

    # 検証10: outdir/images がシンボリックリンク
    if images_out.exists() and images_out.is_symlink():
        errors.append(f"output images must not be a symlink: {images_out}")

    return errors


def copy_atomic(src: Path, dst: Path) -> None:
    """バイト同一のコピーを原子的に行う。

    同一ディレクトリの一時ファイルへ書き、fsync 後に os.replace で確定する
    （feat-002 write_pdf_atomic・feat-004 write_text_atomic と同じ方式。
    ただしテキストではなくバイト列を扱うため shutil.copyfileobj を用いる）。
    失敗時は一時ファイルを削除して例外を送出する。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    tmp_file = tempfile.NamedTemporaryFile(dir=dst.parent, suffix=".tmp", delete=False)
    tmp_path = Path(tmp_file.name)
    try:
        with open(src, "rb") as src_f:
            shutil.copyfileobj(src_f, tmp_file)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_file.close()

        os.replace(tmp_path, dst)
    except BaseException:
        tmp_file.close()
        if tmp_path.exists():
            os.unlink(tmp_path)
        raise


def verify(
    md_src: Path, cl_src: Path, outdir: Path, base: str, src_names: set[str]
) -> list[str]:
    """FR-003 の3項目を検証し、エラーメッセージのリストを返す（空 = 合格）。"""
    errors: list[str] = []

    md_out = outdir / md_src.name
    cl_out = outdir / cl_src.name

    # 検証1: バイト同一
    if md_src.read_bytes() != md_out.read_bytes():
        errors.append(f"byte mismatch: {md_out}")
    if cl_src.read_bytes() != cl_out.read_bytes():
        errors.append(f"byte mismatch: {cl_out}")

    images_out = outdir / IMAGES_DIRNAME
    actual_names: set[str] = set()
    if images_out.is_dir():
        actual_names = {f.name for f in images_out.iterdir() if f.is_file()}

    # 検証2: md の画像参照の解決
    md_text = md_out.read_text(encoding="utf-8")
    refs = {Path(m).name for m in IMAGE_REF_RE.findall(md_text)}
    missing = refs - actual_names
    if missing:
        shown = sorted(missing)[:5]
        suffix = " ..." if len(missing) > 5 else ""
        errors.append(f"missing images referenced by md: {shown}{suffix}")

    # 検証3: img_path 集合の一致
    cl_data = json.loads(cl_out.read_text(encoding="utf-8"))
    expected: set[str] = set()
    if isinstance(cl_data, list):
        for block in cl_data:
            if not isinstance(block, dict):
                continue
            img_path = block.get("img_path")
            if isinstance(img_path, str):
                expected.add(Path(img_path).name)

    if expected != actual_names:
        images_missing = sorted(expected - actual_names)
        images_extra = sorted(actual_names - expected)
        if images_missing:
            errors.append(
                f"images missing (in content_list, not in images/): {images_missing}"
            )
        if images_extra:
            errors.append(
                f"images extra (in images/, not in content_list): {images_extra}"
            )

    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="final ディレクトリ構築スクリプト（正規化済み出力を final へ集約し検証する）"
    )
    parser.add_argument(
        "normalized_dir",
        type=Path,
        help="正規化済みディレクトリ（run-NN-normalized。md・content_list・images/ を含む）",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        required=True,
        help="final の出力先ディレクトリ（例: {root}/final/chapNN）",
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
    normalized_dir: Path = args.normalized_dir
    outdir: Path = args.outdir
    overwrite: bool = args.overwrite

    try:
        base, md_src, cl_src = find_pair(normalized_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors = validate_inputs(normalized_dir, md_src, cl_src, outdir, overwrite)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    images_src = normalized_dir / IMAGES_DIRNAME
    src_names: set[str] = set()
    if images_src.is_dir():
        src_names = {f.name for f in images_src.iterdir() if f.is_file()}

    images_out = outdir / IMAGES_DIRNAME

    try:
        outdir.mkdir(parents=True, exist_ok=True)
        images_out.mkdir(parents=True, exist_ok=True)

        copy_atomic(md_src, outdir / md_src.name)
        copy_atomic(cl_src, outdir / cl_src.name)

        for name in sorted(src_names):
            copy_atomic(images_src / name, images_out / name)

        # 孤児削除（FR-006 基準3）
        for entry in sorted(images_out.iterdir()):
            if entry.name in src_names:
                continue
            if entry.is_dir():
                print(f"unexpected directory in images: {entry}", file=sys.stderr)
                return 1
            entry.unlink()

        verify_errors = verify(md_src, cl_src, outdir, base, src_names)
        if verify_errors:
            for error in verify_errors:
                print(error, file=sys.stderr)
            return 1
    except OSError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1

    print(f"{base}: md=1 content_list=1 images={len(src_names)}")
    print("total: 1 built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
