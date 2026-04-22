from io import BytesIO

from PIL import Image

from file_compressor.images import optimize_image_bytes


def make_image(format_name: str, size=(2000, 1200)) -> bytes:
    image = Image.new("RGB", size, color=(220, 20, 60))
    buffer = BytesIO()
    image.save(buffer, format=format_name)
    return buffer.getvalue()


def test_optimize_jpeg_reduces_large_image_dimensions():
    original = make_image("JPEG")

    optimized = optimize_image_bytes("image/jpeg", original, max_dimension=800, jpeg_quality=75)

    result = Image.open(BytesIO(optimized))
    assert max(result.size) <= 800
    assert len(optimized) < len(original)


def test_optimize_returns_original_when_format_is_unknown():
    original = b"not an image"

    optimized = optimize_image_bytes("application/octet-stream", original)

    assert optimized == original
