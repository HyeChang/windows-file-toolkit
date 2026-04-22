from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from file_compressor.compressors.package import compress_zip_document
from file_compressor.models import CompressionOptions, JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_jpeg() -> bytes:
    image = Image.new("RGB", (2000, 1200), color=(0, 80, 180))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_compress_zip_document_writes_output_and_preserves_entries():
    workdir = case_dir("package-compressor")
    source = workdir / "deck.pptx"
    output = workdir / "deck_compressed.pptx"
    original_image = make_jpeg()
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("ppt/media/image1.jpeg", original_image)

    result = compress_zip_document(source, output)

    assert result.status is JobStatus.COMPLETED
    assert result.output == output
    assert output.exists()
    with ZipFile(output) as archive:
        assert archive.read("[Content_Types].xml") == b"<Types />"
        assert len(archive.read("ppt/media/image1.jpeg")) < len(original_image)


def test_compress_zip_document_passes_image_options(monkeypatch):
    workdir = case_dir("package-options")
    source = workdir / "deck.pptx"
    output = workdir / "deck_compressed.pptx"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("ppt/media/image1.jpeg", b"image")
    calls = []

    def fake_optimize(content_type, data, *, max_dimension, jpeg_quality):
        calls.append((content_type, data, max_dimension, jpeg_quality))
        return b"optimized"

    monkeypatch.setattr("file_compressor.compressors.package.optimize_image_bytes", fake_optimize)

    compress_zip_document(
        source,
        output,
        options=CompressionOptions(max_image_dimension=800, jpeg_quality=50),
    )

    assert calls == [("image/jpeg", b"image", 800, 50)]
