import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import build_final  # noqa: E402


BASE = "chap07_gray300"


def _write_content_list(path: Path, blocks: list[dict]) -> None:
    path.write_text(json.dumps(blocks, ensure_ascii=False), encoding="utf-8")


def _make_normalized_dir(
    tmp_path: Path,
    base: str = BASE,
    md_text: str = "# 本文\n\n![](images/a.jpg)\n",
    blocks: list[dict] | None = None,
    images: dict[str, bytes] | None = None,
) -> Path:
    """md・content_list・images/ を含む正規化済みディレクトリを作る。"""
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()

    if blocks is None:
        blocks = [{"type": "image", "img_path": "images/a.jpg", "page_idx": 0}]

    (normalized_dir / f"{base}.md").write_text(md_text, encoding="utf-8")
    _write_content_list(normalized_dir / f"{base}{build_final.CONTENT_LIST_SUFFIX}", blocks)

    if images is None:
        images = {"a.jpg": b"jpegdata-a"}
    if images:
        images_dir = normalized_dir / build_final.IMAGES_DIRNAME
        images_dir.mkdir()
        for name, data in images.items():
            (images_dir / name).write_bytes(data)

    return normalized_dir


# --- FR-001: 基本構築 --------------------------------------------------------


def test_build_copies_three_parts(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        blocks=[
            {"type": "image", "img_path": "images/a.jpg", "page_idx": 0},
            {"type": "image", "img_path": "images/b.jpg", "page_idx": 0},
        ],
        images={"a.jpg": b"AAA", "b.jpg": b"BBB"},
        md_text="# 本文\n\n![](images/a.jpg)\n![](images/b.jpg)\n",
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0
    assert (outdir / f"{BASE}.md").is_file()
    assert (outdir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").is_file()
    assert (outdir / "images" / "a.jpg").is_file()
    assert (outdir / "images" / "b.jpg").is_file()


def test_build_byte_identical(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0
    md_src = normalized_dir / f"{BASE}.md"
    cl_src = normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}"
    img_src = normalized_dir / "images" / "a.jpg"

    assert (outdir / f"{BASE}.md").read_bytes() == md_src.read_bytes()
    assert (outdir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").read_bytes() == cl_src.read_bytes()
    assert (outdir / "images" / "a.jpg").read_bytes() == img_src.read_bytes()


def test_build_source_unchanged(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"

    md_before = (normalized_dir / f"{BASE}.md").read_bytes()
    cl_before = (normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").read_bytes()
    img_before = (normalized_dir / "images" / "a.jpg").read_bytes()

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0
    assert (normalized_dir / f"{BASE}.md").read_bytes() == md_before
    assert (normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").read_bytes() == cl_before
    assert (normalized_dir / "images" / "a.jpg").read_bytes() == img_before


def test_build_summary_format(tmp_path: Path, capsys) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        blocks=[
            {"type": "image", "img_path": "images/a.jpg", "page_idx": 0},
            {"type": "image", "img_path": "images/b.jpg", "page_idx": 0},
        ],
        images={"a.jpg": b"AAA", "b.jpg": b"BBB"},
        md_text="# 本文\n\n![](images/a.jpg)\n![](images/b.jpg)\n",
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])
    assert ret == 0

    captured = capsys.readouterr()
    assert f"{BASE}: md=1 content_list=1 images=2" in captured.out
    assert "total: 1 built" in captured.out


def test_build_rejects_existing_without_overwrite(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"
    outdir.mkdir()
    (outdir / f"{BASE}.md").write_text("existing", encoding="utf-8")

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert (outdir / f"{BASE}.md").read_text(encoding="utf-8") == "existing"
    assert not (outdir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").exists()


def test_build_overwrite_replaces(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"
    outdir.mkdir()
    (outdir / f"{BASE}.md").write_text("existing", encoding="utf-8")

    ret = build_final.main([str(normalized_dir), "-o", str(outdir), "--overwrite"])

    assert ret == 0
    assert (outdir / f"{BASE}.md").read_bytes() == (normalized_dir / f"{BASE}.md").read_bytes()


# --- FR-002: 入力検証 --------------------------------------------------------


def test_missing_normalized_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    outdir = tmp_path / "final"

    ret = build_final.main([str(missing), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_no_content_list(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_multiple_content_lists(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    _write_content_list(normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}", [])
    _write_content_list(normalized_dir / f"other{build_final.CONTENT_LIST_SUFFIX}", [])
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_missing_md(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    _write_content_list(normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}", [])
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_empty_md(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("", encoding="utf-8")
    _write_content_list(normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}", [])
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_content_list_not_json(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    (normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").write_text(
        "{not json", encoding="utf-8"
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_content_list_not_array(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    (normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}").write_text(
        json.dumps({"not": "an array"}), encoding="utf-8"
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_rejects_outdir_equal_to_source(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    md_before = (normalized_dir / f"{BASE}.md").read_bytes()

    for extra_args in ([], ["--overwrite"]):
        ret = build_final.main([str(normalized_dir), "-o", str(normalized_dir)] + extra_args)
        assert ret == 1
        assert (normalized_dir / f"{BASE}.md").read_bytes() == md_before


def test_rejects_outdir_inside_source(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = normalized_dir / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_rejects_source_inside_outdir(tmp_path: Path) -> None:
    outdir = tmp_path / "final"
    outdir.mkdir()
    # コピー元を outdir の配下に置く
    normalized_dir = outdir / "normalized_inside"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    _write_content_list(normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}", [])

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1


def test_images_src_not_a_directory(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / f"{BASE}.md").write_text("x", encoding="utf-8")
    _write_content_list(normalized_dir / f"{BASE}{build_final.CONTENT_LIST_SUFFIX}", [])
    (normalized_dir / "images").write_text("not a dir", encoding="utf-8")
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert not outdir.exists()


def test_output_images_not_a_directory(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path, images={})
    outdir = tmp_path / "final"
    outdir.mkdir()
    (outdir / "images").write_text("not a dir", encoding="utf-8")

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1


def test_rejects_symlinked_outdir(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    real_dir = tmp_path / "real_outdir"
    real_dir.mkdir()
    marker = real_dir / "marker.txt"
    marker.write_text("keep", encoding="utf-8")

    symlink_outdir = tmp_path / "link_outdir"
    symlink_outdir.symlink_to(real_dir, target_is_directory=True)

    ret = build_final.main([str(normalized_dir), "-o", str(symlink_outdir)])

    assert ret == 1
    assert marker.read_text(encoding="utf-8") == "keep"
    assert not (real_dir / f"{BASE}.md").exists()


def test_rejects_symlinked_output_images(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"
    outdir.mkdir()

    real_images = tmp_path / "real_images"
    real_images.mkdir()
    kept_file = real_images / "keep.jpg"
    kept_file.write_bytes(b"keep")

    (outdir / "images").symlink_to(real_images, target_is_directory=True)

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1
    assert kept_file.is_file()
    assert kept_file.read_bytes() == b"keep"


# --- FR-003: 構築後検証 ------------------------------------------------------


def test_verify_detects_missing_image_ref(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n![](images/a.jpg)\n![](images/missing.jpg)\n",
        blocks=[{"type": "image", "img_path": "images/a.jpg", "page_idx": 0}],
        images={"a.jpg": b"AAA"},
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1


def test_verify_detects_img_path_mismatch(tmp_path: Path) -> None:
    # images/ に content_list の img_path にない画像がある（extra）
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n![](images/a.jpg)\n![](images/extra.jpg)\n",
        blocks=[{"type": "image", "img_path": "images/a.jpg", "page_idx": 0}],
        images={"a.jpg": b"AAA", "extra.jpg": b"EXTRA"},
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1


def test_verify_detects_img_path_missing(tmp_path: Path) -> None:
    # content_list にはあるが images/ に無い
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n![](images/a.jpg)\n",
        blocks=[
            {"type": "image", "img_path": "images/a.jpg", "page_idx": 0},
            {"type": "image", "img_path": "images/b.jpg", "page_idx": 0},
        ],
        images={"a.jpg": b"AAA"},
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 1


def test_md_without_image_refs_ok(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n図の参照なし\n",
        blocks=[{"type": "image", "img_path": "images/a.jpg", "page_idx": 0}],
        images={"a.jpg": b"AAA"},
    )
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0


# --- FR-004: 図 0 件の章 -----------------------------------------------------


def test_no_images_dir_creates_empty(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n図なし\n",
        blocks=[{"type": "text", "text": "本文"}],
        images={},
    )
    # images ディレクトリ自体を作らない
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0
    assert (outdir / "images").is_dir()
    assert list((outdir / "images").iterdir()) == []


def test_empty_images_dir_ok(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(
        tmp_path,
        md_text="# 本文\n\n図なし\n",
        blocks=[{"type": "text", "text": "本文"}],
        images={},
    )
    (normalized_dir / "images").mkdir()
    outdir = tmp_path / "final"

    ret = build_final.main([str(normalized_dir), "-o", str(outdir)])

    assert ret == 0
    assert (outdir / "images").is_dir()


# --- FR-006: 冪等性 ----------------------------------------------------------


def test_idempotent_rebuild(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"

    ret1 = build_final.main([str(normalized_dir), "-o", str(outdir)])
    assert ret1 == 0

    snapshot = {
        p.relative_to(outdir): p.read_bytes()
        for p in sorted(outdir.rglob("*"))
        if p.is_file()
    }

    ret2 = build_final.main([str(normalized_dir), "-o", str(outdir), "--overwrite"])
    assert ret2 == 0

    for rel, data in snapshot.items():
        assert (outdir / rel).read_bytes() == data


def test_orphan_image_removed(tmp_path: Path) -> None:
    normalized_dir = _make_normalized_dir(tmp_path)
    outdir = tmp_path / "final"
    outdir.mkdir()
    images_out = outdir / "images"
    images_out.mkdir()
    (images_out / "old_orphan.jpg").write_bytes(b"stale")

    ret = build_final.main([str(normalized_dir), "-o", str(outdir), "--overwrite"])

    assert ret == 0
    assert not (images_out / "old_orphan.jpg").exists()
    assert (images_out / "a.jpg").is_file()
