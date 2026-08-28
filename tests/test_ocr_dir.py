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


# --- feat-011: 句読点スタイル連動 -------------------------------------------


def test_check_normalized_touten_pass(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("今日は、晴れ。", encoding="utf-8")
    dst.write_text("今日は、晴れ。", encoding="utf-8")

    errors = ocr_dir.check_normalized(src, dst, "touten")
    assert errors == []


def test_check_normalized_touten_rejects_punct_change(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("今日は、晴れ。", encoding="utf-8")
    dst.write_text("今日は，晴れ．", encoding="utf-8")

    errors = ocr_dir.check_normalized(src, dst, "touten")
    assert errors


def test_check_normalized_cjk_allowed(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("变换", encoding="utf-8")
    dst.write_text("変換", encoding="utf-8")

    for style in ("comma", "touten"):
        errors = ocr_dir.check_normalized(src, dst, style)
        assert errors == []


def test_check_normalized_cjk_residual(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    dst_dir = tmp_path / "normalized"
    dst_dir.mkdir()
    dst = dst_dir / "src.md"

    src.write_text("变换", encoding="utf-8")
    dst.write_text("变换", encoding="utf-8")

    for style in ("comma", "touten"):
        errors = ocr_dir.check_normalized(src, dst, style)
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


def test_parse_footnote_summary() -> None:
    stdout = "x.md: 2 inserted, 1 skipped\ntotal: 2 inserted, 1 skipped\n"
    assert ocr_dir.parse_footnote_summary(stdout) == (2, 1)


def test_parse_footnote_summary_no_match() -> None:
    assert ocr_dir.parse_footnote_summary("") is None


def test_insert_footnotes_success(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_content_list = tmp_path / "x_content_list.json"
    normalized_dir = tmp_path

    captured_cmd = {}

    class Result:
        returncode = 0
        stdout = "x.md: 2 inserted, 0 skipped\ntotal: 2 inserted, 0 skipped\n"
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        captured_cmd["cmd"] = cmd
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, footnotes, footnotes_skipped = ocr_dir.insert_footnotes(
        normalized_md, normalized_content_list, normalized_dir
    )
    assert errors == []
    assert (footnotes, footnotes_skipped) == (2, 0)
    cmd = captured_cmd["cmd"]
    assert "insert_footnotes.py" in cmd[1]
    assert "--overwrite" in cmd
    assert str(normalized_md) in cmd
    assert str(normalized_content_list) in cmd


def test_insert_footnotes_nonzero_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_content_list = tmp_path / "x_content_list.json"
    normalized_dir = tmp_path

    class Result:
        returncode = 1
        stdout = ""
        stderr = "boom"

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, footnotes, footnotes_skipped = ocr_dir.insert_footnotes(
        normalized_md, normalized_content_list, normalized_dir
    )
    assert len(errors) == 1
    assert errors[0] == "脚注挿入失敗: boom"
    assert (footnotes, footnotes_skipped) == (0, 0)


def test_insert_footnotes_summary_missing_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_content_list = tmp_path / "x_content_list.json"
    normalized_dir = tmp_path

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, footnotes, footnotes_skipped = ocr_dir.insert_footnotes(
        normalized_md, normalized_content_list, normalized_dir
    )
    assert len(errors) == 1
    assert "summary parse failed" in errors[0]
    assert (footnotes, footnotes_skipped) == (0, 0)


def test_insert_footnotes_warning_passes(tmp_path: Path, monkeypatch, capsys) -> None:
    normalized_md = tmp_path / "x.md"
    normalized_content_list = tmp_path / "x_content_list.json"
    normalized_dir = tmp_path

    class Result:
        returncode = 0
        stdout = "x.md: 1 inserted, 1 skipped\ntotal: 1 inserted, 1 skipped\n"
        stderr = "x.md: page 3: no anchor; 1 note(s) skipped"

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, footnotes, footnotes_skipped = ocr_dir.insert_footnotes(
        normalized_md, normalized_content_list, normalized_dir
    )
    assert errors == []
    assert (footnotes, footnotes_skipped) == (1, 1)
    captured = capsys.readouterr()
    assert "x.md: page 3: no anchor; 1 note(s) skipped" in captured.err


def test_process_dir_footnote_failure_marks_fail(tmp_path: Path, monkeypatch) -> None:
    d = tmp_path / "chap00" / "out"
    d.mkdir(parents=True)
    tif = d / "page-01_2R.tif"
    tif.write_bytes(b"\x00" * 20000)

    root = tmp_path / "root"
    args = ocr_dir.parse_args([str(d), "-o", str(root)])

    monkeypatch.setattr(ocr_dir, "list_tifs", lambda d, glob=None: [tif])
    monkeypatch.setattr(ocr_dir, "blank_positions", lambda files: set())
    monkeypatch.setattr(ocr_dir, "manifest_matches", lambda manifest_path, files: True)
    monkeypatch.setattr(
        ocr_dir, "insert_footnotes", lambda *a, **k: (["脚注挿入失敗: boom"], 0, 0)
    )

    class FakePdfReader:
        def __init__(self, path: str) -> None:
            self.pages = [None]

    monkeypatch.setattr(ocr_dir.pypdf, "PdfReader", FakePdfReader)

    # 既存の入力PDFを再利用させる（manifest_matches をスタブ済みのため中身は不問）。
    pdf_dir = root / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "chap00_gray300.pdf").write_bytes(b"%PDF-1.4\n")
    (pdf_dir / "chap00_gray300.pdf.manifest.json").write_text("{}", encoding="utf-8")

    page_text = "本文"
    page_content_list = json.dumps(
        [{"page_idx": 0, "type": "text", "text": page_text}]
    )

    def stub_subprocess_run(cmd, capture_output=True, text=True, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if cmd and cmd[0] == "mineru":
            # mineru CLI 呼び出しを模倣し、hybrid_auto 配下に md/content_list を生成する。
            pdf_path = Path(cmd[cmd.index("-p") + 1])
            out_dir = Path(cmd[cmd.index("-o") + 1])
            stem = pdf_path.stem
            hybrid_dir = out_dir / stem / "hybrid_auto"
            hybrid_dir.mkdir(parents=True, exist_ok=True)
            (hybrid_dir / f"{stem}.md").write_text(page_text, encoding="utf-8")
            (hybrid_dir / f"{stem}_content_list.json").write_text(
                page_content_list, encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "normalize_punct.py" in cmd[1]:
            md_src = Path(cmd[2])
            content_list_src = Path(cmd[3])
            outdir = Path(cmd[cmd.index("-o") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / md_src.name).write_text(
                md_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (outdir / content_list_src.name).write_text(
                content_list_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "html_table_to_md.py" in cmd[1]:
            result = Result()
            result.stdout = (
                "chap00_gray300.md: 0 converted, 0 skipped\n"
                "total: 0 converted, 0 skipped in 1 files\n"
            )
            return result

        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub_subprocess_run)

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is False
    assert any("脚注挿入失敗" in reason for reason in result.reasons)


def test_main_pass_line_includes_footnotes(monkeypatch, capsys, tmp_path: Path) -> None:
    root = tmp_path / "root"
    d = tmp_path / "chap00"
    d.mkdir()

    fake_result = ocr_dir.DirResult(
        name="chap00",
        passed=True,
        reasons=[],
        pages=1,
        blocks=1,
        replaced_md=0,
        replaced_json=0,
        seconds=1.0,
        tables=1,
        tables_skipped=0,
        footnotes=2,
        footnotes_skipped=1,
    )

    monkeypatch.setattr(ocr_dir, "process_dir", lambda d, root, args: fake_result)

    ret = ocr_dir.main([str(d), "-o", str(root)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "footnotes=2+1skipped" in captured.out


# --- feat-010: 修正適用ステップ -------------------------------------------


def test_parse_fixes_summary() -> None:
    stdout = "x.md: 2 applied, 1 skipped\ntotal: 2 applied, 1 skipped\n"
    assert ocr_dir.parse_fixes_summary(stdout) == (2, 1)


def test_parse_fixes_summary_no_match() -> None:
    assert ocr_dir.parse_fixes_summary("") is None


def test_apply_fixes_wrapper_success(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    fixes_file = tmp_path / "chap00.json"
    normalized_dir = tmp_path

    captured_cmd = {}

    class Result:
        returncode = 0
        stdout = "x.md: 1 applied, 0 skipped\ntotal: 1 applied, 0 skipped\n"
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        captured_cmd["cmd"] = cmd
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, applied, skipped = ocr_dir.apply_fixes(normalized_md, fixes_file, normalized_dir)
    assert errors == []
    assert (applied, skipped) == (1, 0)
    cmd = captured_cmd["cmd"]
    assert "apply_fixes.py" in cmd[1]
    assert "--overwrite" in cmd
    assert str(normalized_md) in cmd
    assert str(fixes_file) in cmd


def test_apply_fixes_wrapper_nonzero_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    fixes_file = tmp_path / "chap00.json"
    normalized_dir = tmp_path

    class Result:
        returncode = 1
        stdout = ""
        stderr = "boom"

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, applied, skipped = ocr_dir.apply_fixes(normalized_md, fixes_file, normalized_dir)
    assert len(errors) == 1
    assert errors[0] == "修正適用失敗: boom"
    assert (applied, skipped) == (0, 0)


def test_apply_fixes_wrapper_summary_missing_fail(tmp_path: Path, monkeypatch) -> None:
    normalized_md = tmp_path / "x.md"
    fixes_file = tmp_path / "chap00.json"
    normalized_dir = tmp_path

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def stub(cmd, capture_output=True, text=True):
        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub)

    errors, applied, skipped = ocr_dir.apply_fixes(normalized_md, fixes_file, normalized_dir)
    assert len(errors) == 1
    assert "summary parse failed" in errors[0]
    assert (applied, skipped) == (0, 0)


def _setup_process_dir_env(
    tmp_path: Path, monkeypatch, extra_args: list[str] | None = None
):
    """process_dir を feat-010 の修正適用ステップまで通すための共通環境。"""
    d = tmp_path / "chap00" / "out"
    d.mkdir(parents=True)
    tif = d / "page-01_2R.tif"
    tif.write_bytes(b"\x00" * 20000)

    root = tmp_path / "root"
    argv = [str(d), "-o", str(root)] + (extra_args or [])
    args = ocr_dir.parse_args(argv)

    monkeypatch.setattr(ocr_dir, "list_tifs", lambda d, glob=None: [tif])
    monkeypatch.setattr(ocr_dir, "blank_positions", lambda files: set())
    monkeypatch.setattr(ocr_dir, "manifest_matches", lambda manifest_path, files: True)
    monkeypatch.setattr(ocr_dir, "insert_footnotes", lambda *a, **k: ([], 0, 0))

    class FakePdfReader:
        def __init__(self, path: str) -> None:
            self.pages = [None]

    monkeypatch.setattr(ocr_dir.pypdf, "PdfReader", FakePdfReader)

    pdf_dir = root / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "chap00_gray300.pdf").write_bytes(b"%PDF-1.4\n")
    (pdf_dir / "chap00_gray300.pdf.manifest.json").write_text("{}", encoding="utf-8")

    page_text = "本文"
    page_content_list = json.dumps(
        [{"page_idx": 0, "type": "text", "text": page_text}]
    )

    def stub_subprocess_run(cmd, capture_output=True, text=True, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if cmd and cmd[0] == "mineru":
            pdf_path = Path(cmd[cmd.index("-p") + 1])
            out_dir = Path(cmd[cmd.index("-o") + 1])
            stem = pdf_path.stem
            hybrid_dir = out_dir / stem / "hybrid_auto"
            hybrid_dir.mkdir(parents=True, exist_ok=True)
            (hybrid_dir / f"{stem}.md").write_text(page_text, encoding="utf-8")
            (hybrid_dir / f"{stem}_content_list.json").write_text(
                page_content_list, encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "normalize_punct.py" in cmd[1]:
            md_src = Path(cmd[2])
            content_list_src = Path(cmd[3])
            outdir = Path(cmd[cmd.index("-o") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / md_src.name).write_text(
                md_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (outdir / content_list_src.name).write_text(
                content_list_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "html_table_to_md.py" in cmd[1]:
            result = Result()
            result.stdout = (
                "chap00_gray300.md: 0 converted, 0 skipped\n"
                "total: 0 converted, 0 skipped in 1 files\n"
            )
            return result

        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub_subprocess_run)

    return d, root, args


def test_process_dir_fixes_dir_none_step_not_run(tmp_path: Path, monkeypatch) -> None:
    d, root, args = _setup_process_dir_env(tmp_path, monkeypatch)

    called = {"count": 0}

    def fake_apply_fixes(*a, **k):
        called["count"] += 1
        return [], 1, 0

    monkeypatch.setattr(ocr_dir, "apply_fixes", fake_apply_fixes)

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is True
    assert called["count"] == 0
    assert (result.fixes_applied, result.fixes_skipped) == (0, 0)


def test_process_dir_fixes_file_missing_skipped(tmp_path: Path, monkeypatch) -> None:
    fixes_dir = tmp_path / "fixes"
    fixes_dir.mkdir()
    d, root, args = _setup_process_dir_env(
        tmp_path, monkeypatch, ["--fixes-dir", str(fixes_dir)]
    )

    called = {"count": 0}

    def fake_apply_fixes(*a, **k):
        called["count"] += 1
        return [], 1, 0

    monkeypatch.setattr(ocr_dir, "apply_fixes", fake_apply_fixes)

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is True
    assert called["count"] == 0
    assert (result.fixes_applied, result.fixes_skipped) == (0, 0)


def test_process_dir_fixes_applied_success(tmp_path: Path, monkeypatch) -> None:
    fixes_dir = tmp_path / "fixes"
    fixes_dir.mkdir()
    (fixes_dir / "chap00.json").write_text('{"fixes": []}', encoding="utf-8")
    d, root, args = _setup_process_dir_env(
        tmp_path, monkeypatch, ["--fixes-dir", str(fixes_dir)]
    )

    monkeypatch.setattr(ocr_dir, "apply_fixes", lambda *a, **k: ([], 1, 2))

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is True
    assert (result.fixes_applied, result.fixes_skipped) == (1, 2)


def test_process_dir_fixes_failure_marks_fail(tmp_path: Path, monkeypatch) -> None:
    fixes_dir = tmp_path / "fixes"
    fixes_dir.mkdir()
    (fixes_dir / "chap00.json").write_text('{"fixes": []}', encoding="utf-8")
    d, root, args = _setup_process_dir_env(
        tmp_path, monkeypatch, ["--fixes-dir", str(fixes_dir)]
    )

    monkeypatch.setattr(
        ocr_dir, "apply_fixes", lambda *a, **k: (["修正適用失敗: boom"], 0, 0)
    )

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is False
    assert any("修正適用失敗" in reason for reason in result.reasons)


def test_process_dir_passes_punct_style(tmp_path: Path, monkeypatch) -> None:
    d = tmp_path / "chap00" / "out"
    d.mkdir(parents=True)
    tif = d / "page-01_2R.tif"
    tif.write_bytes(b"\x00" * 20000)

    root = tmp_path / "root"
    args = ocr_dir.parse_args(
        [str(d), "-o", str(root), "--punct-style", "touten"]
    )

    monkeypatch.setattr(ocr_dir, "list_tifs", lambda d, glob=None: [tif])
    monkeypatch.setattr(ocr_dir, "blank_positions", lambda files: set())
    monkeypatch.setattr(ocr_dir, "manifest_matches", lambda manifest_path, files: True)
    monkeypatch.setattr(ocr_dir, "insert_footnotes", lambda *a, **k: ([], 0, 0))

    class FakePdfReader:
        def __init__(self, path: str) -> None:
            self.pages = [None]

    monkeypatch.setattr(ocr_dir.pypdf, "PdfReader", FakePdfReader)

    pdf_dir = root / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "chap00_gray300.pdf").write_bytes(b"%PDF-1.4\n")
    (pdf_dir / "chap00_gray300.pdf.manifest.json").write_text("{}", encoding="utf-8")

    page_text = "本文"
    page_content_list = json.dumps(
        [{"page_idx": 0, "type": "text", "text": page_text}]
    )

    captured_cmd = {}

    def stub_subprocess_run(cmd, capture_output=True, text=True, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if cmd and cmd[0] == "mineru":
            pdf_path = Path(cmd[cmd.index("-p") + 1])
            out_dir = Path(cmd[cmd.index("-o") + 1])
            stem = pdf_path.stem
            hybrid_dir = out_dir / stem / "hybrid_auto"
            hybrid_dir.mkdir(parents=True, exist_ok=True)
            (hybrid_dir / f"{stem}.md").write_text(page_text, encoding="utf-8")
            (hybrid_dir / f"{stem}_content_list.json").write_text(
                page_content_list, encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "normalize_punct.py" in cmd[1]:
            captured_cmd["cmd"] = cmd
            md_src = Path(cmd[2])
            content_list_src = Path(cmd[3])
            outdir = Path(cmd[cmd.index("-o") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / md_src.name).write_text(
                md_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (outdir / content_list_src.name).write_text(
                content_list_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "html_table_to_md.py" in cmd[1]:
            result = Result()
            result.stdout = (
                "chap00_gray300.md: 0 converted, 0 skipped\n"
                "total: 0 converted, 0 skipped in 1 files\n"
            )
            return result

        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub_subprocess_run)

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is True
    cmd = captured_cmd["cmd"]
    assert "--punct-style" in cmd
    assert cmd[cmd.index("--punct-style") + 1] == "touten"


def test_process_dir_forwards_normalize_stderr(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    d = tmp_path / "chap00" / "out"
    d.mkdir(parents=True)
    tif = d / "page-01_2R.tif"
    tif.write_bytes(b"\x00" * 20000)

    root = tmp_path / "root"
    args = ocr_dir.parse_args([str(d), "-o", str(root)])

    monkeypatch.setattr(ocr_dir, "list_tifs", lambda d, glob=None: [tif])
    monkeypatch.setattr(ocr_dir, "blank_positions", lambda files: set())
    monkeypatch.setattr(ocr_dir, "manifest_matches", lambda manifest_path, files: True)
    monkeypatch.setattr(ocr_dir, "insert_footnotes", lambda *a, **k: ([], 0, 0))

    class FakePdfReader:
        def __init__(self, path: str) -> None:
            self.pages = [None]

    monkeypatch.setattr(ocr_dir.pypdf, "PdfReader", FakePdfReader)

    pdf_dir = root / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "chap00_gray300.pdf").write_bytes(b"%PDF-1.4\n")
    (pdf_dir / "chap00_gray300.pdf.manifest.json").write_text("{}", encoding="utf-8")

    page_text = "本文"
    page_content_list = json.dumps(
        [{"page_idx": 0, "type": "text", "text": page_text}]
    )

    def stub_subprocess_run(cmd, capture_output=True, text=True, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if cmd and cmd[0] == "mineru":
            pdf_path = Path(cmd[cmd.index("-p") + 1])
            out_dir = Path(cmd[cmd.index("-o") + 1])
            stem = pdf_path.stem
            hybrid_dir = out_dir / stem / "hybrid_auto"
            hybrid_dir.mkdir(parents=True, exist_ok=True)
            (hybrid_dir / f"{stem}.md").write_text(page_text, encoding="utf-8")
            (hybrid_dir / f"{stem}_content_list.json").write_text(
                page_content_list, encoding="utf-8"
            )
            return Result()

        if len(cmd) > 1 and "normalize_punct.py" in cmd[1]:
            md_src = Path(cmd[2])
            content_list_src = Path(cmd[3])
            outdir = Path(cmd[cmd.index("-o") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / md_src.name).write_text(
                md_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (outdir / content_list_src.name).write_text(
                content_list_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            result = Result()
            result.stderr = "chap00_gray300.md: JIS外漢字 1 種 1 件\n  '跺' x1: ...文脈..."
            return result

        if len(cmd) > 1 and "html_table_to_md.py" in cmd[1]:
            result = Result()
            result.stdout = (
                "chap00_gray300.md: 0 converted, 0 skipped\n"
                "total: 0 converted, 0 skipped in 1 files\n"
            )
            return result

        return Result()

    monkeypatch.setattr(ocr_dir.subprocess, "run", stub_subprocess_run)

    result = ocr_dir.process_dir(d, root, args)

    assert result.passed is True
    captured = capsys.readouterr()
    assert "JIS外漢字" in captured.err


def test_main_pass_line_includes_fixes(monkeypatch, capsys, tmp_path: Path) -> None:
    root = tmp_path / "root"
    d = tmp_path / "chap00"
    d.mkdir()

    fake_result = ocr_dir.DirResult(
        name="chap00",
        passed=True,
        reasons=[],
        pages=1,
        blocks=1,
        replaced_md=0,
        replaced_json=0,
        seconds=1.0,
        tables=1,
        tables_skipped=0,
        footnotes=2,
        footnotes_skipped=1,
        fixes_applied=1,
        fixes_skipped=0,
    )

    monkeypatch.setattr(ocr_dir, "process_dir", lambda d, root, args: fake_result)

    ret = ocr_dir.main([str(d), "-o", str(root)])
    assert ret == 0

    captured = capsys.readouterr()
    assert "fixes=1+0skipped" in captured.out
