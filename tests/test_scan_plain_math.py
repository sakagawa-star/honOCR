import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import scan_plain_math  # noqa: E402

TSV_HEADER = "chapter\tline\toffset\tkind\tlocation\tsymbol\tcontext"


def _write_md(tmp_path: Path, chapter: str, content: str) -> Path:
    """{tmp_path}/{chapter}/{chapter}_gray300.md に content を書き、パスを返す。"""
    d = tmp_path / chapter
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{chapter}_gray300.md"
    p.write_text(content, encoding="utf-8")
    return p


# T-01: is_japanese がひらがな・カタカナ・漢字・指定9約物に真、英数字・半角記号・ギリシャ文字に偽を返す
def test_is_japanese() -> None:
    for ch in ["あ", "ア", "漢", "、", "。", "，", "．", "・", "「", "」", "（", "）"]:
        assert scan_plain_math.is_japanese(ch) is True
    for ch in ["A", "1", "!", "α"]:
        assert scan_plain_math.is_japanese(ch) is False


# T-02: is_greek が θ・Ω に真、O（ラテン大文字オー）・о（キリル小文字）に偽を返す
def test_is_greek() -> None:
    assert scan_plain_math.is_greek("θ") is True
    assert scan_plain_math.is_greek("Ω") is True
    assert scan_plain_math.is_greek("O") is False
    assert scan_plain_math.is_greek("о") is False


# T-03: mask_regions の返すマスク文字列の長さが元と等しい
def test_mask_regions_length_preserved() -> None:
    md = "本文 $x$ と ```\ncode\n``` と $$\na=b\n$$ 終わり"
    masked, _ = scan_plain_math.mask_regions(md)
    assert len(masked) == len(md)


# T-04: 数式ブロック（$$ 対・複数行）の内側から候補が出ない
def test_math_block_excludes_candidates() -> None:
    md = "前文\n$$\nα と X の話\n$$\n後文"
    candidates = scan_plain_math.find_candidates(md)
    assert candidates == []


# T-05: コードブロック（フェンス対・複数行）の内側から候補が出ない
def test_code_block_excludes_candidates() -> None:
    md = "前文\n```\nΩ と X の話\n```\n後文"
    candidates = scan_plain_math.find_candidates(md)
    assert candidates == []


# T-06: コードブロックの中の行頭 $$ が数式ブロックと誤認されない（適用順の検証）
def test_code_fence_precedes_math_block() -> None:
    md = "```\nsome code\n$$\nΩ inside\n$$\nend\n```\n"
    masked, _ = scan_plain_math.mask_regions(md)
    fence_start = md.index("```")
    fence_end = md.rindex("```") + len("```")
    assert masked[fence_start:fence_end] == "\x00" * (fence_end - fence_start)
    assert scan_plain_math.find_candidates(md) == []


# T-07: 画像参照 ![](path) の内側から候補が出ない
def test_image_ref_excludes_candidates() -> None:
    md = "前文 ![Ω alt](path/to/img.png) 後文"
    candidates = scan_plain_math.find_candidates(md)
    assert candidates == []


# T-08: 改行をまたぐ $…$ をインライン数式と見なさない
def test_inline_math_does_not_cross_newline() -> None:
    md = "確率変数 $X\nY$ の値"
    candidates = scan_plain_math.find_candidates(md)
    assert all(kind != "C" for kind, _, _ in candidates)


# T-09: 候補L: 「確率変数 X の期待値」から X を1件拾い、offset が X の位置と一致する
def test_candidate_l_basic() -> None:
    md = "確率変数 X の期待値"
    offset = md.index("X")
    candidates = scan_plain_math.find_candidates(md)
    l_candidates = [c for c in candidates if c[0] == "L"]
    assert l_candidates == [("L", offset, "X")]


# T-10: 候補L: 連続英字（「Python で」）を拾わない
def test_candidate_l_rejects_consecutive_letters() -> None:
    md = "これは Python で書く"
    candidates = scan_plain_math.find_candidates(md)
    assert [c for c in candidates if c[0] == "L"] == []


# T-11: 候補L: 空白を2つ挟む場合（「変数␣␣X␣␣の」）を拾わない
def test_candidate_l_rejects_double_space() -> None:
    md = "変数  X  の話"
    candidates = scan_plain_math.find_candidates(md)
    assert [c for c in candidates if c[0] == "L"] == []


# T-12: 候補L: md の先頭・末尾の英字を拾わない
def test_candidate_l_rejects_at_boundaries() -> None:
    md_start = "Xの続き"
    md_end = "続きのX"
    assert [c for c in scan_plain_math.find_candidates(md_start) if c[0] == "L"] == []
    assert [c for c in scan_plain_math.find_candidates(md_end) if c[0] == "L"] == []


# T-13: 候補G: インライン数式の内側のギリシャ文字を拾わない
def test_candidate_g_excluded_inside_inline_math() -> None:
    md = "$θ$ のこと"
    candidates = scan_plain_math.find_candidates(md)
    assert [c for c in candidates if c[0] == "G"] == []


# T-14: 候補C: $a$ と $b$ が並ぶとき2件になり、各 offset が $ の位置と一致する
def test_candidate_c_two_inline_math() -> None:
    md = "$a$ $b$"
    candidates = scan_plain_math.find_candidates(md)
    c_candidates = sorted((c for c in candidates if c[0] == "C"), key=lambda c: c[1])
    assert c_candidates == [("C", 0, "$a$"), ("C", 4, "$b$")]


# T-15: classify_location が | 始まりを table、> 始まりを footnote、他を body と判定する
def test_classify_location() -> None:
    md = "| a |\n> b\nc\n"
    starts = scan_plain_math.line_starts(md)
    offset_table = md.index("a")
    offset_footnote = md.index("b")
    offset_body = md.index("c")
    assert scan_plain_math.classify_location(md, starts, offset_table) == "table"
    assert scan_plain_math.classify_location(md, starts, offset_footnote) == "footnote"
    assert scan_plain_math.classify_location(md, starts, offset_body) == "body"


# T-16: line が 1 始まりで、複数行 md の各行に正しく対応する
def test_line_number_one_indexed(tmp_path: Path) -> None:
    md = "1行目\n2行目\n変数 X の値\n4行目\n"
    path = _write_md(tmp_path, "chap00", md)
    rows = scan_plain_math.scan_md(path, {"G", "L", "C"})
    l_rows = [r for r in rows if r["kind"] == "L"]
    assert len(l_rows) == 1
    assert l_rows[0]["line"] == 3


# T-17: context のタブ・改行が半角スペースに置換され、TSV の列数が壊れない
def test_context_sanitized(tmp_path: Path) -> None:
    md = "これは短い文です\n変数 X の値\n続きの文章がここにあります\n"
    path = _write_md(tmp_path, "chap00", md)
    rows = scan_plain_math.scan_md(path, {"G", "L", "C"})
    l_rows = [r for r in rows if r["kind"] == "L"]
    assert len(l_rows) == 1
    context = l_rows[0]["context"]
    assert "\n" not in context
    assert "\t" not in context
    tsv = scan_plain_math._format_tsv(rows)
    lines = [line for line in tsv.splitlines() if line]
    for line in lines:
        assert len(line.split("\t")) == 7


# T-18: 出力の並び順が §3.2 のとおりである（入力ファイルの指定順を逆にしても同一）
def test_output_order_independent_of_input_order(tmp_path: Path, capsys) -> None:
    path_a = _write_md(tmp_path, "chapA", "変数 X の値\nギリシャ θ の話\n")
    path_b = _write_md(tmp_path, "chapB", "変数 Y の値\nギリシャ φ の話\n")

    ret1 = scan_plain_math.main([str(path_a), str(path_b)])
    assert ret1 == 0
    out1 = capsys.readouterr().out

    ret2 = scan_plain_math.main([str(path_b), str(path_a)])
    assert ret2 == 0
    out2 = capsys.readouterr().out

    assert out1 == out2


# T-19: 同じ入力に対する2回の実行がバイト同一である
def test_deterministic_output(tmp_path: Path) -> None:
    path = _write_md(tmp_path, "chap00", "変数 X の値\nギリシャ θ の話\n")
    out1 = tmp_path / "out1.tsv"
    out2 = tmp_path / "out2.tsv"

    ret1 = scan_plain_math.main([str(path), "-o", str(out1)])
    ret2 = scan_plain_math.main([str(path), "-o", str(out2)])

    assert ret1 == 0
    assert ret2 == 0
    assert out1.read_bytes() == out2.read_bytes()


# T-20: --kind G がギリシャ文字だけを出力する
def test_kind_filter_g(tmp_path: Path) -> None:
    path = _write_md(tmp_path, "chap00", "変数 X の値\nギリシャ θ の話\n$a$ の数式")
    out = tmp_path / "out.tsv"
    ret = scan_plain_math.main([str(path), "-o", str(out), "--kind", "G"])
    assert ret == 0
    lines = [line for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert lines[0] == TSV_HEADER
    data_lines = lines[1:]
    assert len(data_lines) >= 1
    for line in data_lines:
        cols = line.split("\t")
        assert cols[3] == "G"


# T-21: 入力ファイルが存在しないとき終了コード1・標準エラーにメッセージ
def test_input_not_found(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "does_not_exist.md"
    ret = scan_plain_math.main([str(missing)])
    assert ret == 1
    err = capsys.readouterr().err
    assert str(missing) in err


# T-22: --out が既存で --overwrite 無しのとき終了コード1・既存ファイルの内容が変わらない
def test_output_exists_without_overwrite(tmp_path: Path) -> None:
    path = _write_md(tmp_path, "chap00", "変数 X の値\n")
    out = tmp_path / "out.tsv"
    out.write_bytes(b"existing-content")

    ret = scan_plain_math.main([str(path), "-o", str(out)])
    assert ret == 1
    assert out.read_bytes() == b"existing-content"


# T-23: 候補0件のときヘッダ行のみ・終了コード0
def test_zero_candidates(tmp_path: Path, capsys) -> None:
    path = _write_md(tmp_path, "chap00", "これはただの日本語の文章です。\n")
    ret = scan_plain_math.main([str(path)])
    assert ret == 0
    out = capsys.readouterr().out
    assert out == TSV_HEADER + "\n"


# T-24: 空の md で終了コード0・ヘッダ行のみ
def test_empty_md(tmp_path: Path, capsys) -> None:
    path = _write_md(tmp_path, "chap00", "")
    ret = scan_plain_math.main([str(path)])
    assert ret == 0
    out = capsys.readouterr().out
    assert out == TSV_HEADER + "\n"
