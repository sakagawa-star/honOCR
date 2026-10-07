"""候補レコードから content_list を逆引きし、原本ページ（`page_idx`）を特定して
判定結果レコードを出力する CLI。

逆引きの規則（照合キー・`K` の階梯・検索対象テキスト）と判定結果レコードの形式は
`docs/issues/feat-025-inline-math-markup-survey/m2-1-locate-smoke/design.md` が正。
本ファイルはその実装。原本 TIF からの切り出しは既存の `scripts/crop_blocks.py` を
使う（本ファイルはそれを呼び出さない。実行手順は design.md §1.9.2 を参照）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# --- 検索対象テキストのキー（design.md §1.4.3） ---------------------------

SEARCH_KEYS: tuple[str, ...] = (
    "text",
    "table_body",
    "image_caption",
    "image_footnote",
    "table_caption",
    "table_footnote",
    "chart_caption",
    "chart_footnote",
)

# --- 照合キーの `K` の階梯（design.md §1.4.2） -----------------------------

KEY_LENGTHS: list[int] = [40, 20, 10, 5]

# --- 判定の値の集合（design.md §1.4.4） ------------------------------------

JUDGMENTS: tuple[str, ...] = ("missing", "not_missing", "undecidable")

# --- 候補レコード・判定結果レコードのキー（design.md §1.4.4・§1.4.8） -----

RECORD_KEYS: tuple[str, ...] = ("chapter", "offset", "char", "before", "after")
RESULT_KEYS: tuple[str, ...] = (
    "chapter",
    "offset",
    "char",
    "before",
    "after",
    "page_idx",
    "judgment",
)


def resolve_content_list(final_dir: Path, chapter: str) -> Path:
    """章名から content_list のパスを一意に解決する（design.md §1.4.1）。
    `final_dir / chapter` を `*_content_list.json` で glob し、ちょうど 1 個で
    あることを要求する。0 個・2 個以上・章のディレクトリが存在しない場合は
    例外を送出する。"""
    chapter_dir = final_dir / chapter
    if not chapter_dir.is_dir():
        raise FileNotFoundError(f"章のディレクトリが存在しない: {chapter_dir}")

    matches = sorted(chapter_dir.glob("*_content_list.json"))
    if len(matches) == 0:
        raise FileNotFoundError(f"content_list が見つからない: {chapter_dir}")
    if len(matches) >= 2:
        raise ValueError(f"content_list が複数ある: {chapter_dir}")
    return matches[0]


def block_search_text(block: dict[str, object]) -> str:
    """content_list のブロック 1 個から検索対象テキストを組み立てる
    （design.md §1.4.3）。`SEARCH_KEYS` の順に見て、`str` はそのまま、`list`
    は要素のうち `str` であるものを順に取り出し、`\\n` で連結する。"""
    parts: list[str] = []
    for key in SEARCH_KEYS:
        if key not in block:
            continue
        value = block[key]
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(v for v in value if isinstance(v, str))
    return "\n".join(parts)


def build_key(record: dict[str, object], k: int) -> str:
    """照合キーを作る（design.md §1.4.2、ADR-17）。
    まず文脈を改行で切り詰める（`before` は最後の改行より後、`after` は最初の
    改行より前だけを使う。改行が無ければ全体を使う）。そのうえで
    `key(K) = b[-K:] + record["char"] + a[:K]` を返す。切り詰めは照合キーの
    生成にだけ効き、`record` の `before` / `after` は変更しない。"""
    before = record["before"]
    char = record["char"]
    after = record["after"]
    b = before.rsplit("\n", 1)[-1]
    a = after.split("\n", 1)[0]
    return b[-k:] + char + a[:k]


def locate_block(
    record: dict[str, object], blocks: list[dict[str, object]]
) -> tuple[int | None, int | None, int | None]:
    """`KEY_LENGTHS` の階梯で content_list のブロックを特定する
    （design.md §1.4.2）。`(block_idx, page_idx, k)` を返す。逆引き失敗の
    ときは `(None, None, None)` を返す。"""
    search_texts = [block_search_text(block) for block in blocks]

    for k in KEY_LENGTHS:
        key = build_key(record, k)
        matches = [i for i, text in enumerate(search_texts) if key in text]

        if len(matches) == 0:
            continue
        if len(matches) >= 2:
            return (None, None, None)

        block_idx = matches[0]
        page_idx = blocks[block_idx].get("page_idx")
        if not isinstance(page_idx, int) or isinstance(page_idx, bool):
            return (None, None, None)
        return (block_idx, page_idx, k)

    return (None, None, None)


def make_result(
    record: dict[str, object], page_idx: int | None, judgment: str | None
) -> dict[str, object]:
    """判定結果レコードを作る（design.md §1.4.4）。キーは 7 個に限る
    （ブロック番号・採用した `K` は含めない）。"""
    return {
        "chapter": record["chapter"],
        "offset": record["offset"],
        "char": record["char"],
        "before": record["before"],
        "after": record["after"],
        "page_idx": page_idx,
        "judgment": judgment,
    }


def _validate_record_fields(value: dict[str, object], path: Path, lineno: int) -> None:
    """候補レコードの型・値域を検証する（design.md §1.4.8 の表）。
    合わなければ例外を送出する。"""
    chapter = value.get("chapter")
    if not isinstance(chapter, str) or chapter == "":
        raise ValueError(f"候補レコードの値が不正: {path}:{lineno}（chapter）")

    offset = value.get("offset")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError(f"候補レコードの値が不正: {path}:{lineno}（offset）")

    char = value.get("char")
    if not isinstance(char, str) or len(char) != 1:
        raise ValueError(f"候補レコードの値が不正: {path}:{lineno}（char）")

    before = value.get("before")
    if not isinstance(before, str):
        raise ValueError(f"候補レコードの値が不正: {path}:{lineno}（before）")

    after = value.get("after")
    if not isinstance(after, str):
        raise ValueError(f"候補レコードの値が不正: {path}:{lineno}（after）")


def read_candidates(path: Path) -> list[tuple[int, dict[str, object]]]:
    """候補レコード JSONL を読み込み、検証する（design.md §1.4.8）。
    （物理行番号, レコード）の対を入力ファイルの並び順のまま返す。物理行番号
    は 1 始まりで、空行も 1 行として数える（候補としては飛ばす）。検証エラー
    では例外を送出する（最初に見つかったエラーで打ち切る）。"""
    if not path.is_file():
        raise FileNotFoundError(f"候補ファイルが存在しない: {path}")

    results: list[tuple[int, dict[str, object]]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            if line == "":
                continue

            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"JSON として読めない行がある: {path}:{lineno}")

            if not isinstance(value, dict):
                raise ValueError(f"候補レコードがオブジェクトでない: {path}:{lineno}")

            keys = list(value.keys())
            if set(keys) != set(RECORD_KEYS):
                raise ValueError(
                    f"候補レコードのキーが不正: {path}:{lineno}（{keys}）"
                )

            _validate_record_fields(value, path, lineno)
            results.append((lineno, value))

    return results


def _check_output_writable(out: Path, overwrite: bool) -> None:
    """出力先の保護判定（design.md §1.4.4「ファイル形式と出力先の保護」）。
    問題があれば書き込まずに例外を送出する。判定順序を厳守する。"""
    if out.exists() and not overwrite:
        raise FileExistsError(
            f"出力先が既に存在する: {out}（上書きするには --overwrite を付ける）"
        )
    if out.exists() and out.is_dir():
        raise IsADirectoryError(f"出力先がディレクトリである: {out}")


def write_jsonl(records: list[dict[str, object]], out: Path, overwrite: bool) -> None:
    """判定結果レコードを JSONL として原子的に書き込む（design.md §1.4.4）。
    同じディレクトリに一時ファイルを作って書き切ってから `os.replace` で
    置き換える。`records` が空でも 0 バイトのファイルを作る。"""
    _check_output_writable(out, overwrite)

    out.parent.mkdir(parents=True, exist_ok=True)

    content = "".join(
        json.dumps(rec, ensure_ascii=False) + "\n" for rec in records
    )

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
    """CLI 引数の解析（design.md §1.7）。"""
    parser = argparse.ArgumentParser(
        description=(
            "候補レコードから content_list を逆引きして原本ページを特定し、"
            "判定結果レコードを出力する CLI"
        )
    )
    parser.add_argument(
        "candidates",
        type=Path,
        help="候補レコードの JSONL のパス",
    )
    parser.add_argument(
        "--final-dir",
        type=Path,
        required=True,
        help="content_list の親ディレクトリ（例: {BASE2}/ocr/final）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="出力先の JSONL のパス",
    )
    parser.add_argument(
        "--select",
        type=int,
        default=None,
        help=(
            "処理する候補の物理行番号（候補 JSONL の先頭行を 1 とする。"
            "空行も 1 行と数える）。省略時は全件を処理する"
        ),
    )
    parser.add_argument(
        "--judgment",
        choices=JUDGMENTS,
        default=None,
        help="判定の値。--select との併用時のみ指定できる",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="出力先が存在するとき上書きする（既定は拒否）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """全体の制御。終了コードを返す（`sys.exit` を内部で呼ばない。design.md §1.7）。"""
    args = parse_args(argv)
    candidates_path: Path = args.candidates
    final_dir: Path = args.final_dir
    out: Path = args.output
    select: int | None = args.select
    judgment: str | None = args.judgment
    overwrite: bool = args.overwrite

    # --judgment は --select との併用時のみ許可する（design.md §1.7）
    if judgment is not None and select is None:
        print("--judgment には --select の指定が必要である", file=sys.stderr)
        raise SystemExit(2)

    if not final_dir.is_dir():
        print(f"成果物ディレクトリが存在しない: {final_dir}", file=sys.stderr)
        return 1

    try:
        _check_output_writable(out, overwrite)
    except (FileExistsError, IsADirectoryError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        candidates = read_candidates(candidates_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if select is not None:
        targets = [(lineno, rec) for lineno, rec in candidates if lineno == select]
        if not targets:
            print(f"--select の行番号に候補レコードが無い: {select}", file=sys.stderr)
            raise SystemExit(2)
    else:
        targets = candidates

    blocks_cache: dict[str, list[dict[str, object]]] = {}
    results: list[dict[str, object]] = []
    success_count = 0

    for lineno, record in targets:
        chapter = record["chapter"]

        if chapter not in blocks_cache:
            try:
                content_list_path = resolve_content_list(final_dir, chapter)
            except (FileNotFoundError, ValueError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
            try:
                blocks_cache[chapter] = json.loads(
                    content_list_path.read_text(encoding="utf-8")
                )
            except (OSError, ValueError) as exc:
                print(
                    f"content_list が読み込めない: {content_list_path}（{exc}）",
                    file=sys.stderr,
                )
                return 1

        blocks = blocks_cache[chapter]
        block_idx, page_idx, k = locate_block(record, blocks)

        if judgment in ("missing", "not_missing") and page_idx is None:
            print(
                f"逆引き失敗の候補に {judgment} は指定できない",
                file=sys.stderr,
            )
            raise SystemExit(2)

        if page_idx is not None:
            success_count += 1

        results.append(make_result(record, page_idx, judgment))
        print(
            f"{lineno} {chapter} offset={record['offset']} "
            f"block={block_idx} page={page_idx} k={k}"
        )

    write_jsonl(results, out, overwrite)

    fail_count = len(results) - success_count
    print(
        f"処理: {len(results)} 件（逆引き成功 {success_count} 件 / "
        f"失敗 {fail_count} 件） → {out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
