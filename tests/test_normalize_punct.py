import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import normalize_punct  # noqa: E402


def test_replaces_punctuation(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_text(encoding="utf-8") == "今日は，晴れ．"


def test_preserves_other_content(tmp_path: Path) -> None:
    content = "，．$x_{1}$ \\tag{1.9}"
    src = tmp_path / "src.md"
    src.write_text(content, encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_bytes() == src.read_bytes()
    assert output.read_text(encoding="utf-8") == content


def test_input_unchanged(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    original = "今日は、晴れ。"
    src.write_text(original, encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0
    assert src.read_text(encoding="utf-8") == original


def test_cli_missing_input(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(missing), "-o", str(outdir)])
    assert ret == 1
    assert not (outdir / "missing.md").exists()


def test_cli_not_utf8(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_bytes(bytes([0x80, 0xFF]))
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 1
    assert not (outdir / "src.md").exists()


def test_cli_duplicate_basename(tmp_path: Path) -> None:
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    src_a = dir_a / "src.md"
    src_b = dir_b / "src.md"
    src_a.write_text("今日は、晴れ。", encoding="utf-8")
    src_b.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src_a), str(src_b), "-o", str(outdir)])
    assert ret == 1
    assert not (outdir / "src.md").exists()


def test_cli_refuses_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir()
    output = outdir / "src.md"
    output.write_text("existing-content", encoding="utf-8")

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 1
    assert output.read_text(encoding="utf-8") == "existing-content"


def test_cli_overwrite_flag(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir()
    output = outdir / "src.md"
    output.write_text("existing-content", encoding="utf-8")

    ret = normalize_punct.main([str(src), "-o", str(outdir), "--overwrite"])
    assert ret == 0
    assert output.read_text(encoding="utf-8") == "今日は，晴れ．"


# --- feat-011: 句読点スタイル・字形正規化・JIS外漢字警告 ---------------------


def test_punct_style_default_is_comma(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_text(encoding="utf-8") == "今日は，晴れ．"


def test_punct_style_touten_keeps_punctuation(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir), "--punct-style", "touten"])
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_text(encoding="utf-8") == "今日は、晴れ。"


def test_punct_style_invalid_value(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。", encoding="utf-8")
    outdir = tmp_path / "out"

    with pytest.raises(SystemExit) as exc_info:
        normalize_punct.main(
            [str(src), "-o", str(outdir), "--punct-style", "invalid"]
        )
    assert exc_info.value.code == 2


def test_cjk_normalized_in_comma_style(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("二值变数・单・对・图・换・徵・樣", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_text(encoding="utf-8") == "二値変数・単・対・図・換・徴・様"


def test_cjk_normalized_in_touten_style(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("二值变数・单・对・图・换・徵・樣", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main(
        [str(src), "-o", str(outdir), "--punct-style", "touten"]
    )
    assert ret == 0

    output = outdir / "src.md"
    assert output.read_text(encoding="utf-8") == "二値変数・単・対・図・換・徴・様"


def test_replace_count_includes_cjk(tmp_path: Path, capsys) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は、晴れ。值", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "src.md: 3 replaced" in captured.out


def test_length_preserved(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    content = "今日は、晴れ。值变单对图换徵樣"
    src.write_text(content, encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    output = outdir / "src.md"
    assert len(output.read_text(encoding="utf-8")) == len(content)


def test_non_jis_warning_emitted(tmp_path: Path, capsys) -> None:
    src = tmp_path / "src.md"
    src.write_text("濵習と跺な解", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "src.md: JIS外漢字 2 種 2 件" in captured.err
    assert "'跺' x1:" in captured.err
    assert "'濵' x1:" in captured.err


def test_non_jis_warning_exit_code_zero(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_text("濵習", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0


def test_non_jis_warning_absent_when_clean(tmp_path: Path, capsys) -> None:
    src = tmp_path / "src.md"
    src.write_text("今日は，晴れ．", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""


def test_non_jis_warning_excludes_replaced_chars(tmp_path: Path, capsys) -> None:
    src = tmp_path / "src.md"
    src.write_text("变", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = normalize_punct.main([str(src), "-o", str(outdir)])
    assert ret == 0

    captured = capsys.readouterr()
    assert captured.err == ""


def test_build_replacements_comma_and_touten() -> None:
    comma = normalize_punct.build_replacements("comma")
    touten = normalize_punct.build_replacements("touten")

    assert set(comma.keys()) == {"、", "。"} | set(normalize_punct.CJK_REPLACEMENTS)
    assert set(touten.keys()) == set(normalize_punct.CJK_REPLACEMENTS)


def test_is_jis_x0208() -> None:
    assert normalize_punct.is_jis_x0208("値") is True
    assert normalize_punct.is_jis_x0208("值") is False
    assert normalize_punct.is_jis_x0208("樣") is True
