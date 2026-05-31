from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import subprocess
from typing import Callable

from PIL import Image


JPEG_SUFFIXES = {".jpg", ".jpeg"}
LOSSLESS_RASTER_SUFFIXES = {".png", ".bmp"}
SUPPORTED_IMAGE_SUFFIXES = JPEG_SUFFIXES | LOSSLESS_RASTER_SUFFIXES
SUPPORTED_ANGLES = {90, 180, 270}


@dataclass(frozen=True)
class ImageRotationPlan:
    source: Path
    target: Path
    angle: int
    status: str
    message: str = ""
    jpegtran_executable: str | None = None
    allow_lossy_jpeg: bool = False


Runner = Callable[..., subprocess.CompletedProcess]


def build_image_rotation_plan(
    paths: list[Path],
    *,
    angle: int,
    output_folder: Path | None = None,
    jpegtran_executable: str | None = None,
    allow_lossy_jpeg: bool = False,
) -> list[ImageRotationPlan]:
    normalized_angle = _normalize_angle(angle)
    occupied: set[Path] = set()
    plans: list[ImageRotationPlan] = []
    for source in paths:
        source = Path(source)
        target = _rotation_target(source, output_folder)
        target = _unique_path(target, occupied)
        occupied.add(target)

        if not source.exists():
            plans.append(
                ImageRotationPlan(
                    source=source,
                    target=target,
                    angle=normalized_angle,
                    status="skipped",
                    message="Source file does not exist.",
                    jpegtran_executable=jpegtran_executable,
                    allow_lossy_jpeg=allow_lossy_jpeg,
                )
            )
            continue
        if source.is_dir():
            plans.append(
                ImageRotationPlan(
                    source=source,
                    target=target,
                    angle=normalized_angle,
                    status="skipped",
                    message="Folders cannot be rotated as images.",
                    jpegtran_executable=jpegtran_executable,
                    allow_lossy_jpeg=allow_lossy_jpeg,
                )
            )
            continue

        suffix = source.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_SUFFIXES:
            plans.append(
                ImageRotationPlan(
                    source=source,
                    target=target,
                    angle=normalized_angle,
                    status="skipped",
                    message="Unsupported image format.",
                    jpegtran_executable=jpegtran_executable,
                    allow_lossy_jpeg=allow_lossy_jpeg,
                )
            )
            continue

        if suffix in JPEG_SUFFIXES and not jpegtran_executable and not allow_lossy_jpeg:
            plans.append(
                ImageRotationPlan(
                    source=source,
                    target=target,
                    angle=normalized_angle,
                    status="skipped",
                    message="jpegtran is required for lossless JPEG rotation.",
                    jpegtran_executable=jpegtran_executable,
                    allow_lossy_jpeg=allow_lossy_jpeg,
                )
            )
            continue

        plans.append(
            ImageRotationPlan(
                source=source,
                target=target,
                angle=normalized_angle,
                status="ready",
                jpegtran_executable=jpegtran_executable,
                allow_lossy_jpeg=allow_lossy_jpeg,
            )
        )
    return plans


def apply_image_rotation_plan(
    plans: list[ImageRotationPlan],
    *,
    runner: Runner = subprocess.run,
) -> list[ImageRotationPlan]:
    results: list[ImageRotationPlan] = []
    for plan in plans:
        if plan.status != "ready":
            results.append(plan)
            continue
        if not plan.source.exists():
            results.append(replace(plan, status="failed", message="Source file does not exist."))
            continue
        if plan.target.exists():
            results.append(replace(plan, status="failed", message="Target file already exists."))
            continue

        try:
            plan.target.parent.mkdir(parents=True, exist_ok=True)
            if plan.source.suffix.lower() in JPEG_SUFFIXES:
                results.append(_apply_jpeg_rotation(plan, runner=runner))
            else:
                results.append(_apply_raster_rotation(plan))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
    return results


def _apply_raster_rotation(plan: ImageRotationPlan) -> ImageRotationPlan:
    with Image.open(plan.source) as image:
        rotated = image.transpose(_pillow_transpose(plan.angle))
        rotated.save(plan.target)
    return replace(plan, status="completed", message="Rotated.")


def _apply_jpeg_rotation(plan: ImageRotationPlan, *, runner: Runner) -> ImageRotationPlan:
    if not plan.jpegtran_executable:
        if plan.allow_lossy_jpeg:
            return _apply_lossy_jpeg_rotation(plan)
        return replace(plan, status="skipped", message="jpegtran is required for lossless JPEG rotation.")

    command = [
        plan.jpegtran_executable,
        "-copy",
        "all",
        "-perfect",
        "-rotate",
        str(plan.angle),
        "-outfile",
        str(plan.target),
        str(plan.source),
    ]
    completed = runner(command, check=False, capture_output=True, text=True)
    if completed.returncode == 0:
        return replace(plan, status="completed", message="Rotated.")

    if plan.target.exists():
        plan.target.unlink()
    message = (completed.stderr or completed.stdout or "JPEG cannot be rotated losslessly.").strip()
    if plan.allow_lossy_jpeg:
        return _apply_lossy_jpeg_rotation(plan)
    return replace(plan, status="skipped", message=message)


def _apply_lossy_jpeg_rotation(plan: ImageRotationPlan) -> ImageRotationPlan:
    with Image.open(plan.source) as image:
        exif = image.info.get("exif")
        rotated = image.transpose(_pillow_transpose(plan.angle))
        if rotated.mode not in ("RGB", "L"):
            rotated = rotated.convert("RGB")

        save_kwargs = {"quality": 95, "optimize": True}
        if exif:
            save_kwargs["exif"] = exif
        rotated.save(plan.target, format="JPEG", **save_kwargs)
    return replace(plan, status="completed", message="Rotated with JPEG re-encoding.")


def _pillow_transpose(angle: int) -> Image.Transpose:
    return {
        90: Image.Transpose.ROTATE_270,
        180: Image.Transpose.ROTATE_180,
        270: Image.Transpose.ROTATE_90,
    }[angle]


def _normalize_angle(angle: int) -> int:
    normalized = angle % 360
    if normalized not in SUPPORTED_ANGLES:
        raise ValueError("angle must be 90, 180, or 270 degrees")
    return normalized


def _rotation_target(source: Path, output_folder: Path | None) -> Path:
    folder = Path(output_folder) if output_folder is not None else source.parent
    return folder / f"{source.stem}_rotated{source.suffix}"


def _unique_path(path: Path, occupied: set[Path]) -> Path:
    candidate = path
    counter = 2
    while candidate.exists() or candidate in occupied:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        counter += 1
    return candidate
