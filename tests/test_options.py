from file_compressor.models import COMPRESSION_LEVEL_PRESETS, CompressionOptions


def test_default_compression_options_are_balanced():
    options = CompressionOptions()

    assert options.max_image_dimension == 1600
    assert options.jpeg_quality == 78
    assert options.pdf_preset == "screen"


def test_compression_options_can_keep_original_image_dimensions():
    options = CompressionOptions(max_image_dimension=None)

    assert options.max_image_dimension is None


def test_compression_level_presets_map_to_detailed_options():
    assert list(COMPRESSION_LEVEL_PRESETS) == ["high_quality", "balanced", "maximum"]
    assert COMPRESSION_LEVEL_PRESETS["high_quality"] == CompressionOptions(
        max_image_dimension=None,
        jpeg_quality=90,
        pdf_preset="printer",
    )
    assert COMPRESSION_LEVEL_PRESETS["balanced"] == CompressionOptions()
    assert COMPRESSION_LEVEL_PRESETS["maximum"] == CompressionOptions(
        max_image_dimension=800,
        jpeg_quality=50,
        pdf_preset="screen",
    )
