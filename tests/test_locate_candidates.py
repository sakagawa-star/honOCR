import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import locate_candidates as lc  # noqa: E402


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )


def _write_content_list(path: Path, blocks: list[dict]) -> None:
    path.write_text(json.dumps(blocks, ensure_ascii=False), encoding="utf-8")


def _setup_chapter(final_dir: Path, chapter: str, blocks: list[dict]) -> Path:
    chap_dir = final_dir / chapter
    chap_dir.mkdir(parents=True, exist_ok=True)
    cl = chap_dir / f"{chapter}_gray300_content_list.json"
    _write_content_list(cl, blocks)
    return cl


# T-101: resolve_content_list が一時ディレクトリに置いた1個の content_list を解決できる
def test_resolve_content_list_single_match(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    chap_dir = final_dir / "chap01"
    chap_dir.mkdir(parents=True)
    cl = chap_dir / "chap01_gray300_content_list.json"
    cl.write_text("[]", encoding="utf-8")

    result = lc.resolve_content_list(final_dir, "chap01")
    assert result == cl


# T-102: 0個・2個以上のとき例外を送出する（章のディレクトリが無い場合も含む）
def test_resolve_content_list_zero_or_multiple(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    chap_dir = final_dir / "chap01"
    chap_dir.mkdir(parents=True)

    # 章のディレクトリはあるが content_list が無い（0個）
    with pytest.raises(Exception):
        lc.resolve_content_list(final_dir, "chap01")

    # 章のディレクトリ自体が存在しない
    with pytest.raises(Exception):
        lc.resolve_content_list(final_dir, "chap02")

    # content_list が2個以上
    (chap_dir / "a_content_list.json").write_text("[]", encoding="utf-8")
    (chap_dir / "b_content_list.json").write_text("[]", encoding="utf-8")
    with pytest.raises(Exception):
        lc.resolve_content_list(final_dir, "chap01")


# T-103: text のみ、table_body を持つ、キャプションの list を持つブロックで、
# SEARCH_KEYS の順に \n 連結される
def test_block_search_text_multiple_keys() -> None:
    block = {
        "text": "abc",
        "table_body": "<table>x</table>",
        "image_caption": ["cap1", "cap2"],
        "chart_footnote": ["foot"],
    }
    result = lc.block_search_text(block)
    assert result == "abc\n<table>x</table>\ncap1\ncap2\nfoot"


# T-104: 該当キーを1つも持たないブロックで空文字列を返す。list 内の非 str 要素を飛ばす
def test_block_search_text_empty_and_skips_non_str() -> None:
    assert lc.block_search_text({"type": "page_number"}) == ""

    block = {"image_caption": ["ok", 123, None, "also-ok"]}
    assert lc.block_search_text(block) == "ok\nalso-ok"


# T-105: K = 40・20・10・5 でキーの長さと内容が正しい。before が K 未満のとき、あるだけを使う
def test_build_key_various_lengths() -> None:
    record = {"before": "abcdefghij", "char": "X", "after": "0123456789ABCDE"}
    assert lc.build_key(record, 5) == "fghijX01234"
    assert lc.build_key(record, 10) == "abcdefghijX0123456789"
    assert lc.build_key(record, 40) == "abcdefghijX0123456789ABCDE"
    assert lc.build_key(record, 3) == "hijX012"


# T-134: before の最後の改行より後・after の最初の改行より前だけを使う
# （切り詰め後のキーに改行が含まれない）
def test_build_key_truncates_at_newlines() -> None:
    record = {"before": "あい\n\nうえ", "char": "X", "after": "かき\nくけ"}
    result = lc.build_key(record, 40)
    assert result == "うえXかき"
    assert "\n" not in result


# T-135: before/after に改行が無いとき切り詰めが起きない。切り詰めの結果が
# 空文字列になるとき、キーが char の1文字になる
def test_build_key_no_newline_and_empty_after_truncation() -> None:
    record_no_newline = {"before": "abcdefghij", "char": "X", "after": "0123456789"}
    assert lc.build_key(record_no_newline, 40) == "abcdefghijX0123456789"

    record_empty_context = {"before": "abc\n", "char": "X", "after": "\ndef"}
    assert lc.build_key(record_empty_context, 40) == "X"


# T-106: K=40 で一意に定まるとき、その K とブロック番号・page_idx を返す
def test_locate_block_unique_at_k40() -> None:
    record = {"before": "x" * 40, "char": "Ω", "after": "y" * 40}
    key40 = lc.build_key(record, 40)
    blocks = [
        {"text": "unrelated", "page_idx": 0},
        {"text": f"prefix {key40} suffix", "page_idx": 5},
    ]
    result = lc.locate_block(record, blocks)
    assert result == (1, 5, 40)


# T-107: K=40 で0件、K=20 で一意のとき、K=20 で採用する（階梯が降りる）
def test_locate_block_falls_back_to_shorter_k() -> None:
    record = {"before": "x" * 40, "char": "Ω", "after": "y" * 40}
    key20 = lc.build_key(record, 20)
    blocks = [
        {"text": "no match at all", "page_idx": 0},
        {"text": f"has {key20} inside", "page_idx": 7},
    ]
    result = lc.locate_block(record, blocks)
    assert result == (1, 7, 20)


# T-108: ある K で2件以上のとき、より短い K に進まず逆引き失敗を返す
def test_locate_block_two_matches_fails_without_trying_shorter_k() -> None:
    record = {"before": "x" * 40, "char": "Ω", "after": "y" * 40}
    key40 = lc.build_key(record, 40)
    blocks = [
        {"text": f"first {key40} here", "page_idx": 0},
        {"text": f"second {key40} here", "page_idx": 1},
    ]
    result = lc.locate_block(record, blocks)
    assert result == (None, None, None)


# T-109: すべての K で0件のとき逆引き失敗を返す
def test_locate_block_all_k_fail() -> None:
    record = {"before": "abc", "char": "Ω", "after": "def"}
    blocks = [{"text": "completely unrelated text", "page_idx": 0}]
    result = lc.locate_block(record, blocks)
    assert result == (None, None, None)


# T-110: 採用ブロックの page_idx が int でないとき逆引き失敗を返す
def test_locate_block_bad_page_idx_fails() -> None:
    record = {"before": "x" * 40, "char": "Ω", "after": "y" * 40}
    key40 = lc.build_key(record, 40)

    blocks_str = [{"text": f"has {key40} here", "page_idx": "not-an-int"}]
    assert lc.locate_block(record, blocks_str) == (None, None, None)

    blocks_bool = [{"text": f"has {key40} here", "page_idx": True}]
    assert lc.locate_block(record, blocks_bool) == (None, None, None)

    blocks_missing = [{"text": f"has {key40} here"}]
    assert lc.locate_block(record, blocks_missing) == (None, None, None)


# T-111: 同一ブロック内にキーが2回現れるとき、一意として扱う
def test_locate_block_repeated_key_in_same_block_is_unique() -> None:
    record = {"before": "x" * 40, "char": "Ω", "after": "y" * 40}
    key40 = lc.build_key(record, 40)
    blocks = [{"text": f"{key40} ... {key40}", "page_idx": 3}]
    result = lc.locate_block(record, blocks)
    assert result == (0, 3, 40)


# T-112: キーが7個ちょうどで、RESULT_KEYS と一致する。ブロック番号・k を含まない
def test_make_result_keys() -> None:
    record = {"chapter": "chap01", "offset": 5, "char": "Ω", "before": "a", "after": "b"}
    result = lc.make_result(record, 3, "missing")
    assert list(result.keys()) == list(lc.RESULT_KEYS)
    assert len(result) == 7
    assert "block_idx" not in result
    assert "k" not in result


# T-113: page_idx = None・judgment = None が null として JSON に出る
def test_make_result_none_values_become_null() -> None:
    record = {"chapter": "chap01", "offset": 5, "char": "Ω", "before": "a", "after": "b"}
    result = lc.make_result(record, None, None)
    loaded = json.loads(json.dumps(result))
    assert loaded["page_idx"] is None
    assert loaded["judgment"] is None


# T-114: 1行1レコードで読み戻せる。改行・引用符を含む文脈が往復で同一
def test_write_jsonl_roundtrip(tmp_path: Path) -> None:
    records = [
        {
            "chapter": "chap01",
            "offset": 1,
            "char": "Ω",
            "before": "a\tb\n\"c\"",
            "after": "d",
            "page_idx": 3,
            "judgment": "missing",
        },
        {
            "chapter": "chap01",
            "offset": 2,
            "char": "θ",
            "before": "x",
            "after": "y",
            "page_idx": None,
            "judgment": None,
        },
    ]
    out = tmp_path / "out.jsonl"
    lc.write_jsonl(records, out, overwrite=False)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    loaded = [json.loads(line) for line in lines]
    assert loaded == records


# T-115: 出力先が存在し overwrite が偽のとき書き込まずに例外を送出する。親ディレクトリを作る
def test_write_jsonl_refuses_overwrite_and_creates_parent(tmp_path: Path) -> None:
    out = tmp_path / "out.jsonl"
    out.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        lc.write_jsonl([], out, overwrite=False)
    assert out.read_text(encoding="utf-8") == "existing"

    nested_out = tmp_path / "sub" / "dir" / "out.jsonl"
    lc.write_jsonl([{"a": 1}], nested_out, overwrite=False)
    assert nested_out.exists()
    assert json.loads(nested_out.read_text(encoding="utf-8").splitlines()[0]) == {"a": 1}


# T-116: --select で1件だけを処理し、標準出力に内訳の1行が出る
def test_main_select_processes_one(tmp_path: Path, capsys) -> None:
    final_dir = tmp_path / "final"
    record = {
        "chapter": "chap01",
        "offset": 10,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    key40 = lc.build_key(record, 40)
    _setup_chapter(final_dir, "chap01", [{"text": f"has {key40} here", "page_idx": 2}])

    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])

    out = tmp_path / "out.jsonl"
    ret = lc.main(
        [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "1"]
    )
    assert ret == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["page_idx"] == 2

    stdout_lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert len(stdout_lines) == 1


# T-117: --select を省略すると全件を処理する
def test_main_full_processing_without_select(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record1 = {
        "chapter": "chap01",
        "offset": 10,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    record2 = {
        "chapter": "chap01",
        "offset": 20,
        "char": "θ",
        "before": "a" * 40,
        "after": "b" * 40,
    }
    key1 = lc.build_key(record1, 40)
    key2 = lc.build_key(record2, 40)
    _setup_chapter(
        final_dir,
        "chap01",
        [
            {"text": f"has {key1} here", "page_idx": 0},
            {"text": f"has {key2} here", "page_idx": 1},
        ],
    )

    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record1, record2])

    out = tmp_path / "out.jsonl"
    ret = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


# T-118: --judgment の値が集合外のとき SystemExit の .code が 2
def test_main_judgment_invalid_choice() -> None:
    with pytest.raises(SystemExit) as exc_info:
        lc.main(
            [
                "candidates.jsonl",
                "--final-dir",
                "final",
                "-o",
                "out.jsonl",
                "--select",
                "1",
                "--judgment",
                "bogus",
            ]
        )
    assert exc_info.value.code == 2


# T-119: --judgment を --select なしで指定したとき .code が 2
def test_main_judgment_without_select(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text("", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        lc.main(
            [
                str(candidates),
                "--final-dir",
                str(final_dir),
                "-o",
                str(out),
                "--judgment",
                "missing",
            ]
        )
    assert exc_info.value.code == 2


# T-120: --select が範囲外（0以下、総行数超過）のとき .code が 2
def test_main_select_out_of_range(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}
    _setup_chapter(final_dir, "chap01", [{"text": "x", "page_idx": 0}])
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])
    out = tmp_path / "out.jsonl"

    with pytest.raises(SystemExit) as exc_info_zero:
        lc.main(
            [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "0"]
        )
    assert exc_info_zero.value.code == 2

    with pytest.raises(SystemExit) as exc_info_over:
        lc.main(
            [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "5"]
        )
    assert exc_info_over.value.code == 2


# T-121: 逆引き失敗の候補に --judgment missing を指定したとき .code が 2
def test_main_judgment_on_failed_locate_rejected(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}
    _setup_chapter(final_dir, "chap01", [{"text": "totally unrelated", "page_idx": 0}])
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])
    out = tmp_path / "out.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        lc.main(
            [
                str(candidates),
                "--final-dir",
                str(final_dir),
                "-o",
                str(out),
                "--select",
                "1",
                "--judgment",
                "missing",
            ]
        )
    assert exc_info.value.code == 2


# T-122: 逆引き失敗でも終了コード0で終わり、page_idx が null のレコードが出る
def test_main_locate_failure_exit_zero(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}
    _setup_chapter(final_dir, "chap01", [{"text": "totally unrelated", "page_idx": 0}])
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])
    out = tmp_path / "out.jsonl"

    ret = lc.main(
        [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "1"]
    )
    assert ret == 0
    result = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert result["page_idx"] is None
    assert result["judgment"] is None


# T-123: 入力・--final-dir が存在しないとき終了コード1
def test_main_missing_input_or_final_dir(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    missing_candidates = tmp_path / "missing.jsonl"
    out = tmp_path / "out.jsonl"
    ret = lc.main([str(missing_candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 1

    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text("", encoding="utf-8")
    missing_final = tmp_path / "no_such_final"
    ret2 = lc.main([str(candidates), "--final-dir", str(missing_final), "-o", str(out)])
    assert ret2 == 1


# T-124: 同じ入力で2回実行した結果が完全に一致する
def test_determinism(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record = {
        "chapter": "chap01",
        "offset": 1,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    key40 = lc.build_key(record, 40)
    _setup_chapter(final_dir, "chap01", [{"text": f"has {key40} here", "page_idx": 2}])
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])

    out1 = tmp_path / "out1.jsonl"
    out2 = tmp_path / "out2.jsonl"
    ret1 = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out1)])
    ret2 = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out2)])
    assert ret1 == 0
    assert ret2 == 0
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# T-125: 空行を飛ばし、件数に数えない。並び順が入力ファイルのままである
def test_read_candidates_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "candidates.jsonl"
    rec1 = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}
    rec2 = {"chapter": "chap01", "offset": 2, "char": "θ", "before": "", "after": ""}
    path.write_text(
        json.dumps(rec1) + "\n" + "\n" + json.dumps(rec2) + "\n",
        encoding="utf-8",
    )
    result = lc.read_candidates(path)
    assert [r for _, r in result] == [rec1, rec2]
    assert [n for n, _ in result] == [1, 3]


# T-126: JSONとして読めない行・dictでない行・キーが過不足する行・型や値域が合わない行で例外を送出する
def test_read_candidates_invalid_rows(tmp_path: Path) -> None:
    base = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}

    missing_after = {k: v for k, v in base.items() if k != "after"}

    cases = [
        "not json{",
        json.dumps([1, 2, 3]),
        json.dumps({**base, "extra": 1}),
        json.dumps(missing_after),
        json.dumps({**base, "offset": -1}),
        json.dumps({**base, "char": "ab"}),
        json.dumps({**base, "chapter": ""}),
    ]
    for bad_line in cases:
        path = tmp_path / "candidates.jsonl"
        path.write_text(bad_line + "\n", encoding="utf-8")
        with pytest.raises(Exception):
            lc.read_candidates(path)


# T-127: 不正な行を含む候補ファイルを与えると、行番号を含むメッセージが標準エラーに出て
# 終了コード1で終わり、出力ファイルが作られない
def test_main_invalid_row_no_output(tmp_path: Path, capsys) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text("not json{\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    ret = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 1
    assert not out.exists()
    err = capsys.readouterr().err
    assert "1" in err


# T-128: 2つの章のレコードが交互に並ぶ入力で、全件が入力順のまま出力され、
# 標準出力の内訳も同じ順に並ぶ
def test_main_full_processing_preserves_order_across_chapters(tmp_path: Path, capsys) -> None:
    final_dir = tmp_path / "final"
    rec_a1 = {
        "chapter": "chapA",
        "offset": 1,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    rec_b1 = {
        "chapter": "chapB",
        "offset": 1,
        "char": "θ",
        "before": "p" * 40,
        "after": "q" * 40,
    }
    rec_a2 = {
        "chapter": "chapA",
        "offset": 2,
        "char": "α",
        "before": "m" * 40,
        "after": "n" * 40,
    }

    key_a1 = lc.build_key(rec_a1, 40)
    key_b1 = lc.build_key(rec_b1, 40)
    key_a2 = lc.build_key(rec_a2, 40)

    _setup_chapter(
        final_dir,
        "chapA",
        [
            {"text": key_a1, "page_idx": 0},
            {"text": key_a2, "page_idx": 1},
        ],
    )
    _setup_chapter(final_dir, "chapB", [{"text": key_b1, "page_idx": 0}])

    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [rec_a1, rec_b1, rec_a2])

    out = tmp_path / "out.jsonl"
    ret = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    results = [json.loads(line) for line in lines]
    assert [(r["chapter"], r["offset"]) for r in results] == [
        ("chapA", 1),
        ("chapB", 1),
        ("chapA", 2),
    ]

    stdout_lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert len(stdout_lines) == 3
    assert stdout_lines[0].startswith("1 chapA")
    assert stdout_lines[1].startswith("2 chapB")
    assert stdout_lines[2].startswith("3 chapA")


# T-129: 途中のレコードの章の content_list が解決できないとき、終了コード1で終わり、
# 出力ファイルが作られない（部分的な結果を残さない）
def test_main_full_processing_content_list_failure_mid_run(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    rec_ok = {
        "chapter": "chapA",
        "offset": 1,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    rec_bad = {
        "chapter": "chapMissing",
        "offset": 1,
        "char": "θ",
        "before": "p" * 40,
        "after": "q" * 40,
    }
    key_ok = lc.build_key(rec_ok, 40)
    _setup_chapter(final_dir, "chapA", [{"text": key_ok, "page_idx": 0}])
    # chapMissing のディレクトリは final_dir の下に存在しない

    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [rec_ok, rec_bad])

    out = tmp_path / "out.jsonl"
    ret = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 1
    assert not out.exists()


# T-130: 逆引きに失敗する候補を含めても終了コード0で終わり、その候補が page_idx=null
# のレコードとして出力に含まれる
def test_main_full_processing_includes_locate_failures(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    rec_ok = {
        "chapter": "chapA",
        "offset": 1,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    rec_fail = {"chapter": "chapA", "offset": 2, "char": "θ", "before": "", "after": ""}
    key_ok = lc.build_key(rec_ok, 40)
    _setup_chapter(final_dir, "chapA", [{"text": key_ok, "page_idx": 0}])

    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [rec_ok, rec_fail])

    out = tmp_path / "out.jsonl"
    ret = lc.main([str(candidates), "--final-dir", str(final_dir), "-o", str(out)])
    assert ret == 0
    results = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert results[0]["page_idx"] == 0
    assert results[1]["page_idx"] is None


# T-131: 空行を含む候補ファイルで、--select が物理行番号として働く
# （空行の次の行を指定するとその候補が処理される）
def test_main_select_uses_physical_line_number(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    rec1 = {
        "chapter": "chapA",
        "offset": 1,
        "char": "Ω",
        "before": "x" * 40,
        "after": "y" * 40,
    }
    rec2 = {
        "chapter": "chapA",
        "offset": 2,
        "char": "θ",
        "before": "p" * 40,
        "after": "q" * 40,
    }
    key1 = lc.build_key(rec1, 40)
    key2 = lc.build_key(rec2, 40)
    _setup_chapter(
        final_dir,
        "chapA",
        [
            {"text": key1, "page_idx": 0},
            {"text": key2, "page_idx": 1},
        ],
    )

    candidates = tmp_path / "candidates.jsonl"
    # 行1=rec1, 行2=空行, 行3=rec2
    candidates.write_text(
        json.dumps(rec1) + "\n" + "\n" + json.dumps(rec2) + "\n", encoding="utf-8"
    )

    out = tmp_path / "out.jsonl"
    ret = lc.main(
        [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "3"]
    )
    assert ret == 0
    result = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert result["offset"] == 2
    assert result["page_idx"] == 1


# T-132: --select に空行の行番号、または存在しない行番号を与えると SystemExit の .code が 2
def test_main_select_blank_line_number_rejected(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir()
    rec1 = {"chapter": "chapA", "offset": 1, "char": "Ω", "before": "", "after": ""}
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(json.dumps(rec1) + "\n" + "\n", encoding="utf-8")
    out = tmp_path / "out.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        lc.main(
            [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "2"]
        )
    assert exc_info.value.code == 2

    with pytest.raises(SystemExit) as exc_info2:
        lc.main(
            [str(candidates), "--final-dir", str(final_dir), "-o", str(out), "--select", "99"]
        )
    assert exc_info2.value.code == 2


# T-133: 逆引きに失敗する候補に --judgment undecidable を与えると終了コード0で終わり、
# page_idx=null・judgment=undecidable のレコードが1件出る
def test_main_judgment_undecidable_on_failed_locate(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    record = {"chapter": "chap01", "offset": 1, "char": "Ω", "before": "", "after": ""}
    _setup_chapter(final_dir, "chap01", [{"text": "totally unrelated", "page_idx": 0}])
    candidates = tmp_path / "candidates.jsonl"
    _write_jsonl(candidates, [record])
    out = tmp_path / "out.jsonl"

    ret = lc.main(
        [
            str(candidates),
            "--final-dir",
            str(final_dir),
            "-o",
            str(out),
            "--select",
            "1",
            "--judgment",
            "undecidable",
        ]
    )
    assert ret == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["page_idx"] is None
    assert result["judgment"] == "undecidable"
