"""feat-025 M3 閾値実験の実験コード: 標本の抽出・照合・切り出し。

仕様は同じフォルダの criteria.md（§2.2・§2.3・§2.4・§3.5・§3.6）。
標準ライブラリのみを使う。サブコマンド: population / sample / locate、および --selftest。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

CHAPTERS = [f"chap{n:02d}" for n in range(10)]
INLINE_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]*?\$", re.DOTALL)

SEED = 20261006
N_DRAW = 24
GROUP_ORDER = ["SUP", "SUB", "G1", "G2", "G3"]
GROUP_NUMBER = {"SUP": 1, "SUB": 2, "G1": 3, "G2": 4, "G3": 5}

G1_WORDS = {
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi",
    "Omega", "le", "leq", "ge", "geq", "in", "notin", "subset", "subseteq", "supset",
    "supseteq", "forall", "exists", "partial", "nabla", "emptyset", "varnothing",
}
G2_WORDS = {
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta", "theta",
    "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi", "varpi", "rho",
    "varrho", "sigma", "varsigma", "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega",
}
G3_WORDS = {"sum", "prod", "int"}
# 添字の先頭として数える「ギリシャ文字の制御語」: G1 のうち大文字のギリシャ文字と G2 の全部
GREEK_UPPER_WORDS = {
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
}
GREEK_WORDS = GREEK_UPPER_WORDS | G2_WORDS

SEARCH_KEYS = (
    "text", "table_body", "image_caption", "image_footnote",
    "table_caption", "table_footnote", "chart_caption", "chart_footnote",
)


class OpError(Exception):
    """運用エラー（終了コード 1）。"""


# ---------------------------------------------------------------- population


def tokenize(inner: str) -> list[tuple[str, str, int]]:
    """(種類, 文字列, inner 内の開始位置) の列を返す。種類: cw / cs / open / close / char。"""
    tokens: list[tuple[str, str, int]] = []
    i = 0
    n = len(inner)
    while i < n:
        c = inner[i]
        if c.isspace():
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            if re.match(r"[A-Za-z]", inner[i + 1]):
                j = i + 1
                while j < n and re.match(r"[A-Za-z]", inner[j]):
                    j += 1
                tokens.append(("cw", inner[i:j], i))
                i = j
            else:
                tokens.append(("cs", inner[i:i + 2], i))
                i += 2
            continue
        if c == "{":
            tokens.append(("open", c, i))
        elif c == "}":
            tokens.append(("close", c, i))
        else:
            tokens.append(("char", c, i))
        i += 1
    return tokens


def classify_tokens(inner: str) -> list[tuple[str, int, str]]:
    """インライン数式の中身から (群, inner 内の位置, token) の列を返す（位置の昇順）。"""
    tokens = tokenize(inner)
    n = len(tokens)
    in_range = [False] * n
    firsts: list[tuple[str, int]] = []  # (SUP/SUB, 添字の先頭のトークン番号)
    for i, (kind, text, _pos) in enumerate(tokens):
        if kind != "char" or text not in ("^", "_"):
            continue
        j = i + 1
        if j >= n:
            continue
        if tokens[j][0] == "open":
            depth = 0
            close = -1
            for k in range(j, n):
                if tokens[k][0] == "open":
                    depth += 1
                elif tokens[k][0] == "close":
                    depth -= 1
                    if depth == 0:
                        close = k
                        break
            if close < 0:
                continue
            for k in range(j + 1, close):
                in_range[k] = True
            if j + 1 < close:
                firsts.append(("SUP" if text == "^" else "SUB", j + 1))
        else:
            in_range[j] = True
            firsts.append(("SUP" if text == "^" else "SUB", j))
    out: list[tuple[str, int, str]] = []
    for group, idx in firsts:
        kind, text, pos = tokens[idx]
        if kind == "char" and re.fullmatch(r"[A-Za-z0-9]", text):
            out.append((group, pos, text))
        elif kind == "cw" and text[1:] in GREEK_WORDS:
            out.append((group, pos, text))
    for i, (kind, text, pos) in enumerate(tokens):
        if in_range[i] or kind != "cw":
            continue
        word = text[1:]
        if word in G1_WORDS:
            out.append(("G1", pos, text))
        elif word in G2_WORDS:
            out.append(("G2", pos, text))
        elif word in G3_WORDS:
            out.append(("G3", pos, text))
    out.sort(key=lambda t: t[1])
    return out


def extract_rows(chapter: str, md: str) -> list[dict[str, Any]]:
    """1 章分の md から population の行を返す。"""
    rows: list[dict[str, Any]] = []
    for m in INLINE_RE.finditer(md):
        math_text = m.group(0)
        if math_text.startswith("$$"):
            continue
        start = m.start()
        end = m.end()
        line_start = md.rfind("\n", 0, start) + 1
        line_end = md.find("\n", end)
        if line_end < 0:
            line_end = len(md)
        before = md[max(line_start, start - 10):start]
        after = md[end:min(line_end, end + 10)]
        for group, pos, token in classify_tokens(math_text[1:-1]):
            rows.append({
                "group": group,
                "chapter": chapter,
                "math_start": start,
                "math_text": math_text,
                "token_pos": pos + 1,
                "token": token,
                "before": before,
                "after": after,
            })
    rows.sort(key=lambda r: (r["math_start"], r["token_pos"]))
    return rows


def find_single(directory: Path, pattern: str) -> Path:
    found = sorted(glob.glob(str(directory / pattern)))
    if len(found) != 1:
        raise OpError(f"{directory} の {pattern} が {len(found)} 個（ちょうど 1 個が必要）")
    return Path(found[0])


def ensure_parent(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OpError(f"出力先の親ディレクトリを作れない: {path.parent}: {e}") from e


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """出力と同じディレクトリの一時ファイルに書き切り、os.replace で置き換える（失敗したら一時ファイルを削除）。"""
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except OSError as e:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            raise OpError(f"書き込みに失敗: {e}。後片付けに失敗。残ったパス: {tmp}") from e
        raise


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OpError(f"入力が無い: {path}")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cmd_population(args: argparse.Namespace) -> int:
    out = Path(args.o)
    final_dir = Path(args.final_dir)
    if out.exists():
        raise OpError(f"出力先が既にある: {out}")
    rows: list[dict[str, Any]] = []
    for chapter in CHAPTERS:
        md_path = find_single(final_dir / chapter, "*.md")
        md = md_path.read_text(encoding="utf-8")
        rows.extend(extract_rows(chapter, md))
    ensure_parent(out)
    write_jsonl(out, rows)
    return 0


# -------------------------------------------------------------------- sample


def draw_samples(population: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for group in GROUP_ORDER:
        seq = [r for r in population if r["group"] == group]
        picked = random.Random(SEED + GROUP_NUMBER[group]).sample(
            list(range(len(seq))), min(N_DRAW, len(seq))
        )
        picked.sort()
        for k, idx in enumerate(picked, start=1):
            row = dict(seq[idx])
            row["sample_id"] = f"{group}-{k:02d}"
            out.append(row)
    return out


def cmd_sample(args: argparse.Namespace) -> int:
    out = Path(args.o)
    if out.exists():
        raise OpError(f"出力先が既にある: {out}")
    population = read_jsonl(Path(args.population))
    samples = draw_samples(population)
    ensure_parent(out)
    write_jsonl(out, samples)
    return 0


# -------------------------------------------------------------------- locate


def block_search_text(block: dict[str, Any]) -> str:
    """M2-1 design §1.4.3 の検索対象テキスト。"""
    parts: list[str] = []
    for key in SEARCH_KEYS:
        v = block.get(key)
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(x for x in v if isinstance(x, str))
    return "\n".join(parts)


def match_blocks(key: str, texts: list[str]) -> list[int]:
    return [i for i, t in enumerate(texts) if key in t]


def cmd_locate(args: argparse.Namespace) -> int:
    out = Path(args.o)
    crops_dir = Path(args.crops_dir)
    if out.exists() or crops_dir.exists():
        raise OpError("出力先（-o または --crops-dir）が既に存在する")
    samples = read_jsonl(Path(args.samples))
    final_dir = Path(args.final_dir)
    tif_root = Path(args.tif_root)

    cl_paths: dict[str, Path] = {}
    cl_texts: dict[str, list[str]] = {}
    cl_blocks: dict[str, list[Any]] = {}
    results: list[dict[str, Any]] = []
    for s in samples:
        ch = s["chapter"]
        if ch not in cl_paths:
            cl_paths[ch] = find_single(final_dir / ch, "*_content_list.json")
            blocks = json.loads(cl_paths[ch].read_text(encoding="utf-8"))
            cl_blocks[ch] = blocks
            cl_texts[ch] = [block_search_text(b) if isinstance(b, dict) else "" for b in blocks]
        key = s["before"] + s["math_text"] + s["after"]
        hits = match_blocks(key, cl_texts[ch])
        r = dict(s)
        r.update({"locate_status": "特定不能", "block_idx": None, "page_idx": None, "png": None})
        if len(hits) == 1:
            page_idx = cl_blocks[ch][hits[0]].get("page_idx")
            if isinstance(page_idx, int) and not isinstance(page_idx, bool):
                r["locate_status"] = "ok"
                r["block_idx"] = hits[0]
                r["page_idx"] = page_idx
        results.append(r)

    repo_root = Path(__file__).resolve().parents[6]
    crop_script = repo_root / "scripts" / "crop_blocks.py"
    ensure_parent(out)
    parent = crops_dir.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OpError(f"書き込み先のディレクトリを作れない: {parent}（{e}）") from e
    tmp_dir = Path(tempfile.mkdtemp(dir=parent, prefix=".crops-"))

    pairs: list[tuple[str, int]] = []
    for r in results:
        if r["locate_status"] == "ok" and (r["chapter"], r["block_idx"]) not in pairs:
            pairs.append((r["chapter"], r["block_idx"]))
    def cleanup(paths: list[Path]) -> None:
        left: list[str] = []
        for p in paths:
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
            except OSError:
                left.append(str(p))
        if left:
            sys.stderr.write("後片付けに失敗。残ったパス: " + " ".join(left) + "\n")

    for ch, bidx in pairs:
        cmd = [
            sys.executable, str(crop_script), str(cl_paths[ch]), str(tif_root / ch / "out"),
            "-o", str(tmp_dir), "--index", str(bidx),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            cleanup([tmp_dir])
            raise OpError(f"crop_blocks.py の起動に失敗（{ch} ブロック {bidx}）: {e}")
        if proc.returncode != 0:
            cleanup([tmp_dir])
            sys.stderr.write(proc.stdout + proc.stderr)
            raise OpError(f"crop_blocks.py が失敗した（{ch} ブロック {bidx}）")

    for r in results:
        if r["locate_status"] == "ok":
            stem = cl_paths[r["chapter"]].stem
            r["png"] = str(crops_dir / f"{stem}_b{r['block_idx']}_p{r['page_idx']}.png")

    # 段 a
    tmp_file: Path | None = None
    try:
        fd, tmp_file_name = tempfile.mkstemp(dir=out.parent, prefix=".located-")
        tmp_file = Path(tmp_file_name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        cleanup([tmp_dir] if tmp_file is None else [tmp_file, tmp_dir])
        raise OpError(f"located.jsonl の書き込みに失敗: {e}")
    # 段 b
    try:
        os.rename(tmp_dir, crops_dir)
    except OSError as e:
        cleanup([tmp_file, tmp_dir])
        raise OpError(f"crops ディレクトリの改名に失敗: {e}")
    # 段 c
    try:
        os.replace(tmp_file, out)
    except OSError as e:
        cleanup([tmp_file, crops_dir])
        raise OpError(f"located.jsonl の置き換えに失敗: {e}")
    return 0


# ------------------------------------------------------------------ selftest


def selftest() -> int:
    errors: list[str] = []

    def check(name: str, got: Any, want: Any) -> None:
        if got != want:
            errors.append(f"{name}: 期待 {want!r} / 実際 {got!r}")

    def summary(rows: list[dict[str, Any]]) -> list[tuple[str, int, str]]:
        return [(r["group"], r["token_pos"], r["token"]) for r in rows]

    # E1
    rows = extract_rows("chapXX", "前文$\\mu_{i}^{2} + \\sum x$後文")
    check("E1", summary(rows), [("G2", 1, "\\mu"), ("SUB", 6, "i"), ("SUP", 10, "2"), ("G3", 15, "\\sum")])
    check("E1 before/after", [(r["before"], r["after"]) for r in rows], [("前文", "後文")] * 4)
    # E2
    check("E2", summary(extract_rows("chapXX", "$x^\\alpha$")), [("SUP", 3, "\\alpha")])
    # E3
    check("E3", summary(extract_rows("chapXX", "$$\\Omega$$")), [])
    # E4
    check("E4", summary(extract_rows("chapXX", "$a^$")), [])
    # E5
    check("E5", summary(extract_rows("chapXX", "$x_{\\mathrm{d}}$")), [])

    # E6
    pop: list[dict[str, Any]] = []
    for g in ("SUP", "SUB"):
        for t in range(1, 31):
            pop.append({
                "group": g, "chapter": "chap00", "math_start": t, "math_text": "$x$",
                "token_pos": t, "token": "x", "before": "", "after": "",
            })
    drawn = draw_samples(pop)
    sup = [r for r in drawn if r["group"] == "SUP"]
    sub = [r for r in drawn if r["group"] == "SUB"]
    check("E6 SUP", [r["token_pos"] for r in sup],
          [t for t in range(1, 31) if t not in (6, 7, 13, 15, 22, 28)])
    check("E6 SUB", [r["token_pos"] for r in sub],
          [t for t in range(1, 31) if t not in (11, 17, 19, 21, 24, 29)])
    check("E6 SUP id", [r["sample_id"] for r in sup], [f"SUP-{k:02d}" for k in range(1, 25)])
    check("E6 SUB id", [r["sample_id"] for r in sub], [f"SUB-{k:02d}" for k in range(1, 25)])
    check("E6 件数", len(drawn), 48)

    # E7
    blocks = [{"text": "あ$x$い"}, {"text": "う$y$え"}, {"text": "う$y$え"}, {"text": "か$z$き$z$き"}]
    texts = [block_search_text(b) for b in blocks]
    check("E7 あ$x$い", match_blocks("あ$x$い", texts), [0])
    check("E7 う$y$え", match_blocks("う$y$え", texts), [1, 2])
    check("E7 さ$w$し", match_blocks("さ$w$し", texts), [])
    check("E7 $z$き", match_blocks("$z$き", texts), [3])

    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        return 1
    print("extract_samples selftest: OK (E1-E7)")
    return 0


# ---------------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="feat-025 M3 閾値実験: 標本の抽出・特定")
    p.add_argument("--selftest", action="store_true", help="固定ケースの自己検査（E1〜E7）")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("population", help="インライン数式の字形の出現を全件列挙する")
    sp.add_argument("--final-dir", required=True)
    sp.add_argument("-o", required=True)

    ss = sub.add_parser("sample", help="群ごとに標本を抽出する")
    ss.add_argument("--population", required=True)
    ss.add_argument("-o", required=True)

    sl = sub.add_parser("locate", help="標本の原本上のブロックを特定し切り出す")
    sl.add_argument("--samples", required=True)
    sl.add_argument("--final-dir", required=True)
    sl.add_argument("--tif-root", required=True)
    sl.add_argument("--crops-dir", required=True)
    sl.add_argument("-o", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.command is None:
        parser.error("サブコマンドまたは --selftest が必要")
    try:
        if args.command == "population":
            return cmd_population(args)
        if args.command == "sample":
            return cmd_sample(args)
        return cmd_locate(args)
    except OpError as e:
        sys.stderr.write(f"エラー: {e}\n")
        return 1
    except OSError as e:
        sys.stderr.write(f"エラー: 書き込み・入出力の失敗: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
