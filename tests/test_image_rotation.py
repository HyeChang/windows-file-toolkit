from pathlib import Path
import shutil
import subprocess

from PIL import Image

from file_compressor.image_rotation import (
    apply_image_rotation_plan,
    build_image_rotation_plan,
)


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_png_rotation_writes_rotated_copy_without_changing_source():
    workdir = case_dir("image-rotate-png")
    source = workdir / "sample.png"
    Image.new("RGB", (3, 2), "red").save(source)

    [plan] = build_image_rotation_plan([source], angle=90)
    results = apply_image_rotation_plan([plan])

    assert plan.status == "ready"
    assert plan.target == workdir / "sample_rotated.png"
    assert results[0].status == "completed"
    assert source.exists()
    assert plan.target.exists()
    with Image.open(source) as original:
        assert original.size == (3, 2)
    with Image.open(plan.target) as rotated:
        assert rotated.size == (2, 3)


def test_jpeg_rotation_skips_without_lossless_rotation_tool():
    workdir = case_dir("image-rotate-jpeg-missing-tool")
    source = workdir / "photo.jpg"
    Image.new("RGB", (8, 8), "blue").save(source, format="JPEG")

    [plan] = build_image_rotation_plan([source], angle=90, jpegtran_executable=None)
    results = apply_image_rotation_plan([plan])

    assert plan.status == "skipped"
    assert "jpegtran" in plan.message
    assert results[0] == plan
    assert not (workdir / "photo_rotated.jpg").exists()


def test_jpeg_rotation_uses_jpegtran_with_perfect_lossless_transform():
    workdir = case_dir("image-rotate-jpeg-jpegtran")
    source = workdir / "photo.jpg"
    source.write_bytes(b"jpeg")
    calls: list[list[str]] = []

    def fake_runner(command, **kwargs):
        calls.append(command)
        Path(command[command.index("-outfile") + 1]).write_bytes(b"rotated")
        return subprocess.CompletedProcess(command, 0, "", "")

    [plan] = build_image_rotation_plan(
        [source],
        angle=270,
        jpegtran_executable="C:/Tools/jpegtran.exe",
    )
    [result] = apply_image_rotation_plan([plan], runner=fake_runner)

    assert result.status == "completed"
    assert result.target.read_bytes() == b"rotated"
    assert calls == [
        [
            "C:/Tools/jpegtran.exe",
            "-copy",
            "all",
            "-perfect",
            "-rotate",
            "270",
            "-outfile",
            str(result.target),
            str(source),
        ]
    ]


def test_jpeg_rotation_skips_when_jpegtran_cannot_rotate_perfectly():
    workdir = case_dir("image-rotate-jpeg-imperfect")
    source = workdir / "photo.jpg"
    source.write_bytes(b"jpeg")

    def fake_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "not perfect")

    [plan] = build_image_rotation_plan(
        [source],
        angle=90,
        jpegtran_executable="jpegtran",
    )
    [result] = apply_image_rotation_plan([plan], runner=fake_runner)

    assert result.status == "skipped"
    assert "not perfect" in result.message
    assert not result.target.exists()


def test_jpeg_rotation_can_fall_back_to_lossy_rotation_when_allowed():
    workdir = case_dir("image-rotate-jpeg-lossy-fallback")
    source = workdir / "photo.jpg"
    Image.new("RGB", (9, 7), "blue").save(source, format="JPEG")

    def fake_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, "", "not perfect")

    [plan] = build_image_rotation_plan(
        [source],
        angle=90,
        jpegtran_executable="jpegtran",
        allow_lossy_jpeg=True,
    )
    [result] = apply_image_rotation_plan([plan], runner=fake_runner)

    assert result.status == "completed"
    assert "re-encoding" in result.message
    with Image.open(result.target) as rotated:
        assert rotated.size == (7, 9)


def test_jpeg_rotation_can_use_lossy_rotation_without_jpegtran_when_allowed():
    workdir = case_dir("image-rotate-jpeg-lossy-without-tool")
    source = workdir / "photo.jpg"
    Image.new("RGB", (11, 7), "blue").save(source, format="JPEG")

    [plan] = build_image_rotation_plan(
        [source],
        angle=270,
        jpegtran_executable=None,
        allow_lossy_jpeg=True,
    )
    [result] = apply_image_rotation_plan([plan])

    assert plan.status == "ready"
    assert result.status == "completed"
    assert "re-encoding" in result.message
    with Image.open(result.target) as rotated:
        assert rotated.size == (7, 11)


def test_unsupported_image_rotation_skips():
    workdir = case_dir("image-rotate-unsupported")
    source = workdir / "animation.gif"
    source.write_bytes(b"gif")

    [plan] = build_image_rotation_plan([source], angle=90)

    assert plan.status == "skipped"
    assert "Unsupported" in plan.message


def test_invalid_image_rotation_reports_failure_without_raising():
    workdir = case_dir("image-rotate-invalid")
    source = workdir / "broken.png"
    source.write_bytes(b"not an image")

    [plan] = build_image_rotation_plan([source], angle=90)
    [result] = apply_image_rotation_plan([plan])

    assert result.status == "failed"
    assert result.message
    assert not result.target.exists()
