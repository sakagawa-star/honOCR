"""feat-025 M3 閾値実験の実験コード: 字形の高さ・ずれの計測と判定。

仕様は同じフォルダの criteria.md（§3.2・§3.6.5〜§3.6.10・§4）。
標準ライブラリと Pillow だけを使う（numpy は使わない）。
サブコマンド: annotate / compute / fail / summarize、および --selftest。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

INK_THRESHOLD = 200
MIN_AREA = 5  # 面積 4 以下は除外
N_NEED = 19
GROUPS = ["SUP", "SUB", "G1", "G2", "G3"]
ALL_REASONS_Q1 = ["特定不能", "字形不明", "基準文字なし", "成分分離不能", "基準文字分離不能"]
ALL_REASONS_Q2 = ["別の漢字なし", "基準文字なし", "成分分離不能", "基準文字分離不能"]
KEYS = [
    "kind", "sample_id", "group", "png", "status", "target_ids", "ref_ids", "target_bbox",
    "ref_bbox", "h", "H", "BL", "bottom", "r", "d", "italic",
]
TOL = 1e-9
ITALIC_VALUES = ("yes", "no", "判定不能")


class OpError(Exception):
    """運用エラー（終了コード 1）。"""


class ArgError(Exception):
    """引数の誤り（終了コード 2）。"""


class RecordError(Exception):
    """記録の検査の違反（終了コード 1）。"""


# ---------------------------------------------------------------- components


def find_components_with_pixels(gray: Image.Image) -> list[dict[str, Any]]:
    """インク（< 200）の 8 近傍連結成分を求め、面積 5 以上のものに番号を振って返す（画素の一覧 pixels つき）。"""
    w, h = gray.size
    px = gray.load()
    ink = [[px[x, y] < INK_THRESHOLD for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    comps: list[dict[str, Any]] = []
    for y0 in range(h):
        for x0 in range(w):
            if not ink[y0][x0] or seen[y0][x0]:
                continue
            seen[y0][x0] = True
            stack = [(x0, y0)]
            xmin = xmax = x0
            ymin = ymax = y0
            area = 0
            pixels: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                area += 1
                pixels.append((x, y))
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
                if y < ymin:
                    ymin = y
                if y > ymax:
                    ymax = y
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        continue
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        if nx < 0 or nx >= w or (dx == 0 and dy == 0):
                            continue
                        if ink[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            if area >= MIN_AREA:
                comps.append({"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax, "area": area,
                              "pixels": pixels})
    comps.sort(key=lambda c: (c["xmin"], c["ymin"]))
    return [{"id": i, **c} for i, c in enumerate(comps, start=1)]


def find_components(gray: Image.Image) -> list[dict[str, int]]:
    """find_components_with_pixels の結果から画素の一覧を除いたもの。"""
    return [{k: v for k, v in c.items() if k != "pixels"} for c in find_components_with_pixels(gray)]


def compute_slope(pixels: list[tuple[int, int]], ymin: int, ymax: int) -> tuple[Fraction, Fraction, Fraction]:
    """§3.4.1: 上下の帯の x 座標の平均 m_top・m_bot と差 D を Fraction で返す。"""
    h = ymax - ymin + 1
    k = max(1, h // 4)
    top = [x for x, y in pixels if ymin <= y <= ymin + k - 1]
    bot = [x for x, y in pixels if ymax - k + 1 <= y <= ymax]
    m_top = Fraction(sum(top), len(top))
    m_bot = Fraction(sum(bot), len(bot))
    return m_top, m_bot, m_top - m_bot


def slope_value(d: Fraction) -> str:
    if d > 2:
        return "yes"
    if d < -2:
        return "no"
    return "判定不能"

def union_bbox(comps: dict[int, dict[str, int]], ids: list[int]) -> list[int]:
    xs0 = min(comps[i]["xmin"] for i in ids)
    ys0 = min(comps[i]["ymin"] for i in ids)
    xs1 = max(comps[i]["xmax"] for i in ids)
    ys1 = max(comps[i]["ymax"] for i in ids)
    return [xs0, ys0, xs1, ys1]


def compute_metrics(comps: dict[int, dict[str, int]], target_ids: list[int], ref_ids: list[int]) -> dict[str, Any]:
    """§3.1 の h・H・BL・下端・r・d を成分の外接矩形の和集合から計算する（§3.6.6 と §3.6.9 検査 8 で共通）。"""
    tb = union_bbox(comps, target_ids)
    rb = union_bbox(comps, ref_ids)
    h = tb[3] - tb[1] + 1
    big_h = rb[3] - rb[1] + 1
    bl = rb[3]
    bottom = tb[3]
    return {
        "target_ids": sorted(target_ids),
        "ref_ids": sorted(ref_ids),
        "target_bbox": tb,
        "ref_bbox": rb,
        "h": h,
        "H": big_h,
        "BL": bl,
        "bottom": bottom,
        "r": h / big_h,
        "d": (bl - bottom) / big_h,
    }


def comps_paths(annot_dir: Path, png: str) -> Path:
    return annot_dir / f"{Path(png).stem}_components.json"


def load_components(path: Path) -> dict[int, dict[str, int]]:
    if not path.is_file():
        raise OpError(f"components.json が無い: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {c["id"]: c for c in data}


def remove_paths(paths: list[Path]) -> list[str]:
    """パスを削除し、削除できずに残ったパスの文字列の列を返す（既に無いものは残りに数えない）。"""
    left: list[str] = []
    for p in paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            left.append(str(p))
    return left


def cleanup_and_raise(paths: list[Path], cause: Exception) -> None:
    """後片付けをして OpError を送出する。後片付けに失敗したら残ったパスをすべてメッセージに示す。"""
    left = remove_paths(paths)
    if left:
        raise OpError(f"書き込みに失敗: {cause}。後片付けに失敗。残ったパス: {' '.join(left)}") from cause
    raise OpError(f"書き込みに失敗: {cause}") from cause


def atomic_write_text(path: Path, text: str) -> None:
    """出力と同じディレクトリの一時ファイルに書き切り、os.replace で置き換える。"""
    tmps: list[Path] = []
    try:
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        tmps.append(Path(name))
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmps[0], path)
    except OSError as e:
        cleanup_and_raise(tmps, e)


def annotate(png: Path, out_dir: Path) -> str:
    """成分番号つき画像と components.json を作る。既存なら 'exists' を返す。"""
    annot_png = out_dir / f"{png.stem}_annot.png"
    comps_json = out_dir / f"{png.stem}_components.json"
    e1, e2 = annot_png.exists(), comps_json.exists()
    if e1 and e2:
        return "exists"
    if e1 or e2:
        raise OpError(f"片方だけ存在する: {annot_png} / {comps_json}")
    if not png.is_file():
        raise OpError(f"入力が無い: {png}")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OpError(f"書き込み先のディレクトリを作れない: {out_dir}（{e}）") from e
    img = Image.open(png)
    gray = img.convert("L")
    comps = find_components(gray)
    big = img.convert("RGB").resize((img.width * 2, img.height * 2))
    draw = ImageDraw.Draw(big)
    font = ImageFont.load_default()
    for c in comps:
        draw.rectangle([c["xmin"] * 2, c["ymin"] * 2, c["xmax"] * 2 + 1, c["ymax"] * 2 + 1],
                       outline=(255, 0, 0), width=1)
        draw.text((c["xmin"] * 2 + 2, c["ymin"] * 2 + 1), str(c["id"]), fill=(255, 0, 0), font=font)
    cleanup: list[Path] = []
    try:
        fd1, name1 = tempfile.mkstemp(dir=out_dir, prefix=".tmp-")
        tmp_png = Path(name1)
        cleanup.append(tmp_png)
        with os.fdopen(fd1, "wb") as f:
            big.save(f, format="PNG")
        fd2, name2 = tempfile.mkstemp(dir=out_dir, prefix=".tmp-")
        tmp_json = Path(name2)
        cleanup.append(tmp_json)
        with os.fdopen(fd2, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(comps, ensure_ascii=False))
        os.replace(tmp_png, annot_png)
        cleanup.append(annot_png)
        os.replace(tmp_json, comps_json)
    except OSError as e:
        cleanup_and_raise(cleanup, e)
    return "created"


# ----------------------------------------------------------- jsonl utilities


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OpError(f"入力が無い: {path}")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_log_rows(path: Path) -> list[dict[str, Any]]:
    """measurements.jsonl を読む。JSON のオブジェクトとして読めない行があれば形式の違反（RecordError）。"""
    if not path.is_file():
        raise OpError(f"入力が無い: {path}")
    rows: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    raise RecordError(f"行 {i}: JSON として読めない") from None
                if not isinstance(obj, dict):
                    raise RecordError(f"行 {i}: JSON のオブジェクトでない")
                rows.append(obj)
    except UnicodeDecodeError as e:
        raise RecordError(f"UTF-8 として読めない行がある: {e}") from None
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OpError(f"書き込み先のディレクトリを作れない: {path.parent}（{e}）") from e
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_ids(text: str) -> list[int]:
    parts = [p.strip() for p in text.split(",")]
    if not text.strip() or any(p == "" for p in parts):
        raise ArgError(f"成分番号が空または不正: {text!r}")
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise ArgError(f"成分番号が整数でない: {text!r}")


def find_sample(located: list[dict[str, Any]], sample_id: str) -> dict[str, Any]:
    for r in located:
        if r["sample_id"] == sample_id:
            return r
    raise ArgError(f"located.jsonl に sample_id が無い: {sample_id}")


def has_row(log: Path, kind: str, sample_id: str) -> bool:
    if not log.exists():
        return False
    return any(r["kind"] == kind and r["sample_id"] == sample_id for r in read_jsonl(log))


# ------------------------------------------------------------------- compute


def do_compute(located_path: Path, annot_dir: Path, log: Path, sample_id: str, kind: str,
               target: str, ref: str, italic: str | None) -> tuple[dict[str, Any], str | None]:
    located = read_jsonl(located_path)
    s = find_sample(located, sample_id)
    if s["locate_status"] == "特定不能":
        raise ArgError(f"locate_status が 特定不能 の標本: {sample_id}")
    needs_italic = s["group"] == "G2" and kind == "Q1"
    if needs_italic:
        if italic not in ITALIC_VALUES:
            raise ArgError("G2 の Q1 では --italic yes|no|判定不能 が必須")
    elif italic is not None:
        raise ArgError("--italic は G2 の Q1 でだけ指定できる")
    target_ids = parse_ids(target)
    ref_ids = parse_ids(ref)
    if set(target_ids) & set(ref_ids):
        raise ArgError("--target と --ref に同じ番号がある")
    comps = load_components(comps_paths(annot_dir, s["png"]))
    for i in target_ids + ref_ids:
        if i not in comps:
            raise ArgError(f"成分番号が components.json に無い: {i}")
    if has_row(log, kind, sample_id):
        raise OpError(f"同じ (kind, sample_id) の行が既にある: {kind} {sample_id}")
    slope_line: str | None = None
    if needs_italic:
        full = find_components_with_pixels(Image.open(s["png"]).convert("L"))
        redo = {c["id"]: {k: v for k, v in c.items() if k != "pixels"} for c in full}
        if redo != comps:
            raise OpError(f"PNG から求め直した成分が components.json と一致しない: {s['png']}")
        pixels: list[tuple[int, int]] = []
        for c in full:
            if c["id"] in target_ids:
                pixels.extend(c["pixels"])
        tb = union_bbox(comps, target_ids)
        m_top, m_bot, dd = compute_slope(pixels, tb[1], tb[3])
        text = f"m_top={float(m_top):.3f} m_bot={float(m_bot):.3f} D={float(dd):.3f}"
        value = slope_value(dd)
        if value != italic:
            raise ArgError(f"規則による値: {value}（m_top={float(m_top):.3f}, m_bot={float(m_bot):.3f}, D={float(dd):.3f}）")
        slope_line = f"傾き: {text}"
    row: dict[str, Any] = {
        "kind": kind,
        "sample_id": sample_id,
        "group": s["group"] if kind == "Q1" else "Q2",
        "png": s["png"],
        "status": "ok",
    }
    row.update(compute_metrics(comps, target_ids, ref_ids))
    row["italic"] = italic if needs_italic else None
    row = {k: row[k] for k in KEYS}
    append_jsonl(log, row)
    return row, slope_line


def do_fail(located_path: Path, log: Path, sample_id: str, kind: str, reason: str) -> dict[str, Any]:
    located = read_jsonl(located_path)
    s = find_sample(located, sample_id)
    allowed = ALL_REASONS_Q1 if kind == "Q1" else ALL_REASONS_Q2
    if reason not in allowed:
        raise ArgError(f"--kind {kind} で使えない --reason: {reason}")
    if kind == "Q1":
        if s["locate_status"] == "特定不能" and reason != "特定不能":
            raise ArgError("locate_status が 特定不能 の標本には --reason 特定不能 だけ")
        if s["locate_status"] == "ok" and reason == "特定不能":
            raise ArgError("locate_status が ok の標本に --reason 特定不能 は使えない")
    elif s["locate_status"] == "特定不能":
        raise ArgError(f"Q2 に locate_status が 特定不能 の標本は指定できない: {sample_id}")
    if has_row(log, kind, sample_id):
        raise OpError(f"同じ (kind, sample_id) の行が既にある: {kind} {sample_id}")
    row = {k: None for k in KEYS}
    row.update({
        "kind": kind,
        "sample_id": sample_id,
        "group": s["group"] if kind == "Q1" else "Q2",
        "png": s["png"],
        "status": reason,
    })
    append_jsonl(log, row)
    return row


# ----------------------------------------------------------------- summarize


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def is_float(v: Any) -> bool:
    return isinstance(v, float)


def is_int_list(v: Any, n: int | None = None) -> bool:
    return isinstance(v, list) and all(is_int(x) for x in v) and (n is None or len(v) == n)


def q2_targets(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """§3.6.10: (png, sample_id) の列。"""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for g in GROUPS:
        ok = [r for r in rows if r["kind"] == "Q1" and r["group"] == g and r["status"] == "ok"]
        ok.sort(key=lambda r: int(r["sample_id"].split("-")[-1]))
        for r in ok:
            if r["png"] not in seen:
                seen.add(r["png"])
                out.append((r["png"], r["sample_id"]))
    return out


def check_records(located: list[dict[str, Any]], rows: list[dict[str, Any]], annot_dir: Path) -> None:
    def fail(msg: str) -> None:
        raise RecordError(msg)

    # 5. 形式
    for i, r in enumerate(rows, start=1):
        if sorted(r.keys()) != sorted(KEYS):
            fail(f"行 {i}: キーが 16 個と一致しない")
        if r["kind"] not in ("Q1", "Q2"):
            fail(f"行 {i}: kind が不正")
        allowed = ALL_REASONS_Q1 if r["kind"] == "Q1" else ALL_REASONS_Q2
        if r["status"] != "ok" and r["status"] not in allowed:
            fail(f"行 {i}: status が不正: {r['status']}")
        if not isinstance(r["sample_id"], str) or not isinstance(r["group"], str):
            fail(f"行 {i}: sample_id / group の型が不正")
        if r["png"] is not None and not isinstance(r["png"], str):
            fail(f"行 {i}: png の型が不正")
        for key, n in (("target_ids", None), ("ref_ids", None), ("target_bbox", 4), ("ref_bbox", 4)):
            if r[key] is not None and not is_int_list(r[key], n):
                fail(f"行 {i}: {key} の型が不正")
        for key in ("h", "H", "BL", "bottom"):
            if r[key] is not None and not is_int(r[key]):
                fail(f"行 {i}: {key} の型が不正")
        for key in ("r", "d"):
            if r[key] is not None and not is_float(r[key]):
                fail(f"行 {i}: {key} の型が不正")
        if r["italic"] is not None and (not isinstance(r["italic"], str) or r["italic"] not in ITALIC_VALUES):
            fail(f"行 {i}: italic の型が不正")

    # 重複
    seen_keys: set[tuple[str, str]] = set()
    for r in rows:
        k = (r["kind"], r["sample_id"])
        if k in seen_keys:
            fail(f"同じ (kind, sample_id) の行が重複: {k}")
        seen_keys.add(k)

    located_by_id = {r["sample_id"]: r for r in located}
    q1 = [r for r in rows if r["kind"] == "Q1"]
    q2 = [r for r in rows if r["kind"] == "Q2"]

    # 6. Q1 の対応
    for r in q1:
        s = located_by_id.get(r["sample_id"])
        if s is None:
            fail(f"Q1 の sample_id が located.jsonl に無い: {r['sample_id']}")
        if r["group"] != s["group"] or r["png"] != s["png"]:
            fail(f"Q1 の group / png が located.jsonl と一致しない: {r['sample_id']}")
        if s["locate_status"] == "特定不能" and r["status"] != "特定不能":
            fail(f"特定不能の標本の Q1 の status が 特定不能 でない: {r['sample_id']}")
        if s["locate_status"] == "ok" and r["status"] == "特定不能":
            fail(f"ok の標本の Q1 の status が 特定不能: {r['sample_id']}")

    # 1〜3. 群ごとの検査
    for g in GROUPS:
        grows = sorted((r for r in q1 if r["group"] == g), key=lambda r: int(r["sample_id"].split("-")[-1]))
        ks = [int(r["sample_id"].split("-")[-1]) for r in grows]
        if ks != list(range(1, len(ks) + 1)):
            fail(f"{g}: k が 1 から途切れず連続していない")
        oks = [r for r in grows if r["status"] == "ok"]
        if len(oks) > N_NEED:
            fail(f"{g}: ok が {N_NEED} 件を超えている")
        if len(oks) == N_NEED:
            k19 = int(oks[-1]["sample_id"].split("-")[-1])
            if any(int(r["sample_id"].split("-")[-1]) > k19 for r in grows):
                fail(f"{g}: 打ち切り後の標本の行がある")
        else:
            want = {s["sample_id"] for s in located if s["group"] == g}
            got = {r["sample_id"] for r in grows}
            if want != got:
                fail(f"{g}: ok が {N_NEED} 件未満だが全標本の Q1 の行が揃っていない")

    # 4・7. Q2 の対象画像
    targets = q2_targets(rows)
    t_map = {png: sid for png, sid in targets}
    q2_pngs = [r["png"] for r in q2]
    if len(set(q2_pngs)) != len(q2_pngs):
        fail("Q2 の行の png が重複している")
    if set(q2_pngs) != set(t_map):
        fail("Q2 の行が対象画像と一致しない（欠け、または対象外の PNG）")
    for r in q2:
        if r["sample_id"] != t_map[r["png"]] or r["group"] != "Q2":
            fail(f"Q2 の sample_id / group が対象画像と一致しない: {r['sample_id']}")

    # 8・9・10
    for r in rows:
        if r["status"] != "ok":
            for key in ("target_ids", "ref_ids", "target_bbox", "ref_bbox", "h", "H", "BL",
                        "bottom", "r", "d", "italic"):
                if r[key] is not None:
                    fail(f"失敗の行に {key} がある: {r['kind']} {r['sample_id']}")
            continue
        if r["png"] is None:
            fail(f"ok の行の png が null: {r['kind']} {r['sample_id']}")
        tids, rids = r["target_ids"], r["ref_ids"]
        if not tids or not rids or set(tids) & set(rids):
            fail(f"target_ids / ref_ids が空または重なる: {r['kind']} {r['sample_id']}")
        cpath = comps_paths(annot_dir, r["png"])
        try:
            comps = load_components(cpath)
        except OpError as e:
            fail(str(e))
        if any(i not in comps for i in tids + rids):
            fail(f"成分番号が components.json に無い: {r['kind']} {r['sample_id']}")
        m = compute_metrics(comps, tids, rids)
        for key in ("target_ids", "ref_ids", "target_bbox", "ref_bbox", "h", "H", "BL", "bottom"):
            if r[key] != m[key]:
                fail(f"再計算が一致しない ({key}): {r['kind']} {r['sample_id']}")
        for key in ("r", "d"):
            if abs(r[key] - m[key]) > TOL:
                fail(f"再計算が一致しない ({key}): {r['kind']} {r['sample_id']}")
        is_g2_q1 = r["kind"] == "Q1" and r["group"] == "G2"
        if is_g2_q1 != isinstance(r["italic"], str) or (not is_g2_q1 and r["italic"] is not None):
            fail(f"italic の型が不正: {r['kind']} {r['sample_id']}")


def rng(rows: list[dict[str, Any]], key: str) -> tuple[float | None, float | None]:
    vals = [r[key] for r in rows]
    return (min(vals), max(vals)) if vals else (None, None)


def summarize(located_path: Path, log: Path, annot_dir: Path, out: Path) -> dict[str, Any]:
    located = read_jsonl(located_path)
    rows = read_log_rows(log)
    check_records(located, rows, annot_dir)

    counts: dict[str, Any] = {}
    ranges: dict[str, Any] = {}
    oks: dict[str, list[dict[str, Any]]] = {}
    for g in GROUPS + ["Q2"]:
        kind = "Q2" if g == "Q2" else "Q1"
        grp = [r for r in rows if r["kind"] == kind and (g == "Q2" or r["group"] == g)]
        ok = [r for r in grp if r["status"] == "ok"]
        oks[g] = ok
        counts[g] = {"measured": len(grp), "ok": len(ok)}
        rmin, rmax = rng(ok, "r")
        dmin, dmax = rng(ok, "d")
        ranges[g] = {"r_min": rmin, "r_max": rmax, "d_min": dmin, "d_max": dmax}
        if g == "Q2":
            ranges[g]["absd_max"] = max(abs(r["d"]) for r in ok) if ok else None
    q3 = {v: sum(1 for r in oks["G2"] if r["italic"] == v) for v in ITALIC_VALUES}

    shortage = any(counts[g]["ok"] < N_NEED for g in GROUPS + ["Q2"])
    thresholds: dict[str, Any]
    conditions: dict[str, Any]
    if shortage:
        thresholds = {k: None for k in ("T_bl", "T_raise", "T_drop", "T_small", "T_band_G1", "T_band_G2", "T_large")}
        conditions = {k: None for k in ("T_raise", "T_drop", "T_small", "T_band_G1_T_large")}
        verdict = "測定不足"
    else:
        t_bl = ranges["Q2"]["absd_max"]
        t_raise = ranges["SUP"]["d_min"]
        t_drop = min(-r["d"] for r in oks["SUB"])
        g2_deep = max(-r["d"] for r in oks["G2"])
        t_small = max(ranges["SUP"]["r_max"], ranges["SUB"]["r_max"])
        g1_lo, g1_hi = ranges["G1"]["r_min"], ranges["G1"]["r_max"]
        g2_lo, g2_hi = ranges["G2"]["r_min"], ranges["G2"]["r_max"]
        t_large = ranges["G3"]["r_min"]
        thresholds = {
            "T_bl": t_bl, "T_raise": t_raise, "T_drop": t_drop, "T_small": t_small,
            "T_band_G1": [g1_lo, g1_hi], "T_band_G2": [g2_lo, g2_hi], "T_large": t_large,
        }
        conditions = {
            "T_raise": t_raise > t_bl,
            "T_drop": t_drop > t_bl and t_drop > g2_deep,
            "T_small": t_small < g1_lo,
            "T_band_G1_T_large": g1_hi < t_large,
        }
        verdict = "合格" if all(conditions.values()) else "不合格"

    result = {
        "counts": counts,
        "ranges": ranges,
        "q3_italic": q3,
        "thresholds": thresholds,
        "conditions": conditions,
        "verdict": verdict,
    }
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OpError(f"出力先の親ディレクトリを作れない: {out.parent}: {e}") from e
    atomic_write_text(out, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


# ------------------------------------------------------------------ selftest


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_m2(base: Path, drop: tuple[str, int] | None = None, g3_fail: bool = False,
             sup_d: float | None = None) -> tuple[Path, Path, Path]:
    """M2 の located.jsonl・measurements.jsonl・annot-dir を base に作る。"""
    annot = base / "annot"
    annot.mkdir(parents=True)
    spec = {  # 群: (r, d, italic)
        "SUP": (0.6, 0.5, None), "SUB": (0.6, -0.5, None), "G1": (1.0, 0.0, None),
        "G2": (0.6, -0.1, "G2"), "G3": (1.8, -0.2, None),
    }
    located: list[dict[str, Any]] = []
    log: list[dict[str, Any]] = []
    q2_rows: list[dict[str, Any]] = []
    n = 0
    for g in GROUPS:
        r_val, d_val, ital = spec[g]
        if sup_d is not None and g == "SUP":
            d_val = sup_d
        if g == "G3" and g3_fail:
            for k in (1, 2):
                sid = f"G3-{k:02d}"
                located.append({"sample_id": sid, "group": "G3", "locate_status": "特定不能", "png": None})
                row = {key: None for key in KEYS}
                row.update({"kind": "Q1", "sample_id": sid, "group": "G3", "status": "特定不能"})
                log.append(row)
            continue
        for k in range(1, 20):
            if drop == (g, k):
                continue
            n += 1
            sid = f"{g}-{k:02d}"
            png = f"/x/crops/p{n:03d}.png"
            located.append({"sample_id": sid, "group": g, "locate_status": "ok", "png": png})
            h = round(r_val * 20)
            bottom = round(39 - d_val * 20)
            comps = [
                {"id": 1, "xmin": 0, "ymin": 20, "xmax": 9, "ymax": 39, "area": 100},
                {"id": 2, "xmin": 10, "ymin": bottom - h + 1, "xmax": 15, "ymax": bottom, "area": 50},
                {"id": 3, "xmin": 20, "ymin": 19, "xmax": 29, "ymax": 38, "area": 100},
            ]
            (annot / f"p{n:03d}_components.json").write_text(json.dumps(comps), encoding="utf-8")
            cm = {c["id"]: c for c in comps}
            m1 = compute_metrics(cm, [2], [1])
            row = {"kind": "Q1", "sample_id": sid, "group": g, "png": png, "status": "ok", **m1,
                   "italic": (("yes" if k <= 10 else "no" if k <= 15 else "判定不能") if ital == "G2" else None)}
            log.append({k2: row[k2] for k2 in KEYS})
            m2 = compute_metrics(cm, [3], [1])
            row2 = {"kind": "Q2", "sample_id": sid, "group": "Q2", "png": png, "status": "ok", **m2,
                    "italic": None}
            q2_rows.append({k2: row2[k2] for k2 in KEYS})
    log.extend(q2_rows)
    lp, mp = base / "located.jsonl", base / "measurements.jsonl"
    write_jsonl(lp, located)
    write_jsonl(mp, log)
    return lp, mp, annot


def selftest() -> int:
    errors: list[str] = []

    def check(name: str, got: Any, want: Any) -> None:
        if got != want:
            errors.append(f"{name}: 期待 {want!r} / 実際 {got!r}")

    def close(name: str, got: Any, want: float) -> None:
        if got is None or abs(got - want) > TOL:
            errors.append(f"{name}: 期待 {want!r} / 実際 {got!r}")

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        # M1
        img = Image.new("L", (100, 60), 255)
        d = ImageDraw.Draw(img)
        d.rectangle([10, 20, 19, 39], fill=0)
        d.rectangle([30, 10, 35, 17], fill=0)
        d.rectangle([50, 50, 51, 51], fill=0)
        png = tdp / "m1.png"
        img.save(png)
        annot_dir = tdp / "m1_annot"
        check("M1 annotate", annotate(png, annot_dir), "created")
        check("M1 annotate 再実行", annotate(png, annot_dir), "exists")
        comps = load_components(annot_dir / "m1_components.json")
        check("M1 成分数", sorted(comps), [1, 2])
        check("M1 成分 1", [comps[1][k] for k in ("xmin", "ymin", "xmax", "ymax")], [10, 20, 19, 39])
        check("M1 成分 2", [comps[2][k] for k in ("xmin", "ymin", "xmax", "ymax")], [30, 10, 35, 17])
        located_m1 = tdp / "m1_located.jsonl"
        write_jsonl(located_m1, [{"sample_id": "G1-01", "group": "G1", "locate_status": "ok", "png": str(png)}])
        log_m1 = tdp / "m1_log.jsonl"
        row, _ = do_compute(located_m1, annot_dir, log_m1, "G1-01", "Q1", "2", "1", None)
        check("M1 H", row["H"], 20)
        check("M1 BL", row["BL"], 39)
        check("M1 h", row["h"], 8)
        check("M1 bottom", row["bottom"], 17)
        close("M1 r", row["r"], 0.4)
        close("M1 d", row["d"], 1.1)

        def run_summarize(name: str, base: Path, lp: Path, mp: Path, ap: Path) -> tuple[int, dict[str, Any] | None, Path]:
            out = base / "summary.json"
            try:
                res = summarize(lp, mp, ap, out)
                return 0, res, out
            except RecordError:
                return 1, None, out

        # M2
        b = tdp / "m2"
        b.mkdir()
        lp, mp, ap = build_m2(b)
        code, res, _ = run_summarize("M2", b, lp, mp, ap)
        check("M2 終了コード", code, 0)
        if res:
            th = res["thresholds"]
            close("M2 T_bl", th["T_bl"], 0.05)
            close("M2 T_raise", th["T_raise"], 0.5)
            close("M2 T_drop", th["T_drop"], 0.5)
            close("M2 T_small", th["T_small"], 0.6)
            close("M2 T_band_G1[0]", th["T_band_G1"][0], 1.0)
            close("M2 T_band_G1[1]", th["T_band_G1"][1], 1.0)
            close("M2 T_band_G2[0]", th["T_band_G2"][0], 0.6)
            close("M2 T_band_G2[1]", th["T_band_G2"][1], 0.6)
            close("M2 T_large", th["T_large"], 1.8)
            check("M2 条件", res["conditions"], {k: True for k in ("T_raise", "T_drop", "T_small", "T_band_G1_T_large")})
            check("M2 q3", res["q3_italic"], {"yes": 10, "no": 5, "判定不能": 4})
            check("M2 verdict", res["verdict"], "合格")

        # M3
        b = tdp / "m3"
        b.mkdir()
        lp, mp, ap = build_m2(b, drop=("SUP", 19))
        code, res, _ = run_summarize("M3", b, lp, mp, ap)
        check("M3 終了コード", code, 0)
        if res:
            check("M3 verdict", res["verdict"], "測定不足")
            check("M3 閾値 null", all(v is None for v in res["thresholds"].values()), True)
            check("M3 条件 null", all(v is None for v in res["conditions"].values()), True)

        # M4
        b = tdp / "m4"
        b.mkdir()
        lp, mp, ap = build_m2(b, sup_d=0.05)
        code, res, _ = run_summarize("M4", b, lp, mp, ap)
        check("M4 終了コード", code, 0)
        if res:
            close("M4 T_raise", res["thresholds"]["T_raise"], 0.05)
            check("M4 条件 T_raise", res["conditions"]["T_raise"], False)
            check("M4 verdict", res["verdict"], "不合格")

        # M5
        b = tdp / "m5"
        b.mkdir()
        lp, mp, ap = build_m2(b, g3_fail=True)
        code, res, _ = run_summarize("M5", b, lp, mp, ap)
        check("M5 終了コード", code, 0)
        if res:
            check("M5 counts.G3", res["counts"]["G3"], {"measured": 2, "ok": 0})
            check("M5 ranges.G3", all(v is None for v in res["ranges"]["G3"].values()), True)
            check("M5 verdict", res["verdict"], "測定不足")
            check("M5 閾値 null", all(v is None for v in res["thresholds"].values()), True)
            check("M5 条件 null", all(v is None for v in res["conditions"].values()), True)

        # M6
        b = tdp / "m6"
        b.mkdir()
        lp, mp, ap = build_m2(b)
        rows = read_jsonl(mp)
        for r in rows:
            if r["kind"] == "Q1" and r["sample_id"] == "SUP-01":
                r["r"] = 0.7
        write_jsonl(mp, rows)
        code, _res, out = run_summarize("M6", b, lp, mp, ap)
        check("M6 終了コード", code, 1)
        check("M6 summary.json を書かない", out.exists(), False)

        # M7 / M8
        def make_slope_pngs(base: Path) -> tuple[Path, list[tuple[str, Path]]]:
            base.mkdir()
            rules = {
                "a": lambda y: (30 + (29 - y) // 4, 32 + (29 - y) // 4),
                "b": lambda y: (30 + (y - 10) // 4, 32 + (y - 10) // 4),
                "c": lambda y: (30, 32),
                "d": lambda y: (32, 34) if y <= 14 else (30, 32),
            }
            items: list[tuple[str, Path]] = []
            loc: list[dict[str, Any]] = []
            for name, fn in rules.items():
                im = Image.new("L", (100, 60), 255)
                dr = ImageDraw.Draw(im)
                dr.rectangle([10, 20, 19, 39], fill=0)
                for yy in range(10, 30):
                    x0, x1 = fn(yy)
                    dr.rectangle([x0, yy, x1, yy], fill=0)
                pp = base / f"{name}.png"
                im.save(pp)
                items.append((name, pp))
                loc.append({"sample_id": f"G2-{name}", "group": "G2", "locate_status": "ok", "png": str(pp)})
            loc.append({"sample_id": "G1-x", "group": "G1", "locate_status": "ok", "png": str(items[0][1])})
            lpath = base / "located.jsonl"
            write_jsonl(lpath, loc)
            return lpath, items

        b = tdp / "m7"
        lp7, items = make_slope_pngs(b)
        ad7 = b / "annot"
        log7 = b / "log.jsonl"
        want7 = {
            "a": ("yes", "傾き: m_top=34.800 m_bot=31.200 D=3.600"),
            "b": ("no", "傾き: m_top=31.200 m_bot=34.800 D=-3.600"),
            "c": ("判定不能", "傾き: m_top=31.000 m_bot=31.000 D=0.000"),
            "d": ("判定不能", "傾き: m_top=33.000 m_bot=31.000 D=2.000"),
        }
        for name, pp in items:
            annotate(pp, ad7)
            cm7 = load_components(comps_paths(ad7, str(pp)))
            check(f"M7 {name} 成分数", sorted(cm7), [1, 2])
            try:
                row7, line7 = do_compute(lp7, ad7, log7, f"G2-{name}", "Q1", "2", "1", want7[name][0])
                check(f"M7 {name} italic", row7["italic"], want7[name][0])
                check(f"M7 {name} h", row7["h"], 20)
                check(f"M7 {name} 傾き行", line7, want7[name][1])
            except (ArgError, OpError) as e:
                errors.append(f"M7 {name}: 例外 {e}")
        check("M7 追記行数", len(read_jsonl(log7)) if log7.exists() else 0, 4)

        b = tdp / "m8"
        lp8, items8 = make_slope_pngs(b)
        ad8 = b / "annot"
        log8 = b / "log.jsonl"
        pa = items8[0][1]
        annotate(pa, ad8)
        try:
            do_compute(lp8, ad8, log8, "G2-a", "Q1", "2", "1", "no")
            errors.append("M8(1): ArgError が出ない")
        except ArgError as e:
            check("M8(1) 規則による値", "規則による値: yes" in str(e), True)
        check("M8(1) 追記しない", log8.exists(), False)
        for label, sid, ital in (("M8(3)", "G1-x", "判定不能"), ("M8(4)", "G2-a", None)):
            try:
                do_compute(lp8, ad8, log8, sid, "Q1", "2", "1", ital)
                errors.append(f"{label}: ArgError が出ない")
            except ArgError:
                pass
        cj = comps_paths(ad8, str(pa))
        data = json.loads(cj.read_text(encoding="utf-8"))
        for c in data:
            if c["id"] == 2:
                c["xmax"] += 1
        cj.write_text(json.dumps(data), encoding="utf-8")
        try:
            do_compute(lp8, ad8, log8, "G2-a", "Q1", "2", "1", "yes")
            errors.append("M8(2): OpError が出ない")
        except OpError:
            pass
        check("M8 追記しない", log8.exists(), False)

    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        return 1
    print("measure_glyphs selftest: OK (M1-M8)")
    return 0


# ---------------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="feat-025 M3 閾値実験: 字形の計測")
    p.add_argument("--selftest", action="store_true", help="固定ケースの自己検査（M1〜M8）")
    sub = p.add_subparsers(dest="command")

    sa = sub.add_parser("annotate", help="連結成分に番号を振った画像と components.json を作る")
    sa.add_argument("--png", required=True)
    sa.add_argument("--out-dir", required=True)

    sc = sub.add_parser("compute", help="選んだ成分から h・H・BL・r・d を計算して追記する")
    sc.add_argument("--located", required=True)
    sc.add_argument("--annot-dir", required=True)
    sc.add_argument("--log", required=True)
    sc.add_argument("--sample-id", required=True)
    sc.add_argument("--kind", required=True, choices=["Q1", "Q2"])
    sc.add_argument("--target", required=True)
    sc.add_argument("--ref", required=True)
    sc.add_argument("--italic", choices=list(ITALIC_VALUES))

    sf = sub.add_parser("fail", help="測定失敗の行を追記する")
    sf.add_argument("--located", required=True)
    sf.add_argument("--log", required=True)
    sf.add_argument("--sample-id", required=True)
    sf.add_argument("--kind", required=True, choices=["Q1", "Q2"])
    sf.add_argument("--reason", required=True)

    ss = sub.add_parser("summarize", help="記録を検査し、閾値と判定を出す")
    ss.add_argument("--located", required=True)
    ss.add_argument("--log", required=True)
    ss.add_argument("--annot-dir", required=True)
    ss.add_argument("-o", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.command is None:
        parser.error("サブコマンドまたは --selftest が必要")
    try:
        if args.command == "annotate":
            png = Path(args.png)
            out_dir = Path(args.out_dir)
            if annotate(png, out_dir) == "exists":
                print(f"既存: {out_dir / (png.stem + '_annot.png')} {out_dir / (png.stem + '_components.json')}")
            return 0
        if args.command == "compute":
            row, slope_line = do_compute(Path(args.located), Path(args.annot_dir), Path(args.log),
                                         args.sample_id, args.kind, args.target, args.ref, args.italic)
            print(json.dumps(row, ensure_ascii=False))
            if slope_line is not None:
                print(slope_line)
            return 0
        if args.command == "fail":
            do_fail(Path(args.located), Path(args.log), args.sample_id, args.kind, args.reason)
            return 0
        out = Path(args.o)
        if out.exists():
            raise OpError(f"出力先が既にある: {out}")
        res = summarize(Path(args.located), Path(args.log), Path(args.annot_dir), out)
        print(f"判定: {res['verdict']}")
        return 0
    except ArgError as e:
        sys.stderr.write(f"引数の誤り: {e}\n")
        return 2
    except (OpError, RecordError) as e:
        sys.stderr.write(f"エラー: {e}\n")
        return 1
    except OSError as e:
        sys.stderr.write(f"エラー: 書き込み・入出力の失敗: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
