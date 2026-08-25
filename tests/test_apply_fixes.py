import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import apply_fixes  # noqa: E402


def _write_fixes(path: Path, fixes: list[dict]) -> None:
    path.write_text(json.dumps({"fixes": fixes}, ensure_ascii=False), encoding="utf-8")


# --- 1: 通常適用 -------------------------------------------------------


def test_apply_normal() -> None:
    md = "alpha OLDVAL beta"
    fixes = [{"id": "f1", "reason": "r", "old": "OLDVAL", "new": "NEWVAL"}]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert errors == []
    assert (applied, skipped) == (1, 0)
    assert result == "alpha NEWVAL beta"


# --- 2: 複数修正の逐次適用 ------------------------------------------------


def test_apply_sequential() -> None:
    md = "one TARGET two"
    fixes = [
        {"id": "f1", "reason": "r1", "old": "TARGET", "new": "MIDDLE"},
        {"id": "f2", "reason": "r2", "old": "MIDDLE two", "new": "MIDDLE three"},
    ]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert errors == []
    assert (applied, skipped) == (2, 0)
    assert result == "one MIDDLE three"


# --- 3: 適用済みスキップ ---------------------------------------------------


def test_apply_already_applied_skipped() -> None:
    md = "one FINAL two"
    fixes = [{"id": "f1", "reason": "r", "old": "MIDDLE", "new": "FINAL"}]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert errors == []
    assert (applied, skipped) == (0, 1)
    assert result == md


# --- 4: 適用済み曖昧エラー -------------------------------------------------


def test_apply_ambiguous_new_error() -> None:
    md = "FINAL and FINAL again"
    fixes = [{"id": "f1", "reason": "r", "old": "MIDDLE", "new": "FINAL"}]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert len(errors) == 1
    assert "ambiguous" in errors[0]
    assert "f1" in errors[0]


# --- 5: old 不在エラー ------------------------------------------------------


def test_apply_old_not_found_error() -> None:
    md = "nothing relevant here"
    fixes = [{"id": "f1", "reason": "r", "old": "MISSING", "new": "REPLACEMENT"}]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert len(errors) == 1
    assert "not found" in errors[0]
    assert "f1" in errors[0]


# --- 6: old 非一意エラー -----------------------------------------------------


def test_apply_old_not_unique_error() -> None:
    md = "DUPE here and DUPE there"
    fixes = [{"id": "f1", "reason": "r", "old": "DUPE", "new": "SINGLE"}]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert len(errors) == 1
    assert "not unique" in errors[0]
    assert "f1" in errors[0]


# --- 7: エラー全件収集 -------------------------------------------------------


def test_apply_collects_all_errors() -> None:
    md = "nothing relevant here"
    fixes = [
        {"id": "f1", "reason": "r", "old": "MISSING1", "new": "REPL1"},
        {"id": "f2", "reason": "r", "old": "MISSING2", "new": "REPL2"},
    ]

    result, applied, skipped, errors = apply_fixes.apply_fixes(md, fixes, "x.json")

    assert len(errors) == 2
    assert any("f1" in e for e in errors)
    assert any("f2" in e for e in errors)


# --- 8: 冪等性 ---------------------------------------------------------------


def test_apply_idempotent_on_reapply() -> None:
    md = "alpha OLDVAL beta"
    fixes = [{"id": "f1", "reason": "r", "old": "OLDVAL", "new": "NEWVAL"}]

    once, applied1, skipped1, errors1 = apply_fixes.apply_fixes(md, fixes, "x.json")
    assert errors1 == []
    assert (applied1, skipped1) == (1, 0)

    twice, applied2, skipped2, errors2 = apply_fixes.apply_fixes(once, fixes, "x.json")

    assert errors2 == []
    assert (applied2, skipped2) == (0, 1)
    assert twice == once


# --- 9: スキーマ検証 ----------------------------------------------------------


def test_validate_missing_key() -> None:
    data = {"fixes": [{"id": "f1", "reason": "r", "old": "a"}]}
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert errors


def test_validate_duplicate_id() -> None:
    data = {
        "fixes": [
            {"id": "dup", "reason": "r", "old": "a", "new": "b"},
            {"id": "dup", "reason": "r", "old": "c", "new": "d"},
        ]
    }
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert any("unique" in e for e in errors)


def test_validate_empty_old() -> None:
    data = {"fixes": [{"id": "f1", "reason": "r", "old": "", "new": "b"}]}
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert any("old" in e for e in errors)


def test_validate_empty_new() -> None:
    data = {"fixes": [{"id": "f1", "reason": "r", "old": "a", "new": ""}]}
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert any("new" in e for e in errors)


def test_validate_old_equals_new() -> None:
    data = {"fixes": [{"id": "f1", "reason": "r", "old": "same", "new": "same"}]}
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert any("differ" in e for e in errors)


def test_validate_top_level_not_dict() -> None:
    errors = apply_fixes.validate_fixes(["not", "a", "dict"], "x.json")
    assert errors


def test_validate_fixes_not_list() -> None:
    errors = apply_fixes.validate_fixes({"fixes": "not a list"}, "x.json")
    assert errors


def test_validate_pass() -> None:
    data = {"fixes": [{"id": "f1", "reason": "r", "old": "a", "new": "b"}]}
    errors = apply_fixes.validate_fixes(data, "x.json")
    assert errors == []


# --- 10: 空 fixes -------------------------------------------------------------


def test_apply_empty_fixes() -> None:
    md = "unchanged text"
    result, applied, skipped, errors = apply_fixes.apply_fixes(md, [], "x.json")

    assert errors == []
    assert (applied, skipped) == (0, 0)
    assert result == md


def test_validate_empty_fixes_list() -> None:
    errors = apply_fixes.validate_fixes({"fixes": []}, "x.json")
    assert errors == []


# --- 11: CLI overwrite 拒否 -----------------------------------------------


def test_cli_overwrite_rejected(tmp_path: Path) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("alpha OLDVAL beta", encoding="utf-8")
    fixes_path = tmp_path / "x.json"
    _write_fixes(fixes_path, [{"id": "f1", "reason": "r", "old": "OLDVAL", "new": "NEWVAL"}])

    outdir = tmp_path / "out"
    outdir.mkdir()
    output_path = outdir / "x.md"
    output_path.write_text("existing-content", encoding="utf-8")

    ret = apply_fixes.main([str(md_path), str(fixes_path), "-o", str(outdir)])

    assert ret == 1
    assert output_path.read_text(encoding="utf-8") == "existing-content"


# --- 12: CLI サマリ形式 -------------------------------------------------------


def test_cli_summary_format(tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("alpha OLDVAL beta", encoding="utf-8")
    fixes_path = tmp_path / "x.json"
    _write_fixes(fixes_path, [{"id": "f1", "reason": "r", "old": "OLDVAL", "new": "NEWVAL"}])
    outdir = tmp_path / "out"

    ret = apply_fixes.main([str(md_path), str(fixes_path), "-o", str(outdir)])

    assert ret == 0
    captured = capsys.readouterr()
    lines = captured.out.strip("\n").split("\n")
    assert lines == ["x.md: 1 applied, 0 skipped", "total: 1 applied, 0 skipped"]
    assert (outdir / "x.md").read_text(encoding="utf-8") == "alpha NEWVAL beta"


# --- 13: CLI 不正 JSON --------------------------------------------------------


def test_cli_invalid_json(tmp_path: Path, capsys) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("alpha OLDVAL beta", encoding="utf-8")
    fixes_path = tmp_path / "x.json"
    fixes_path.write_text("{not valid json", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = apply_fixes.main([str(md_path), str(fixes_path), "-o", str(outdir)])

    assert ret == 1
    captured = capsys.readouterr()
    assert captured.err.strip() != ""
    assert not outdir.exists() or not (outdir / "x.md").exists()


# --- 14: テンプレート検証 -----------------------------------------------------


def test_template_json_is_valid() -> None:
    template_path = Path(__file__).parent.parent / "fixes" / "template.json"
    data = json.loads(template_path.read_text(encoding="utf-8"))

    errors = apply_fixes.validate_fixes(data, "template.json")

    assert errors == []


# --- 15: 最終不変条件: old ⊂ new ---------------------------------------------


def test_final_invariant_old_substring_of_new(tmp_path: Path) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("見よ CREATURE がいる。", encoding="utf-8")
    fixes_path = tmp_path / "x.json"
    _write_fixes(
        fixes_path,
        [{"id": "f1", "reason": "r", "old": "CREATURE", "new": "CREATURE-EXTRA"}],
    )
    outdir = tmp_path / "out"

    ret = apply_fixes.main([str(md_path), str(fixes_path), "-o", str(outdir)])

    assert ret == 1
    assert not (outdir / "x.md").exists()


# --- 16: 最終不変条件: fix 間干渉 ---------------------------------------------


def test_final_invariant_fix_interference(tmp_path: Path) -> None:
    md_path = tmp_path / "x.md"
    md_path.write_text("start ALPHA end", encoding="utf-8")
    fixes_path = tmp_path / "x.json"
    _write_fixes(
        fixes_path,
        [
            {"id": "f1", "reason": "r", "old": "ALPHA", "new": "BRAVO"},
            {"id": "f2", "reason": "r", "old": "BRAVO", "new": "CHARLIE"},
        ],
    )
    outdir = tmp_path / "out"

    ret = apply_fixes.main([str(md_path), str(fixes_path), "-o", str(outdir)])

    assert ret == 1
    assert not (outdir / "x.md").exists()
