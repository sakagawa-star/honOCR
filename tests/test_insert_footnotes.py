import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import html_table_to_md  # noqa: E402
import insert_footnotes  # noqa: E402


def _write_content_list(path: Path, blocks: list[dict]) -> None:
    path.write_text(json.dumps(blocks, ensure_ascii=False), encoding="utf-8")


# --- 1: 通常挿入 -------------------------------------------------------


def test_insert_normal() -> None:
    md = "本文A\n\n本文B\n\n"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {"type": "text", "text": "本文B", "page_idx": 0, "bbox": [0, 20, 10, 30]},
        {
            "type": "page_footnote",
            "text": "1 注釈テキスト",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (1, 0)
    assert warnings == []
    assert result == "本文A\n\n本文B\n\n> 1 注釈テキスト\n\n"


# --- 2: 複数脚注の順序 ---------------------------------------------------


def test_insert_multiple_footnotes_order() -> None:
    md = "本文A\n\n"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "page_footnote",
            "text": "1 一番目",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
        {
            "type": "page_footnote",
            "text": "2 二番目",
            "page_idx": 0,
            "bbox": [0, 120, 10, 130],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (2, 0)
    assert result == "本文A\n\n> 1 一番目\n\n> 2 二番目\n\n"
    idx1 = result.index("1 一番目")
    idx2 = result.index("2 二番目")
    assert idx1 < idx2


# --- 3: 浮遊断片除去（空白差含む） ---------------------------------------


def test_assemble_floating_fragment_removed() -> None:
    blocks = [
        {"text": "3 見よ $|U| = 1$ のとき", "bbox": [0, 0, 10, 10]},
        {"text": "$|U|=1$", "bbox": [0, 5, 10, 8]},
        {"text": "の場合を考える．", "bbox": [0, 20, 10, 30]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["3 見よ $|U| = 1$ のとき の場合を考える．"]


# --- 4: bbox 並べ替え ----------------------------------------------------


def test_assemble_bbox_reorders() -> None:
    blocks = [
        {"text": "2 二番目", "bbox": [0, 50, 10, 60]},
        {"text": "1 一番目", "bbox": [0, 10, 10, 20]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["1 一番目", "2 二番目"]


# --- 5: 番号なし先頭ブロック ---------------------------------------------


def test_assemble_no_prefix_first_block_alone() -> None:
    blocks = [
        {"text": "英語では圧倒的に joint が使われる．", "bbox": [0, 0, 10, 10]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["英語では圧倒的に joint が使われる．"]


# --- 6: 番号なし連結 -------------------------------------------------------


def test_assemble_no_prefix_concatenation() -> None:
    blocks = [
        {"text": "5 定義", "bbox": [0, 0, 10, 10]},
        {"text": "$x^{2}$", "bbox": [0, 10, 10, 20]},
        {"text": "である．", "bbox": [0, 20, 10, 30]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["5 定義 $x^{2}$ である．"]


# --- 7: アンカーなし ------------------------------------------------------


def test_insert_no_anchor_skipped_with_warning() -> None:
    md = "本文A\n\n"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "page_footnote",
            "text": "1 見つからないページの脚注",
            "page_idx": 5,
            "bbox": [0, 0, 10, 10],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (0, 1)
    assert result == md
    assert warnings == ["x.md: page 5: no anchor; 1 note(s) skipped"]


# --- 8: 冪等性 -------------------------------------------------------------


def test_insert_idempotent_on_reapply() -> None:
    md = "本文A\n\n"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "page_footnote",
            "text": "1 注釈",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    once, inserted1, skipped1, _ = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )
    assert (inserted1, skipped1) == (1, 0)

    twice, inserted2, skipped2, warnings2 = insert_footnotes.insert_notes(
        once, "x.md", content_list
    )

    assert (inserted2, skipped2) == (0, 1)
    assert twice == once
    assert warnings2 == []


# --- 9: 画像アンカー -------------------------------------------------------


def test_insert_image_anchor() -> None:
    md = "本文\n\n![](images/fig1.jpg)\n\n"
    content_list = [
        {"type": "text", "text": "本文", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "image",
            "img_path": "images/fig1.jpg",
            "page_idx": 0,
            "bbox": [0, 20, 10, 30],
        },
        {
            "type": "page_footnote",
            "text": "1 図の説明",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (1, 0)
    assert warnings == []
    assert result == "本文\n\n![](images/fig1.jpg)\n\n> 1 図の説明\n\n"


# --- 9b: 表アンカー（未変換） ----------------------------------------------


def test_insert_table_anchor_html_unconverted() -> None:
    table_html = "<table><tr><td>a</td><td>b</td></tr></table>"
    md = f"本文\n\n{table_html}\n\n"
    content_list = [
        {"type": "text", "text": "本文", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "table",
            "table_body": table_html,
            "img_path": "images/tbl1.jpg",
            "page_idx": 0,
            "bbox": [0, 20, 10, 30],
        },
        {
            "type": "page_footnote",
            "text": "1 表の脚注",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (1, 0)
    assert warnings == []
    assert result == f"本文\n\n{table_html}\n\n> 1 表の脚注\n\n"


# --- 9c: 表アンカー（変換後） ------------------------------------------------


def test_insert_table_anchor_converted_md() -> None:
    table_html = "<table><tr><td>a</td><td>b</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    converted = "\n".join(lines)
    md = f"本文\n\n{converted}\n\n"
    content_list = [
        {"type": "text", "text": "本文", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "table",
            "table_body": table_html,
            "page_idx": 0,
            "bbox": [0, 20, 10, 30],
        },
        {
            "type": "page_footnote",
            "text": "1 表の脚注",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (1, 0)
    assert warnings == []
    assert result == f"本文\n\n{converted}\n\n> 1 表の脚注\n\n"


# --- 10: 末尾ページ（後続 \n\n なし） -----------------------------------------


def test_insert_at_tail_without_trailing_blank() -> None:
    md = "本文A"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {
            "type": "page_footnote",
            "text": "1 末尾脚注",
            "page_idx": 0,
            "bbox": [0, 100, 10, 110],
        },
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (1, 0)
    assert result == "本文A\n\n> 1 末尾脚注"


# --- 11: 脚注 0 件 ---------------------------------------------------------


def test_insert_zero_footnotes() -> None:
    md = "本文A\n\n本文B\n\n"
    content_list = [
        {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
        {"type": "text", "text": "本文B", "page_idx": 0, "bbox": [0, 20, 10, 30]},
    ]

    result, inserted, skipped, warnings = insert_footnotes.insert_notes(
        md, "x.md", content_list
    )

    assert (inserted, skipped) == (0, 0)
    assert result == md
    assert warnings == []


# --- 12: CLI overwrite 拒否 ------------------------------------------------


def test_cli_overwrite_rejected(tmp_path: Path) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("本文A\n\n", encoding="utf-8")
    content_list_path = tmp_path / "x_content_list.json"
    _write_content_list(
        content_list_path,
        [{"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]}],
    )

    outdir = tmp_path / "out"
    outdir.mkdir()
    output_path = outdir / "x.md"
    output_path.write_text("existing-content", encoding="utf-8")

    ret = insert_footnotes.main(
        [str(md_path), str(content_list_path), "-o", str(outdir)]
    )

    assert ret == 1
    assert output_path.read_text(encoding="utf-8") == "existing-content"


# --- 13: CLI サマリ形式 -----------------------------------------------------


def test_cli_summary_format(tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("本文A\n\n", encoding="utf-8")
    content_list_path = tmp_path / "x_content_list.json"
    _write_content_list(
        content_list_path,
        [
            {"type": "text", "text": "本文A", "page_idx": 0, "bbox": [0, 0, 10, 10]},
            {
                "type": "page_footnote",
                "text": "1 注釈",
                "page_idx": 0,
                "bbox": [0, 100, 10, 110],
            },
        ],
    )
    outdir = tmp_path / "out"

    ret = insert_footnotes.main(
        [str(md_path), str(content_list_path), "-o", str(outdir)]
    )

    assert ret == 0
    captured = capsys.readouterr()
    lines = captured.out.strip("\n").split("\n")
    assert lines == ["x.md: 1 inserted, 0 skipped", "total: 1 inserted, 0 skipped"]


# --- 14: CLI 不正 JSON ------------------------------------------------------


def test_cli_invalid_json(tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("本文A\n\n", encoding="utf-8")
    content_list_path = tmp_path / "x_content_list.json"
    content_list_path.write_text("{not valid json", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = insert_footnotes.main(
        [str(md_path), str(content_list_path), "-o", str(outdir)]
    )

    assert ret == 1
    captured = capsys.readouterr()
    assert captured.err.strip() != ""


# --- feat-011: 脚注プレフィックス・断片判定の拡張 ---------------------------


def test_assemble_asterisk_prefix_splits_notes() -> None:
    blocks = [
        {"text": "\\*2 参考文献 [8] の…", "bbox": [0, 0, 10, 10]},
        {"text": "$^{3}$ ただし精度という…", "bbox": [0, 20, 10, 30]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["\\*2 参考文献 [8] の…", "$^{3}$ ただし精度という…"]


def test_assemble_asterisk_without_backslash() -> None:
    blocks = [
        {"text": "*4 本文", "bbox": [0, 0, 10, 10]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["*4 本文"]


def test_assemble_superscript_math_prefix() -> None:
    blocks = [
        {"text": "$^{*4}$ 本文", "bbox": [0, 0, 10, 10]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["$^{*4}$ 本文"]


def test_assemble_page_ref_superscript_not_prefix() -> None:
    blocks = [
        {"text": "1 本文", "bbox": [0, 0, 10, 10]},
        {"text": "$^{(p.128)}$ 続き", "bbox": [0, 20, 10, 30]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["1 本文 $^{(p.128)}$ 続き"]


def test_assemble_fragment_with_math_removed() -> None:
    blocks = [
        {
            "text": "\\*4 厳密に言えば、$[0,1)$ でなく $(0,1]$ とすべき",
            "bbox": [0, 0, 10, 10],
        },
        {"text": "[0,1) でなく (0,1]", "bbox": [0, 5, 10, 8]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["\\*4 厳密に言えば、$[0,1)$ でなく $(0,1]$ とすべき"]


def test_assemble_keeps_original_text() -> None:
    blocks = [
        {"text": "\\*4 厳密に言えば、$[0,1)$ でなく $(0,1]$ とすべき", "bbox": [0, 0, 10, 10]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["\\*4 厳密に言えば、$[0,1)$ でなく $(0,1]$ とすべき"]
    assert "$" in notes[0]
    assert "\\" in notes[0]


def test_assemble_empty_key_block_kept() -> None:
    blocks = [
        {"text": "1 本文", "bbox": [0, 0, 10, 10]},
        {"text": "$$", "bbox": [0, 20, 10, 30]},
    ]

    notes = insert_footnotes.assemble_notes(blocks)

    assert notes == ["1 本文 $$"]


def test_comparison_key() -> None:
    assert insert_footnotes.comparison_key("a $b$ \\c") == "abc"
