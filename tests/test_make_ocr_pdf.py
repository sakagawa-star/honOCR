import io
import os
import sys
from pathlib import Path

import pypdf
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import make_ocr_pdf  # noqa: E402


@pytest.fixture
def rgb_tif(tmp_path: Path) -> Path:
    path = tmp_path / "rgb.tif"
    img = Image.new("RGB", (100, 160), color=(120, 130, 140))
    img.save(path, format="TIFF", compression="tiff_lzw", dpi=(600, 600))
    return path


@pytest.fixture
def blank_tif(tmp_path: Path) -> Path:
    path = tmp_path / "blank.tif"
    img = Image.new("1", (60, 80), color=1)
    img.save(path, format="TIFF", compression="group4")
    return path


@pytest.fixture
def rgba_tif(tmp_path: Path) -> Path:
    path = tmp_path / "rgba.tif"
    img = Image.new("RGBA", (20, 20), color=(10, 20, 30, 255))
    img.save(path, format="TIFF")
    return path


@pytest.fixture
def broken_tif(tmp_path: Path, rgb_tif: Path) -> Path:
    path = tmp_path / "broken.tif"
    data = rgb_tif.read_bytes()
    truncated = data[: int(len(data) * 0.6)]
    path.write_bytes(truncated)
    return path


def test_convert_page_rgb(rgb_tif: Path) -> None:
    png_bytes = make_ocr_pdf.convert_tif_to_png(rgb_tif)
    with Image.open(io.BytesIO(png_bytes)) as im:
        assert im.mode == "L"
        assert im.size == (50, 80)
        dpi = im.info["dpi"]
        # PNG は dpi を整数 px/m で格納するため round-trip で微小誤差が生じる
        assert dpi[0] == pytest.approx(300, abs=0.01)
        assert dpi[1] == pytest.approx(300, abs=0.01)


def test_convert_page_bilevel(blank_tif: Path) -> None:
    png_bytes = make_ocr_pdf.convert_tif_to_png(blank_tif)
    with Image.open(io.BytesIO(png_bytes)) as im:
        assert im.mode == "L"
        assert im.size == (30, 40)


def test_cli_creates_pdf(rgb_tif: Path, blank_tif: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    ret = make_ocr_pdf.main([str(rgb_tif), str(blank_tif), "-o", str(output)])
    assert ret == 0

    reader = pypdf.PdfReader(str(output))
    assert len(reader.pages) == 2

    page = reader.pages[0]
    xobjects = page["/Resources"]["/XObject"]
    image_key = list(xobjects.keys())[0]
    image_obj = xobjects[image_key]
    filters = image_obj["/Filter"]
    filter_names = (
        [str(f) for f in filters] if isinstance(filters, list) else [str(filters)]
    )
    assert "/FlateDecode" in filter_names
    assert "/DCTDecode" not in filter_names

    width_pt = float(page.mediabox.width)
    assert width_pt == pytest.approx(12.0, abs=0.5)


def test_cli_missing_input(tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    missing = tmp_path / "missing.tif"
    ret = make_ocr_pdf.main([str(missing), "-o", str(output)])
    assert ret == 1
    assert not output.exists()


def test_cli_unsupported_mode(rgba_tif: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    ret = make_ocr_pdf.main([str(rgba_tif), "-o", str(output)])
    assert ret == 1
    assert not output.exists()


def test_cli_refuses_overwrite(rgb_tif: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    output.write_bytes(b"existing-content")
    ret = make_ocr_pdf.main([str(rgb_tif), "-o", str(output)])
    assert ret == 1
    assert output.read_bytes() == b"existing-content"


def test_cli_overwrite_flag(rgb_tif: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    output.write_bytes(b"existing-content")
    ret = make_ocr_pdf.main([str(rgb_tif), "-o", str(output), "--overwrite"])
    assert ret == 0
    assert output.exists()
    assert output.read_bytes() != b"existing-content"


def test_cli_truncated_tif(broken_tif: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    ret = make_ocr_pdf.main([str(broken_tif), "-o", str(output)])
    assert ret == 1
    assert not output.exists()


def test_write_atomic_no_clobber_race(tmp_path: Path) -> None:
    output = tmp_path / "out.pdf"
    output.write_bytes(b"existing-content")
    with pytest.raises(FileExistsError):
        make_ocr_pdf.write_pdf_atomic(b"%PDF-1.4 fake", output, overwrite=False)
    assert output.read_bytes() == b"existing-content"
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_atomic_failure_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out.pdf"
    output.write_bytes(b"existing-content")

    def raise_oserror(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", raise_oserror)
    with pytest.raises(OSError):
        make_ocr_pdf.write_pdf_atomic(b"%PDF-1.4 fake", output, overwrite=True)
    assert output.read_bytes() == b"existing-content"
    assert list(tmp_path.glob("*.tmp")) == []
