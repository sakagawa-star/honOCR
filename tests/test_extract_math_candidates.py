import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import extract_math_candidates as emc  # noqa: E402


# T-01: mask_math が $$…$$（改行をまたぐものを含む）の中身をマスクする
def test_mask_math_block_multiline() -> None:
    md = "before $$a\nb$$ after"
    masked = emc.mask_math(md)
    start = md.index("$$")
    end = md.index("$$", start + 2) + 2
    assert masked[start:end] == emc.MASK_CHAR * (end - start)
    assert masked[:start] == md[:start]
    assert masked[end:] == md[end:]


# T-02: mask_math が $…$ の中身をマスクする
def test_mask_math_inline() -> None:
    md = "value $x$ end"
    masked = emc.mask_math(md)
    start = md.index("$")
    end = md.index("$", start + 1) + 1
    assert masked[start:end] == emc.MASK_CHAR * (end - start)
    assert masked[:start] == md[:start]
    assert masked[end:] == md[end:]


# T-03: $…$ が改行をまたがない（$ と $ の間に改行があるとき、その範囲をマスクしない）
def test_mask_math_inline_does_not_cross_newline() -> None:
    md = "a $Ω\nb$ c"
    masked = emc.mask_math(md)
    assert masked == md


# T-04: 出力の長さが入力と同じで、マスクされない位置の文字が入力の同じ位置の文字と一致する
def test_mask_math_preserves_length_and_positions() -> None:
    md = "α $$x$$ β $y$ γ"
    masked = emc.mask_math(md)
    assert len(masked) == len(md)
    for a, b in zip(md, masked):
        if b != emc.MASK_CHAR:
            assert a == b


# T-05: ギリシャ文字が真、ラテン文字・キリル文字・日本語が偽
def test_is_candidate_char_greek() -> None:
    assert emc.is_candidate_char("Ω") is True
    assert emc.is_candidate_char("ω") is True
    assert emc.is_candidate_char("θ") is True
    assert emc.is_candidate_char("O") is False
    assert emc.is_candidate_char("о") is False  # キリル文字の "o"
    assert emc.is_candidate_char("あ") is False


# T-06: MATH_SYMBOLS の全32文字が真
def test_is_candidate_char_math_symbols() -> None:
    assert len(emc.MATH_SYMBOLS) == 32
    for ch in emc.MATH_SYMBOLS:
        assert emc.is_candidate_char(ch) is True


# T-07: 対象外・保留の文字がすべて偽
def test_is_candidate_char_excluded() -> None:
    for ch in "…→×·":
        assert emc.is_candidate_char(ch) is False


# T-08: find_offsets が昇順で、候補が無ければ空リスト
def test_find_offsets_ascending_and_empty() -> None:
    assert emc.find_offsets("") == []
    assert emc.find_offsets("abc") == []
    masked = "aΩbθc"
    offsets = emc.find_offsets(masked)
    assert offsets == [1, 3]
    assert offsets == sorted(offsets)


# T-09: make_record が5キー揃い、char が md[offset] と一致する
def test_make_record_basic() -> None:
    md = "hello Ω world"
    offset = md.index("Ω")
    rec = emc.make_record(md, "chap01", offset)
    assert set(rec.keys()) == {"chapter", "offset", "char", "before", "after"}
    assert rec["chapter"] == "chap01"
    assert rec["offset"] == offset
    assert rec["char"] == md[offset]


# T-10: offset=0 で before が空、末尾で after が空、40文字未満で埋めない
def test_make_record_boundaries() -> None:
    md_start = "Ω" + "x" * 5
    rec_start = emc.make_record(md_start, "chap01", 0)
    assert rec_start["before"] == ""
    assert rec_start["after"] == "xxxxx"

    md_end = "y" * 5 + "θ"
    offset_end = len(md_end) - 1
    rec_end = emc.make_record(md_end, "chap01", offset_end)
    assert rec_end["after"] == ""
    assert rec_end["before"] == "yyyyy"


# T-11: 文脈をマスク前の原文から切り出す（文脈内の $…$ が原文のまま残る）
def test_make_record_context_from_original() -> None:
    md = "$a$ Ω $b$"
    offset = md.index("Ω")
    rec = emc.make_record(md, "chap01", offset)
    assert rec["before"] == "$a$ "
    assert rec["after"] == " $b$"


# T-12: 1行1レコードで json.loads できる。改行・タブ・引用符を含む文脈が書き出しと読み戻しで同一
def test_write_jsonl_roundtrip(tmp_path: Path) -> None:
    records: list[dict[str, object]] = [
        {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "a\tb\n\"c\"", "after": "d"},
        {"chapter": "chap01", "offset": 2, "char": "θ", "before": "x", "after": "y"},
    ]
    out = tmp_path / "out.jsonl"
    emc.write_jsonl(records, out, overwrite=False)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    loaded = [json.loads(line) for line in lines]
    assert loaded == records


# T-13: レコードが空のとき0バイトのファイルを作る
def test_write_jsonl_empty(tmp_path: Path) -> None:
    out = tmp_path / "empty.jsonl"
    emc.write_jsonl([], out, overwrite=False)
    assert out.exists()
    assert out.stat().st_size == 0


# T-14: 出力先が存在し overwrite が偽のとき、書き込まずに例外を送出する
def test_write_jsonl_refuses_overwrite(tmp_path: Path) -> None:
    out = tmp_path / "out.jsonl"
    out.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        emc.write_jsonl([{"a": 1}], out, overwrite=False)
    assert out.read_text(encoding="utf-8") == "existing"


# T-15: 親ディレクトリが無いとき作成する
def test_write_jsonl_creates_parent_dir(tmp_path: Path) -> None:
    out = tmp_path / "sub" / "dir" / "out.jsonl"
    emc.write_jsonl([{"a": 1}], out, overwrite=False)
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0]) == {"a": 1}


# T-16: 一時ディレクトリに chapXX/ を作って md を置き、複数ファイルを指定して実行し、
# 章名が親ディレクトリ名になり、順序が指定順・位置昇順になる
def test_main_cli_multiple_files_order(tmp_path: Path) -> None:
    chap1 = tmp_path / "chap01"
    chap1.mkdir()
    f1 = chap1 / "chap01_gray300.md"
    f1.write_text("θ text Ω", encoding="utf-8")

    chap2 = tmp_path / "chap02"
    chap2.mkdir()
    f2 = chap2 / "chap02_gray300.md"
    f2.write_text("α text β", encoding="utf-8")

    out = tmp_path / "out.jsonl"
    ret = emc.main([str(f1), str(f2), "-o", str(out)])
    assert ret == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]

    assert records[0]["chapter"] == "chap01"
    assert records[-1]["chapter"] == "chap02"

    chap1_records = [r for r in records if r["chapter"] == "chap01"]
    chap1_offsets = [r["offset"] for r in chap1_records]
    assert chap1_offsets == sorted(chap1_offsets)

    chap2_records = [r for r in records if r["chapter"] == "chap02"]
    chap2_offsets = [r["offset"] for r in chap2_records]
    assert chap2_offsets == sorted(chap2_offsets)


# T-17: 存在しない入力を混ぜると終了コード1で、出力ファイルが作られない
def test_main_cli_missing_input_no_output(tmp_path: Path) -> None:
    chap1 = tmp_path / "chap01"
    chap1.mkdir()
    f1 = chap1 / "chap01_gray300.md"
    f1.write_text("Ω", encoding="utf-8")

    missing = tmp_path / "chap02" / "missing.md"
    out = tmp_path / "out.jsonl"

    ret = emc.main([str(f1), str(missing), "-o", str(out)])
    assert ret == 1
    assert not out.exists()


# T-18: --overwrite の有無で上書きの可否が変わる
def test_main_cli_overwrite_flag(tmp_path: Path) -> None:
    chap1 = tmp_path / "chap01"
    chap1.mkdir()
    f1 = chap1 / "chap01_gray300.md"
    f1.write_text("Ω", encoding="utf-8")

    out = tmp_path / "out.jsonl"
    out.write_text("old", encoding="utf-8")

    ret = emc.main([str(f1), "-o", str(out)])
    assert ret == 1
    assert out.read_text(encoding="utf-8") == "old"

    ret2 = emc.main([str(f1), "-o", str(out), "--overwrite"])
    assert ret2 == 0
    assert out.read_text(encoding="utf-8") != "old"


# T-19: 同じ入力で2回実行した結果が完全に一致する
def test_determinism(tmp_path: Path) -> None:
    chap1 = tmp_path / "chap01"
    chap1.mkdir()
    f1 = chap1 / "chap01_gray300.md"
    f1.write_text("αβγ Ω $x$ θ ≤≥ text", encoding="utf-8")

    out1 = tmp_path / "out1.jsonl"
    out2 = tmp_path / "out2.jsonl"
    ret1 = emc.main([str(f1), "-o", str(out1)])
    ret2 = emc.main([str(f1), "-o", str(out2)])
    assert ret1 == 0
    assert ret2 == 0
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# T-20: 必須引数（入力ファイル、または -o）を欠いて実行すると SystemExit が送出され、
# その .code が 2 である
def test_main_cli_missing_required_args() -> None:
    with pytest.raises(SystemExit) as exc_info_no_args:
        emc.main([])
    assert exc_info_no_args.value.code == 2

    with pytest.raises(SystemExit) as exc_info_no_output:
        emc.main(["some.md"])
    assert exc_info_no_output.value.code == 2
