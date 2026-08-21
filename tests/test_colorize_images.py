import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import colorize_images  # noqa: E402

TIF_WIDTH = 100
TIF_HEIGHT = 160


def _make_pattern_image(width: int = TIF_WIDTH, height: int = TIF_HEIGHT) -> Image.Image:
    """位置ごとに異なる画素値を持つテスト用カラー画像を作る。"""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (x % 256, y % 256, (x + y) % 256)
    return img


def _make_tif_dir(tmp_path: Path) -> Path:
    """page-01_1L.tif・page-01_2R.tif を配置した TIF ディレクトリを作る。"""
    tif_dir = tmp_path / "tif"
    tif_dir.mkdir()
    _make_pattern_image().save(tif_dir / "page-01_1L.tif", format="TIFF")
    _make_pattern_image().save(tif_dir / "page-01_2R.tif", format="TIFF")
    return tif_dir


def _write_content_list(path: Path, blocks: list[dict]) -> None:
    path.write_text(json.dumps(blocks), encoding="utf-8")


def _mean_abs_error(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def test_crop_color_and_size(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/foo.jpg", "page_idx": 0, "bbox": [100, 125, 600, 875]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--scale", "1.0"]
    )
    assert ret == 0

    output_path = outdir / "foo.jpg"
    assert output_path.is_file()

    output_img = Image.open(output_path)
    assert output_img.mode == "RGB"
    assert output_img.size == (50, 120)

    expected = _make_pattern_image().crop((10, 20, 60, 140)).convert("RGB")
    assert _mean_abs_error(expected, output_img) <= 3


def test_scale_default(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/scaled.jpg", "page_idx": 0, "bbox": [0, 0, 600, 750]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 0

    output_img = Image.open(outdir / "scaled.jpg")
    assert output_img.size == (20, 40)


def test_scale_custom(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/scaled.jpg", "page_idx": 0, "bbox": [0, 0, 600, 750]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--scale", "0.5"]
    )
    assert ret == 0

    output_img = Image.open(outdir / "scaled.jpg")
    assert output_img.size == (30, 60)


def test_scale_invalid(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/scaled.jpg", "page_idx": 0, "bbox": [0, 0, 600, 750]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--scale", "0"]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())


def test_bbox_clamp(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/full.jpg", "page_idx": 0, "bbox": [0, 0, 1000, 1000]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--scale", "1.0"]
    )
    assert ret == 0

    output_img = Image.open(outdir / "full.jpg")
    assert output_img.size == (TIF_WIDTH, TIF_HEIGHT)


def test_duplicate_img_path(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [
            {"img_path": "images/dup.jpg", "page_idx": 0, "bbox": [100, 100, 500, 500]},
            {"img_path": "images/dup.jpg", "page_idx": 0, "bbox": [100, 100, 500, 500]},
        ],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 0
    assert list(outdir.iterdir()) == [outdir / "dup.jpg"]


def test_no_image_blocks(tmp_path: Path, capsys) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [{"type": "text", "page_idx": 0}])
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 0
    out = capsys.readouterr().out
    assert "blocks=0" in out


def test_missing_content_list(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    missing = tmp_path / "missing.json"
    outdir = tmp_path / "out"

    ret = colorize_images.main([str(missing), str(tif_dir), "-o", str(outdir)])
    assert ret == 1


def test_invalid_json(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    content_list.write_text("not json {", encoding="utf-8")
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 1


def test_empty_tif_dir(tmp_path: Path) -> None:
    tif_dir = tmp_path / "tif"
    tif_dir.mkdir()
    content_list = tmp_path / "content_list.json"
    _write_content_list(content_list, [])
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 1


def test_page_idx_out_of_range(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/bad.jpg", "page_idx": 2, "bbox": [100, 100, 500, 500]}],
    )
    outdir = tmp_path / "out"

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 1
    assert not outdir.exists() or not any(outdir.iterdir())


def test_bad_bbox(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    outdir = tmp_path / "out"

    bad_bboxes = [
        [100, 100, 500],  # length 3
        [500, 100, 500, 900],  # x0 >= x1
        [100, 100, 1001, 900],  # out of 0-1000 range
    ]

    for i, bbox in enumerate(bad_bboxes):
        content_list = tmp_path / f"content_list_{i}.json"
        _write_content_list(
            content_list,
            [{"img_path": f"images/bad{i}.jpg", "page_idx": 0, "bbox": bbox}],
        )

        ret = colorize_images.main(
            [str(content_list), str(tif_dir), "-o", str(outdir)]
        )
        assert ret == 1
        assert not outdir.exists() or not any(outdir.iterdir())


def test_refuses_overwrite(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/existing.jpg", "page_idx": 0, "bbox": [100, 100, 500, 500]}],
    )
    outdir = tmp_path / "out"
    outdir.mkdir()
    existing = outdir / "existing.jpg"
    existing.write_bytes(b"existing-content")

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 1
    assert existing.read_bytes() == b"existing-content"


def test_overwrite_flag(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    _write_content_list(
        content_list,
        [{"img_path": "images/existing.jpg", "page_idx": 0, "bbox": [100, 100, 500, 500]}],
    )
    outdir = tmp_path / "out"
    outdir.mkdir()
    existing = outdir / "existing.jpg"
    existing.write_bytes(b"existing-content")

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir), "--overwrite", "--scale", "1.0"]
    )
    assert ret == 0
    assert existing.read_bytes() != b"existing-content"
    output_img = Image.open(existing)
    assert output_img.size == (40, 64)


def test_inputs_unchanged(tmp_path: Path) -> None:
    tif_dir = _make_tif_dir(tmp_path)
    content_list = tmp_path / "content_list.json"
    blocks = [{"img_path": "images/foo.jpg", "page_idx": 0, "bbox": [100, 125, 600, 875]}]
    _write_content_list(content_list, blocks)
    outdir = tmp_path / "out"

    tif_1l = tif_dir / "page-01_1L.tif"
    tif_2r = tif_dir / "page-01_2R.tif"
    content_before = content_list.read_bytes()
    tif_1l_before = tif_1l.read_bytes()
    tif_2r_before = tif_2r.read_bytes()

    ret = colorize_images.main(
        [str(content_list), str(tif_dir), "-o", str(outdir)]
    )
    assert ret == 0

    assert content_list.read_bytes() == content_before
    assert tif_1l.read_bytes() == tif_1l_before
    assert tif_2r.read_bytes() == tif_2r_before
