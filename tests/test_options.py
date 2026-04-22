from file_compressor.models import CompressionOptions


def test_default_compression_options_are_balanced():
    options = CompressionOptions()

    assert options.max_image_dimension == 1600
    assert options.jpeg_quality == 78
    assert options.pdf_preset == "screen"


def test_compression_options_can_keep_original_image_dimensions():
    options = CompressionOptions(max_image_dimension=None)

    assert options.max_image_dimension is None
