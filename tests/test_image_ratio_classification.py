from pathlib import Path
from math import isclose

from PIL import Image

from file_compressor.image_ratio_classification import (
    MATCH_CATEGORY,
    MATCH_OUTPUT_FOLDER,
    ImageRatioOptions,
    apply_image_ratio_classification_plan,
    build_image_ratio_classification_plan,
)


def _make_image(path: Path, size: tuple[int, int]) -> None:
    image = Image.new("RGB", size, color=(30, 90, 160))
    image.save(path)


def test_only_matching_images_are_actionable_and_use_condition_folder(tmp_path: Path):
    wide = tmp_path / "wide.jpg"
    normal = tmp_path / "normal.jpg"
    _make_image(wide, (300, 100))
    _make_image(normal, (120, 100))

    plans = build_image_ratio_classification_plan(
        [wide, normal],
        None,
        ImageRatioOptions(direction="wide", threshold_ratio=2.0, operation="copy"),
    )

    assert plans[0].category == MATCH_CATEGORY
    assert plans[0].status == "ready"
    assert plans[0].target == tmp_path / MATCH_OUTPUT_FOLDER / "wide.jpg"
    assert plans[1].status == "skipped"
    assert plans[1].target == normal

    results = apply_image_ratio_classification_plan(plans)

    assert results[0].status == "completed"
    assert (tmp_path / MATCH_OUTPUT_FOLDER / "wide.jpg").exists()
    assert not (tmp_path / MATCH_OUTPUT_FOLDER / "normal.jpg").exists()
    assert normal.exists()


def test_matching_images_use_selected_output_folder_directly(tmp_path: Path):
    source = tmp_path / "source.jpg"
    output = tmp_path / "out"
    _make_image(source, (300, 100))

    plans = build_image_ratio_classification_plan(
        [source],
        output,
        ImageRatioOptions(direction="wide", threshold_ratio=2.0),
    )

    assert plans[0].target == output / "source.jpg"


def test_matching_images_reuse_existing_default_condition_folder(tmp_path: Path):
    source = tmp_path / "source.jpg"
    condition_folder = tmp_path / MATCH_OUTPUT_FOLDER
    condition_folder.mkdir()
    _make_image(source, (300, 100))

    plans = build_image_ratio_classification_plan(
        [source],
        None,
        ImageRatioOptions(direction="wide", threshold_ratio=2.0),
    )

    assert plans[0].target == condition_folder / "source.jpg"


def test_matching_images_inside_condition_folder_do_not_create_nested_condition_folder(tmp_path: Path):
    condition_folder = tmp_path / MATCH_OUTPUT_FOLDER
    condition_folder.mkdir()
    source = condition_folder / "source.jpg"
    _make_image(source, (300, 100))

    plans = build_image_ratio_classification_plan(
        [source],
        None,
        ImageRatioOptions(direction="wide", threshold_ratio=2.0),
    )

    assert plans[0].target == condition_folder / "source_2.jpg"
    assert MATCH_OUTPUT_FOLDER not in plans[0].target.relative_to(condition_folder).parts


def test_reference_ratio_can_match_portrait_images_wider_than_reference(tmp_path: Path):
    reference = tmp_path / "reference.jpg"
    wider_portrait = tmp_path / "wider_portrait.jpg"
    narrower_portrait = tmp_path / "narrower_portrait.jpg"
    _make_image(reference, (554, 1105))
    _make_image(wider_portrait, (690, 907))
    _make_image(narrower_portrait, (479, 1200))

    plans = build_image_ratio_classification_plan(
        [wider_portrait, narrower_portrait],
        None,
        ImageRatioOptions(
            direction="wide",
            reference_path=reference,
            reference_multiplier=1.10,
            operation="copy",
        ),
    )

    assert isclose(plans[0].threshold_ratio, (554 / 1105) * 1.10)
    assert isclose(plans[0].ratio, 690 / 907)
    assert plans[0].status == "ready"
    assert isclose(plans[1].ratio, 479 / 1200)
    assert plans[1].status == "skipped"
