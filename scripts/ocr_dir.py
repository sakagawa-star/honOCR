"""OCR 一括実行スクリプト。

入力ディレクトリ（補正済み TIF が置かれたディレクトリ）1個以上を対象に、
「入力PDF 生成 → MinerU 変換 → 句読点正規化 → 機械確認」を一括実行する。
詳細は docs/issues/feat-006-ocr-pipeline-cli/design.md を参照。
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pypdf

SCRIPTS_DIR: Path = Path(__file__).resolve().parent

TIF_PATTERNS: tuple[str, ...] = ("page-*_1L.tif", "page-*_2R.tif")
BLANK_MAX_BYTES: int = 10240
PDF_SUFFIX: str = "_gray300.pdf"
MANIFEST_SUFFIX: str = "_gray300.pdf.manifest.json"
DEFAULT_TIMEOUT_MIN: int = 60
REPLACEMENTS: dict[str, str] = {"、": "，", "。": "．"}


@dataclasses.dataclass
class DirResult:
    """1入力ディレクトリ分の処理結果。"""

    name: str
    passed: bool
    reasons: list[str]
    pages: int
    blocks: int
    replaced_md: int
    replaced_json: int
    seconds: float
    tables: int = 0
    tables_skipped: int = 0


def derive_name(d: Path) -> str:
    """name を決定する（ベース名。"out" なら親の名前）。"""
    name = d.name
    if name == "out":
        name = d.parent.name
    return name


def list_tifs(d: Path, glob: str | None = None) -> list[Path]:
    """対象TIF を辞書順に列挙する。

    既定は TIF_PATTERNS の2パターンを結合する。glob 指定時は単一パターン
    のみを使う（上級オプション）。
    """
    patterns = (glob,) if glob else TIF_PATTERNS
    files: list[Path] = []
    for pattern in patterns:
        files.extend(d.glob(pattern))
    return sorted(files, key=lambda p: p.name)


def build_manifest(files: list[Path]) -> dict:
    """対象TIF の (絶対パス, サイズ, mtime_ns) 列から manifest 辞書を作る。"""
    entries = []
    for f in files:
        st = f.stat()
        entries.append(
            {
                "path": str(f.resolve()),
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
            }
        )
    return {"files": entries}


def manifest_matches(manifest_path: Path, files: list[Path]) -> bool:
    """既存 manifest と現在の対象TIF の完全一致を判定する。"""
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return manifest == build_manifest(files)


def blank_positions(files: list[Path], threshold: int = BLANK_MAX_BYTES) -> set[int]:
    """白紙位置（サイズ < threshold の 0始まり位置の集合）を検出する。"""
    return {i for i, f in enumerate(files) if f.stat().st_size < threshold}


def next_run_number(name_dir: Path) -> int:
    """run 番号（既存 run-NN の最大 NN + 1。なければ 1）を決定する。"""
    if not name_dir.is_dir():
        return 1
    max_n = 0
    for entry in name_dir.iterdir():
        if not entry.is_dir():
            continue
        m = re.fullmatch(r"run-(\d+)", entry.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def check_page_idx(content_list: Path, page_count: int, blanks: set[int]) -> list[str]:
    """content list の page_idx 検査。エラーメッセージのリストを返す（空 = 合格）。"""
    try:
        data = json.loads(content_list.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"content list unreadable: {content_list} ({exc})"]

    if not isinstance(data, list) or len(data) == 0:
        return [f"content list empty: {content_list}"]

    pages: set[int] = set()
    for i, block in enumerate(data):
        page_idx = block.get("page_idx") if isinstance(block, dict) else None
        if not isinstance(page_idx, int):
            return [f"block {i}: missing or non-integer page_idx"]
        pages.add(page_idx)

    full_range = set(range(page_count))
    extra = pages - full_range
    missing = full_range - pages
    non_blank_missing = missing - blanks

    errors: list[str] = []
    if extra:
        errors.append(f"page_idx out of range: {sorted(extra)}")
    if non_blank_missing:
        errors.append(f"missing non-blank pages: {sorted(non_blank_missing)}")
    return errors


def check_normalized(src: Path, dst: Path) -> list[str]:
    """正規化の機械確認（feat-004 criteria §2 と同一規則）。"""
    if not dst.is_file():
        return [f"normalized output missing: {dst}"]

    a = src.read_text(encoding="utf-8")
    b = dst.read_text(encoding="utf-8")

    if len(a) != len(b):
        return [f"length mismatch: {src} ({len(a)}) vs {dst} ({len(b)})"]

    allowed = {("、", "，"), ("。", "．")}
    bad_diff = sum(1 for x, y in zip(a, b) if x != y and (x, y) not in allowed)

    errors: list[str] = []
    if bad_diff:
        errors.append(f"disallowed diff: {bad_diff} positions in {dst}")

    residual = b.count("、") + b.count("。")
    if residual:
        errors.append(f"residual punctuation: {residual} in {dst}")

    return errors


def parse_table_summary(stdout: str) -> tuple[int, int] | None:
    """html_table_to_md.py の合計行から (converted, skipped) を読み取る。"""
    m = re.search(
        r"^total: (\d+) converted, (\d+) skipped in \d+ files$",
        stdout,
        re.MULTILINE,
    )
    if m is None:
        return None
    return int(m.group(1)), int(m.group(2))


def convert_tables(normalized_md: Path, normalized_dir: Path) -> tuple[list[str], int, int]:
    """正規化済み md の HTML 表をパイプテーブルに変換する（インプレース）。

    戻り値は (エラーメッセージのリスト, 変換件数, スキップ件数)。
    エラーリストが空 = 成功。
    """
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "html_table_to_md.py"),
        str(normalized_md),
        "-o",
        str(normalized_dir),
        "--overwrite",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        return [f"HTML表変換失敗: {proc.stderr.strip()}"], 0, 0

    summary = parse_table_summary(proc.stdout)
    if summary is None:
        return (
            [f"HTML表変換失敗: summary parse failed: {proc.stdout.strip()}"],
            0,
            0,
        )

    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)

    tables, tables_skipped = summary
    return [], tables, tables_skipped


def _fail(name: str, reasons: list[str], start: float, pages: int = 0, blocks: int = 0,
          replaced_md: int = 0, replaced_json: int = 0) -> DirResult:
    """不合格の DirResult を作る（理由を標準エラーに出力する）。"""
    for reason in reasons:
        print(reason, file=sys.stderr)
    return DirResult(
        name=name,
        passed=False,
        reasons=reasons,
        pages=pages,
        blocks=blocks,
        replaced_md=replaced_md,
        replaced_json=replaced_json,
        seconds=time.monotonic() - start,
    )


def process_dir(d: Path, root: Path, args: argparse.Namespace) -> DirResult:
    """1入力ディレクトリ分のパイプラインを実行する（design.md §4.1）。"""
    start = time.monotonic()
    name = args.name if args.name is not None else derive_name(d)

    print(f"[{name}] 開始: {d}")

    if not d.is_dir():
        return _fail(name, [f"入力ディレクトリが存在しません: {d}"], start)

    tifs = list_tifs(d, args.glob)
    if not tifs:
        return _fail(name, [f"対象TIFが見つかりません: {d}"], start)

    blanks = blank_positions(tifs)

    pdf_dir = root / "pdf"
    pdf_path = pdf_dir / f"{name}{PDF_SUFFIX}"
    manifest_path = pdf_dir / f"{name}{MANIFEST_SUFFIX}"

    if args.overwrite_pdf:
        print(f"[{name}] 入力PDF生成中(overwrite): {pdf_path}")
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "make_ocr_pdf.py"),
            *[str(t) for t in tifs],
            "-o",
            str(pdf_path),
            "--overwrite",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return _fail(name, [f"入力PDF生成失敗: {proc.stderr.strip()}"], start)
        manifest_path.write_text(
            json.dumps(build_manifest(tifs), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif not pdf_path.exists():
        print(f"[{name}] 入力PDF生成中: {pdf_path}")
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "make_ocr_pdf.py"),
            *[str(t) for t in tifs],
            "-o",
            str(pdf_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return _fail(name, [f"入力PDF生成失敗: {proc.stderr.strip()}"], start)
        manifest_path.write_text(
            json.dumps(build_manifest(tifs), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        if not manifest_matches(manifest_path, tifs):
            return _fail(
                name,
                [
                    f"入力PDFの manifest が対象TIFと一致しません: {manifest_path} "
                    f"(--overwrite-pdf で作り直してください)"
                ],
                start,
            )
        print(f"[{name}] 既存の入力PDFを再利用: {pdf_path}")

    try:
        page_count = len(pypdf.PdfReader(str(pdf_path)).pages)
    except Exception as exc:  # noqa: BLE001
        return _fail(name, [f"PDF読み込み失敗: {exc}"], start)

    if page_count != len(tifs):
        return _fail(
            name,
            [f"PDFページ数不一致: pdf={page_count} tif={len(tifs)}"],
            start,
        )

    name_dir = root / "mineru-full" / name
    run_n = next_run_number(name_dir)
    run_dir = name_dir / f"run-{run_n:02d}"
    log_path = name_dir / f"run-{run_n:02d}.log"

    name_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{name}] mineru run-{run_n:02d} 開始 ({page_count} pages)...")
    env = os.environ.copy()
    existing_no_proxy = env.get("no_proxy", "")
    env["no_proxy"] = "localhost,127.0.0.1" + (
        "," + existing_no_proxy if existing_no_proxy else ""
    )
    existing_NO_PROXY = env.get("NO_PROXY", "")
    env["NO_PROXY"] = "localhost,127.0.0.1" + (
        "," + existing_NO_PROXY if existing_NO_PROXY else ""
    )

    cmd = ["mineru", "-p", str(pdf_path), "-o", str(run_dir)]
    timeout_seconds = args.timeout * 60
    try:
        with open(log_path, "w", encoding="utf-8") as log_file:
            proc = subprocess.run(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired:
        return _fail(
            name,
            [f"MinerU タイムアウト（{args.timeout}分）: {log_path}"],
            start,
            pages=page_count,
        )

    if proc.returncode != 0:
        return _fail(
            name,
            [f"MinerU 非0終了（code={proc.returncode}）: {log_path}"],
            start,
            pages=page_count,
        )

    stem = pdf_path.stem
    hybrid_dir = run_dir / stem / "hybrid_auto"
    md_path = hybrid_dir / f"{stem}.md"
    content_list_path = hybrid_dir / f"{stem}_content_list.json"

    if not hybrid_dir.is_dir():
        return _fail(
            name,
            [f"hybrid_auto ディレクトリが見つかりません: {hybrid_dir}"],
            start,
            pages=page_count,
        )

    print(f"[{name}] 正規化中...")
    normalized_dir = name_dir / f"run-{run_n:02d}-normalized"
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "normalize_punct.py"),
        str(md_path),
        str(content_list_path),
        "-o",
        str(normalized_dir),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return _fail(
            name,
            [f"正規化失敗: {proc.stderr.strip()}"],
            start,
            pages=page_count,
        )

    normalized_md = normalized_dir / md_path.name
    normalized_content_list = normalized_dir / content_list_path.name

    machine_errors: list[str] = []

    if not md_path.is_file() or md_path.stat().st_size == 0:
        machine_errors.append(f"md が存在しないか空です: {md_path}")

    blocks = 0
    if content_list_path.is_file():
        machine_errors.extend(check_page_idx(content_list_path, page_count, blanks))
        try:
            blocks = len(json.loads(content_list_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            blocks = 0
    else:
        machine_errors.append(f"content list が存在しません: {content_list_path}")

    machine_errors.extend(check_normalized(md_path, normalized_md))
    machine_errors.extend(check_normalized(content_list_path, normalized_content_list))

    replaced_md = 0
    replaced_json = 0
    if md_path.is_file():
        md_text = md_path.read_text(encoding="utf-8")
        replaced_md = sum(md_text.count(c) for c in REPLACEMENTS)
    if content_list_path.is_file():
        content_text = content_list_path.read_text(encoding="utf-8")
        replaced_json = sum(content_text.count(c) for c in REPLACEMENTS)

    if machine_errors:
        return _fail(
            name,
            machine_errors,
            start,
            pages=page_count,
            blocks=blocks,
            replaced_md=replaced_md,
            replaced_json=replaced_json,
        )

    print(f"[{name}] HTML表変換中...")
    table_errors, tables, tables_skipped = convert_tables(normalized_md, normalized_dir)
    if table_errors:
        return _fail(
            name,
            table_errors,
            start,
            pages=page_count,
            blocks=blocks,
            replaced_md=replaced_md,
            replaced_json=replaced_json,
        )

    elapsed = time.monotonic() - start
    print(f"[{name}] 完了: PASS ({elapsed:.1f}秒)")
    return DirResult(
        name=name,
        passed=True,
        reasons=[],
        pages=page_count,
        blocks=blocks,
        replaced_md=replaced_md,
        replaced_json=replaced_json,
        tables=tables,
        tables_skipped=tables_skipped,
        seconds=elapsed,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数の解析。"""
    parser = argparse.ArgumentParser(
        description="OCR 一括実行スクリプト（入力PDF生成→MinerU→正規化→機械確認）"
    )
    parser.add_argument(
        "dirs",
        nargs="+",
        type=Path,
        help="入力ディレクトリ（補正済み TIF が置かれたディレクトリ）",
    )
    parser.add_argument(
        "-o",
        "--root",
        type=Path,
        required=True,
        help="出力先ルート（pdf/・mineru-full/ を配下に作る）",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="name の明示指定（入力ディレクトリが1個のときのみ有効）",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default=None,
        help="対象TIF を単一パターンに変更する（既定は TIF_PATTERNS の2パターン結合）",
    )
    parser.add_argument(
        "--overwrite-pdf",
        action="store_true",
        help="既存の入力PDF を作り直す（既定は検証の上で再利用）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_MIN,
        help=f"MinerU のタイムアウト（分。既定 {DEFAULT_TIMEOUT_MIN}）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体制御。終了コードを返す。"""
    args = parse_args(argv)
    dirs: list[Path] = args.dirs
    root: Path = args.root

    if args.name is not None and len(dirs) > 1:
        print(
            "--name はディレクトリを1個指定したときのみ使用できます",
            file=sys.stderr,
        )
        return 2

    names = [args.name if args.name is not None else derive_name(d) for d in dirs]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        print(f"name が重複しています: {', '.join(duplicates)}", file=sys.stderr)
        return 2

    root.mkdir(parents=True, exist_ok=True)

    results = [process_dir(d, root, args) for d in dirs]

    for r in results:
        if r.passed:
            minutes, seconds = divmod(int(r.seconds), 60)
            print(
                f"{r.name}: PASS pages={r.pages} blocks={r.blocks} "
                f"replaced={r.replaced_md}+{r.replaced_json} "
                f"tables={r.tables}+{r.tables_skipped}skipped "
                f"({minutes}分{seconds}秒)"
            )
        else:
            print(f"{r.name}: FAIL {'; '.join(r.reasons)}")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
