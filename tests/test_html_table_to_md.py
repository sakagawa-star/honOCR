import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import html_table_to_md  # noqa: E402


def test_convert_table_simple() -> None:
    table_html = "<table><tr><td>a</td><td>b</td></tr><tr><td>1</td><td>2</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    assert lines == ["| a | b |", "| --- | --- |", "| 1 | 2 |"]


def test_convert_table_math_and_empty() -> None:
    table_html = (
        "<table><tr><td></td><td> $M = 0$ </td></tr>"
        "<tr><td> $w_{0}^{*}$ </td><td>0.19</td></tr></table>"
    )
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    assert lines[0] == "|  | $M = 0$ |"
    assert lines[2] == "| $w_{0}^{*}$ | 0.19 |"


def test_convert_table_th_thead_tbody() -> None:
    table_html = (
        "<table><thead><tr><th>a</th><th>b</th></tr></thead>"
        "<tbody><tr><td>1</td><td>2</td></tr></tbody></table>"
    )
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    assert lines == ["| a | b |", "| --- | --- |", "| 1 | 2 |"]


def test_convert_table_entities() -> None:
    table_html = "<table><tr><td>a &lt; b</td><td>x &amp; y</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    assert lines == ["| a < b | x & y |", "| --- | --- |"]


def test_convert_table_ragged() -> None:
    table_html = "<table><tr><td>a</td><td>b</td></tr><tr><td>1</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "ragged rows"


def test_convert_table_attribute() -> None:
    table_html = '<table><tr><td colspan="2">a</td></tr></table>'
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "attribute on <td>"


def test_convert_table_unsupported_tag() -> None:
    table_html = "<table><tr><td>a<br>b</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "unsupported tag in cell"


def test_convert_table_pipe() -> None:
    table_html = "<table><tr><td>a|b</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "pipe in cell"


def test_convert_table_lt_in_math() -> None:
    table_html = "<table><tr><td>$a<b$</td><td>$c>d$</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert reason is None
    assert lines == ["| $a<b$ | $c>d$ |", "| --- | --- |"]


def test_convert_table_text_outside_cell() -> None:
    table_html = "<table><tr>x<td>a</td></tr></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "text outside cell"


def test_convert_table_no_rows() -> None:
    table_html = "<table></table>"
    lines, reason = html_table_to_md.convert_table(table_html)
    assert lines == []
    assert reason == "no rows"


def test_convert_text_replaces_line() -> None:
    text = "\n<table><tr><td>a</td><td>b</td></tr></table>\n\n本文"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (1, 0)
    assert warnings == []
    lines = out.split("\n")
    assert lines == ["", "| a | b |", "| --- | --- |", "", "本文"]


def test_convert_text_inserts_blank_lines() -> None:
    text = "本文\n<table><tr><td>a</td></tr></table>\n本文2"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (1, 0)
    lines = out.split("\n")
    assert lines[0] == "本文"
    assert lines[1] == ""
    assert lines[2] == "| a |"
    assert lines[3] == "| --- |"
    assert lines[4] == ""
    assert lines[5] == "本文2"


def test_convert_text_skip_keeps_line() -> None:
    original_line = '<table><tr><td colspan="2">a</td></tr></table>'
    text = f"本文\n{original_line}\n本文2"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (0, 1)
    assert out == text
    assert len(warnings) == 1
    assert "x.md:2:" in warnings[0]
    assert "attribute on <td>" in warnings[0]


def test_convert_text_multiline_table() -> None:
    text = "本文\n<table>\n<tr><td>a</td></tr>\n</table>\n本文2"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (0, 1)
    assert out == text
    assert len(warnings) == 1
    assert "x.md:2:" in warnings[0]
    assert "multi-line table" in warnings[0]


def test_convert_text_no_tables() -> None:
    text = "本文1\n本文2\n"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (0, 0)
    assert out == text
    assert warnings == []


def test_convert_text_eof_without_newline() -> None:
    text = "本文\n<table><tr><td>a</td></tr></table>"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (1, 0)
    assert not out.endswith("\n")
    assert out.split("\n")[-1] == "| --- |"


def test_convert_text_crlf_no_tables() -> None:
    text = "本文1\r\n本文2\r\n"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (0, 0)
    assert out == text


def test_convert_text_crlf_with_table() -> None:
    text = "本文\r\n<table><tr><td>a</td></tr></table>\r\n本文2\r\n"
    out, converted, skipped, warnings = html_table_to_md.convert_text(text, "x.md")
    assert (converted, skipped) == (1, 0)
    # 表行以外はバイト不変（\r\n を保持）。表行前後は非空行に隣接するため
    # 空行が挿入され、パイプテーブル各行末も \r\n になる。
    assert out == "本文\r\n\r\n| a |\r\n| --- |\r\n\r\n本文2\r\n"


def test_cli_writes_output(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    original = "本文\n<table><tr><td>a</td><td>b</td></tr></table>\n本文2\n"
    src.write_text(original, encoding="utf-8")
    outdir = tmp_path / "out"

    ret = html_table_to_md.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    text = output.read_text(encoding="utf-8")
    assert "| --- | --- |" in text
    assert src.read_text(encoding="utf-8") == original


def test_cli_inplace_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    original = "<table><tr><td>a</td></tr></table>\n"
    src.write_text(original, encoding="utf-8")

    ret = html_table_to_md.main([str(src), "-o", str(tmp_path), "--overwrite"])
    assert ret == 0

    text = src.read_text(encoding="utf-8")
    assert "| --- |" in text
    assert "<table" not in text


def test_cli_output_exists_without_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("<table><tr><td>a</td></tr></table>\n", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir()
    output = outdir / "src.md"
    output.write_text("existing-content", encoding="utf-8")

    ret = html_table_to_md.main([str(src), "-o", str(outdir)])
    assert ret == 1
    assert output.read_text(encoding="utf-8") == "existing-content"


def test_cli_missing_input(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    outdir = tmp_path / "out"

    ret = html_table_to_md.main([str(missing), "-o", str(outdir)])
    assert ret == 1
