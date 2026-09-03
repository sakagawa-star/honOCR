import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import crop_blocks  # noqa: E402

TIF_WIDTH = 100
TIF_HEIGHT = 100


def _make_pattern_image(width: int = TIF_WIDTH, height: int = TIF_HEIGHT) -> Image.Image:
    """位置ごとに異なる画素値を持つテスト用グレースケール画像を作る。"""
    img = Image.new("L", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (x + y) % 256
    return img


def _make_tif_dir(tmp_path: Path) -> Path:
    """page-01_1L.tif・page-01_2R.tif を配置した TIF ディレクトリを作る。"""
    tif_dir = tmp_path / "tif"
    tif_dir.mkdir()
    _make_pattern_image().save(tif_dir / "page-01_1L.tif", format="TIFF")
    _make_pattern_image().save(tif_dir / "page-01_2R.tif", format="TIFF")
    return tif_dir


def _write_content_list(path: Path, blocks: list) -> None:
    path.write_text(json.dumps(blocks), encoding="utf-8")


# T-01: bbox_to_pixels が 0-1000 を正しくピクセルへ変換する
def test_bbox_to_pixels_conversion() -> None:
    assert crop_blocks.bbox_to_pixels([0, 0, 1000, 1000], (100, 100)) == (0, 0, 100, 100)
    assert crop_blocks.bbox_to_pixels([500, 0, 1000, 500], (100, 100)) == (50, 0, 100, 50)


# T-02: bbox_to_pixels が範囲外の値をクランプする
def test_bbox_to_pixels_clamp() -> None:
    assert crop_blocks.bbox_to_pixels([-100, -50, 1100, 1200], (100, 100)) == (0, 0, 100, 100)


# T-03: list_tifs が 1L・2R を混ぜてファイル名順に並べる
def test_list_tifs_sorted(tmp_path: Path) -> None:
    tif_dir = tmp_path / "tif"
    tif_dir.mkdir()
    for name in ["page-02_1L.tif", "page-01_2R.tif", "page-01_1L.tif", "page-02_2R.tif"]:
        _make_pattern_image().save(tif_dir / name, format="TIFF")

    tifs = crop_blocks.list_tifs(tif_dir)
    assert [p.name for p in tifs] == [
        "page-01_1L.tif",
        "page-01_2R.tif",
        "page-02_1L.tif",
        "page-02_2R.tif",
    ]


# T-04: 正常系: --index 2個で PNG が2枚できる（ファイル名・mode を確認）
def test_two_indices_produce_two_pngs(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "chapNN_gray300_content_list.json"
    _write_content_list(
        content_list,
        [
            {"type": "text", "text_level": 2, "page_idx": 0, "bbox": [100, 100, 500, 500]},
            {"type": "text", "text_level": 2, "page_idx": 1, "bbox": [200, 200, 600, 600]},
        ],
    )
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0", "--index", "1"]
    )
    assert ret == 0

    files = sorted(outdir.iterdir())
    assert [f.name for f in files] == [
        "chapNN_gray300_content_list_b0_p0.png",
        "chapNN_gray300_content_list_b1_p1.png",
    ]
    for f in files:
        img = Image.open(f)
        assert img.mode == "L"


# T-05: 切り出し領域が正しい
def test_crop_region_correct(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 200, 600, 700]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0", "--margin", "0"]
    )
    assert ret == 0

    output_img = Image.open(outdir / "content_list_b0_p0.png")
    expected = _make_pattern_image().crop((10, 20, 60, 70))
    assert list(output_img.getdata()) == list(expected.getdata())


# T-06: --margin が四方に効く
def test_margin_increases_size(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 200, 600, 700]}])

    outdir0 = tmp_path / "out0"
    ret0 = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir0), "--index", "0", "--margin", "0"]
    )
    assert ret0 == 0
    size0 = Image.open(outdir0 / "content_list_b0_p0.png").size

    outdir1 = tmp_path / "out1"
    ret1 = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir1), "--index", "0", "--margin", "100"]
    )
    assert ret1 == 0
    size1 = Image.open(outdir1 / "content_list_b0_p0.png").size

    assert size1[0] > size0[0]
    assert size1[1] > size0[1]
    # TIF は 100x100 のため、正規化 margin=100 は各辺 10px に相当する
    assert size1 == (size0[0] + 20, size0[1] + 20)


# T-07: --max-width 超過で縮小される
def test_max_width_shrinks(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [0, 0, 1000, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [
            str(content_list),
            str(tif_dir),
            "-o",
            str(outdir),
            "--index",
            "0",
            "--margin",
            "0",
            "--max-width",
            "40",
        ]
    )
    assert ret == 0

    img = Image.open(outdir / "content_list_b0_p0.png")
    assert img.size == (40, 20)


# T-08: --max-width ちょうどでは縮小しない
def test_max_width_exact_no_shrink(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [0, 0, 1000, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [
            str(content_list),
            str(tif_dir),
            "-o",
            str(outdir),
            "--index",
            "0",
            "--margin",
            "0",
            "--max-width",
            "100",
        ]
    )
    assert ret == 0

    img = Image.open(outdir / "content_list_b0_p0.png")
    assert img.size == (100, 50)


# T-09: 範囲外 --index でエラー
def test_index_out_of_range(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [0, 0, 500, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "5"]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())


# T-10: 範囲外 page_idx でエラー
def test_page_idx_out_of_range(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)  # 2 tifs -> valid page_idx は 0, 1
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 2, "bbox": [0, 0, 500, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())


# T-11: 不正 bbox（長さ違い・非数値・範囲外・順序逆転）でエラー
def test_bad_bbox(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    outdir = tmp_path / "out"

    bad_bboxes = [
        [100, 100, 500],  # length 3
        ["a", 100, 500, 900],  # non-numeric
        [500, 100, 100, 900],  # x0 > x1
        [100, 100, 1001, 900],  # out of 0-1000 range
    ]

    for i, bbox in enumerate(bad_bboxes):
        content_list = tmp_path / f"content_list_{i}.json"
        _write_content_list(content_list, [{"page_idx": 0, "bbox": bbox}])

        ret = crop_blocks.main(
            [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
        )
        assert ret == 1
        assert not outdir.exists() or not any(outdir.iterdir())


# T-12: 既存ファイルがあり --overwrite なしでエラー（内容が変わらない）
def test_refuses_overwrite(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"
    outdir.mkdir()
    existing = outdir / "content_list_b0_p0.png"
    existing.write_bytes(b"existing-content")

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
    )
    assert ret == 1
    assert existing.read_bytes() == b"existing-content"


# T-13: --overwrite ありなら上書きする
def test_overwrite_flag(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"
    outdir.mkdir()
    existing = outdir / "content_list_b0_p0.png"
    existing.write_bytes(b"existing-content")

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0", "--overwrite"]
    )
    assert ret == 0
    assert existing.read_bytes() != b"existing-content"
    img = Image.open(existing)
    assert img.mode == "L"


# T-14: 複数エラーが全件列挙される
def test_multiple_errors_listed(tmp_path: Path, capsys) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "5", "--index", "9"]
    )
    assert ret == 1
    err = capsys.readouterr().err
    lines = [line for line in err.splitlines() if line]
    assert len(lines) >= 2


# T-15: 入力の content_list と TIF が変更されない
def test_inputs_unchanged(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"

    tif_1l = tif_dir / "page-01_1L.tif"
    tif_2r = tif_dir / "page-01_2R.tif"
    content_before = content_list.read_bytes()
    tif_1l_before = tif_1l.read_bytes()
    tif_2r_before = tif_2r.read_bytes()

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
    )
    assert ret == 0

    assert content_list.read_bytes() == content_before
    assert tif_1l.read_bytes() == tif_1l_before
    assert tif_2r.read_bytes() == tif_2r_before


# T-16: --margin 負値・--max-width 0以下でエラー
def test_negative_margin_and_bad_max_width(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])

    outdir1 = tmp_path / "out1"
    ret1 = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir1), "--index", "0", "--margin", "-1"]
    )
    assert ret1 == 1
    assert not outdir1.exists() or not any(outdir1.iterdir())

    outdir2 = tmp_path / "out2"
    ret2 = crop_blocks.main(
        [
            str(content_list),
            str(tif_dir),
            "-o",
            str(outdir2),
            "--index",
            "0",
            "--max-width",
            "0",
        ]
    )
    assert ret2 == 1
    assert not outdir2.exists() or not any(outdir2.iterdir())


# T-17: --margin が NaN / inf でエラー（math.isfinite による検証）
def test_margin_nan_inf(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])

    for value in ["nan", "inf"]:
        outdir = tmp_path / f"out_{value}"
        ret = crop_blocks.main(
            [
                str(content_list),
                str(tif_dir),
                "-o",
                str(outdir),
                "--index",
                "0",
                "--margin",
                value,
            ]
        )
        assert ret == 1
        assert not outdir.exists() or not any(outdir.iterdir())


# T-18: bbox に NaN / inf / bool を含むブロックを指定してエラー
def test_bbox_nan_inf_bool(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    outdir = tmp_path / "out"

    bad_blocks = [
        {"page_idx": 0, "bbox": [float("nan"), 100, 500, 500]},
        {"page_idx": 0, "bbox": [float("inf"), 100, 500, 500]},
        {"page_idx": 0, "bbox": [True, 100, 500, 500]},
    ]

    for i, block in enumerate(bad_blocks):
        content_list = tmp_path / f"content_list_{i}.json"
        _write_content_list(content_list, [block])

        ret = crop_blocks.main(
            [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
        )
        assert ret == 1
        assert not outdir.exists() or not any(outdir.iterdir())


# T-19: --index に同じ番号を2回指定してエラー
def test_duplicate_index_errors(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": 0, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0", "--index", "0"]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())


# T-20: page_idx が bool（True）のブロックを指定してエラー
def test_page_idx_bool(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"page_idx": True, "bbox": [100, 100, 500, 500]}])
    outdir = tmp_path / "out"

    ret = crop_blocks.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--index", "0"]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())
