from io import BytesIO

from PIL import Image, ImageOps


SUPPORTED_CONTENT_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
}


def optimize_image_bytes(
    content_type: str,
    data: bytes,
    *,
    max_dimension: int = 1600,
    jpeg_quality: int = 78,
) -> bytes:
    image_format = SUPPORTED_CONTENT_TYPES.get(content_type.lower())
    if image_format is None:
        return data

    try:
        with Image.open(BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((max_dimension, max_dimension))

            output = BytesIO()
            if image_format == "JPEG":
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=jpeg_quality, optimize=True)
            else:
                image.save(output, format="PNG", optimize=True)

            optimized = output.getvalue()
            return optimized if len(optimized) < len(data) else data
    except Exception:
        return data
