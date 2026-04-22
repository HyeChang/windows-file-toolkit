from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from file_compressor.zip_packages import rewrite_zip_package


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_rewrite_zip_package_preserves_non_media_entries():
    workdir = case_dir("zip-rewrite")
    source = workdir / "source.zip"
    output = workdir / "output.zip"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("doc.xml", "<doc />")
        archive.writestr("media/image.jpg", b"image-data")

    rewrite_zip_package(
        source,
        output,
        transform=lambda name, data: b"smaller" if name.endswith(".jpg") else data,
    )

    with ZipFile(output) as archive:
        assert archive.read("doc.xml") == b"<doc />"
        assert archive.read("media/image.jpg") == b"smaller"


def test_rewrite_zip_package_removes_partial_output_on_failure():
    workdir = case_dir("zip-rewrite-failure")
    source = workdir / "source.zip"
    output = workdir / "output.zip"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("doc.xml", "<doc />")

    def fail_transform(name: str, data: bytes) -> bytes:
        raise ValueError("boom")

    try:
        rewrite_zip_package(source, output, transform=fail_transform)
    except ValueError:
        pass

    assert not output.exists()
