import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import ocr_dir  # noqa: E402


def test_derive_name_plain() -> None:
    assert ocr_dir.derive_name(Path("/x/chap03")) == "chap03"


def test_derive_name_out() -> None:
    assert ocr_dir.derive_name(Path("/x/chap03/out")) == "chap03"


def test_blank_positions(tmp_path: Path) -> None:
    sizes = [5000, 20000, 3000, 50000]
    files = []
    for i, size in enumerate(sizes):
        path = tmp_path / f"page-{i}.tif"
        path.write_bytes(b"\x00" * size)
        files.append(path)

    result = ocr_dir.blank_positions(files)
    assert result == {0, 2}


def test_next_run_number_empty(tmp_path: Path) -> None:
    name_dir = tmp_path / "chap03"
    assert ocr_dir.next_run_number(name_dir) == 1


def test_next_run_number_existing(tmp_path: Path) -> None:
    name_dir = tmp_path / "chap03"
    (name_dir / "run-01").mkdir(parents=True)
    (name_dir / "run-03").mkdir(parents=True)

    assert ocr_dir.next_run_number(name_dir) == 4


def _write_content_list(path: Path, blocks: list[dict]) -> None:
    path.write_text(json.dumps(blocks), encoding="utf-8")


def test_check_page_idx_pass(tmp_path: Path) -> None:
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"page_idx": 0}, {"page_idx": 2}],
    )

    errors = ocr_dir.check_page_idx(content_list, page_count=3, blanks={1})
    assert errors == []


def test_check_page_idx_missing_fail(tmp_path: Path) -> None:
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"page_idx": 0}, {"page_idx": 2}],
    )

    errors = ocr_dir.check_page_idx(content_list, page_count=3, blanks=set())
    assert errors
    assert any("1" in e for e in errors)


def test_check_page_idx_extra_fail(tmp_path: Path) -> None:
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"page_idx": 0}, {"page_idx": 5}],
    )

    errors = ocr_dir.check_page_idx(content_list, page_count=2, blanks=set())
    assert errors
    assert any("5" in e for e in errors)


def test_check_page_idx_non_int_fail(tmp_path: Path) -> None:
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"page_idx": 0}, {"foo": "bar"}],
    )

    errors = ocr_dir.check_page_idx(content_list, page_count=2, blanks=set())
    assert errors


def test_check_normalized_pass(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("今日は、晴れ。", encoding="utf-8")
    dst.write_text("今日は，晴れ．", encoding="utf-8")

    errors = ocr_dir.check_normalized(src, dst)
    assert errors == []


def test_check_normalized_bad_diff(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("今日は、晴れ。", encoding="utf-8")
    dst.write_text("今日は，曇り．", encoding="utf-8")

    errors = ocr_dir.check_normalized(src, dst)
    assert errors


def test_check_normalized_residual(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("今日は、晴れ。", encoding="utf-8")
    dst.write_text("今日は、晴れ。", encoding="utf-8")

    errors = ocr_dir.check_normalized(src, dst)
    assert errors


def test_manifest_roundtrip_match(tmp_path: Path) -> None:
    files = []
    for i in range(2):
        path = tmp_path / f"page-{i}.tif"
        path.write_bytes(b"\x00" * 1000)
        files.append(path)

    manifest_path = tmp_path / "manifest.json"
    manifest = ocr_dir.build_manifest(files)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert ocr_dir.manifest_matches(manifest_path, files) is True


def test_manifest_mismatch(tmp_path: Path) -> None:
    files = []
    for i in range(2):
        path = tmp_path / f"page-{i}.tif"
        path.write_bytes(b"\x00" * 1000)
        files.append(path)

    manifest_path = tmp_path / "manifest.json"
    manifest = ocr_dir.build_manifest(files)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    files[0].write_bytes(b"\x00" * 2000)

    assert ocr_dir.manifest_matches(manifest_path, files) is False


def test_cli_name_with_multiple_dirs(tmp_path: Path) -> None:
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()
    root = tmp_path / "root"

    ret = ocr_dir.main(
        [str(dir1), str(dir2), "--name", "x", "-o", str(root)]
    )
    assert ret == 2


def test_cli_duplicate_names(tmp_path: Path) -> None:
    dir_a = tmp_path / "a" / "out"
    dir_b = tmp_path / "a"
    dir_a.mkdir(parents=True)
    root = tmp_path / "root"

    ret = ocr_dir.main([str(dir_a), str(dir_b), "-o", str(root)])
    assert ret == 2


def test_cli_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    root = tmp_path / "root"

    ret = ocr_dir.main([str(missing), "-o", str(root)])
    assert ret == 1


def test_parse_table_summary() -> None:
    stdout = "x.md: 2 converted, 1 skipped\ntotal: 2 converted, 1 skipped in 1 files\n"
    assert ocr_dir.parse_table_summary(stdout) == (2, 1)


def test_parse_table_summary_no_match() -> None:
    assert ocr_dir.parse_table_summary("") is None


def test_convert_tables_success(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_dir = tmp_path

    captured_cmd = {}

    class Result:
        returncode = 0
        stdout = "x.md: 2 converted, 0 skipped\ntotal: 2 converted, 0 skipped in 1 files\n"
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        captured_cmd["cmd"] = cmd
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, tables, tables_skipped = ocr_dir.convert_tables(normalized_md, normalized_dir)
    assert errors == []
    assert (tables, tables_skipped) == (2, 0)
    cmd = captured_cmd["cmd"]
    assert "html_table_to_md.py" in cmd[1]
    assert "--overwrite" in cmd
    assert str(normalized_md) in cmd


def test_convert_tables_nonzero_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_dir = tmp_path

    class Result:
        returncode = 1
        stdout = ""
        stderr = "boom"

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, tables, tables_skipped = ocr_dir.convert_tables(normalized_md, normalized_dir)
    assert len(errors) == 1
    assert errors[0] == "HTML表変換失敗: boom"
    assert (tables, tables_skipped) == (0, 0)


def test_convert_tables_summary_missing_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_dir = tmp_path

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, tables, tables_skipped = ocr_dir.convert_tables(normalized_md, normalized_dir)
    assert len(errors) == 1
    assert "summary parse failed" in errors[0]
    assert (tables, tables_skipped) == (0, 0)


def test_convert_tables_warning_passes(tmp_path: Path, monkeypatch, capsys) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_dir = tmp_path

    class Result:
        returncode = 0
        stdout = "x.md: 1 converted, 1 skipped\ntotal: 1 converted, 1 skipped in 1 files\n"
        stderr = "x.md:3: skipped (ragged rows)"

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, tables, tables_skipped = ocr_dir.convert_tables(normalized_md, normalized_dir)
    assert errors == []
    assert (tables, tables_skipped) == (1, 1)
    captured = capsys.readouterr()
    assert "x.md:3: skipped (ragged rows)" in captured.err
