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
