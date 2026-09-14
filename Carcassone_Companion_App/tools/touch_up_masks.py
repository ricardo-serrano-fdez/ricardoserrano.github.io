"""Fill small enclosed background gaps in color segmentation masks.

Run from the Carcassonne_Companion_App directory. The original masks are
never modified; repaired masks are written to a separate directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


ROOT = Path("tile_library_z-man_2014")
DEFAULT_SOURCE = ROOT / "Segmentation_mask_09142026" / "SegmentationClass"
DEFAULT_DESTINATION = ROOT / "Segmentation_mask_09142026" / "SegmentationClass_touched_up"


PALETTE = {
    (0, 0, 0),
    (80, 80, 178),
    (255, 221, 51),
    (61, 245, 61),
    (103, 157, 250),
    (83, 50, 250),
    (209, 240, 170),
    (183, 50, 250),
    (23, 102, 169),
}
LABEL_COLORS = [color for color in PALETTE if color != (0, 0, 0)]


def fill_enclosed_gaps(mask: np.ndarray, max_hole_area: int) -> tuple[np.ndarray, int]:
    """Fill enclosed black components using the most common neighboring color."""
    background = np.all(mask == (0, 0, 0), axis=2).astype(np.uint8)
    component_count, components, stats, _ = cv2.connectedComponentsWithStats(
        background, connectivity=8
    )
    repaired = mask.copy()
    kernel = np.ones((3, 3), dtype=np.uint8)
    repaired_pixels = 0

    for component_id in range(1, component_count):
        x, y, width, height, area = stats[component_id]
        touches_border = (
            x == 0
            or y == 0
            or x + width == mask.shape[1]
            or y + height == mask.shape[0]
        )
        if touches_border or area > max_hole_area:
            continue

        component = components == component_id
        boundary = cv2.dilate(component.astype(np.uint8), kernel).astype(bool) & ~component
        boundary_colors = mask[boundary]
        boundary_colors = [tuple(int(channel) for channel in color) for color in boundary_colors]
        boundary_colors = [color for color in boundary_colors if color in PALETTE and color != (0, 0, 0)]
        if not boundary_colors:
            continue

        colors, counts = np.unique(np.array(boundary_colors), axis=0, return_counts=True)
        fill_color = colors[np.argmax(counts)]
        repaired[component] = fill_color
        repaired_pixels += int(area)

    return repaired, repaired_pixels


def fill_tile_interior_gaps(mask: np.ndarray, iterations: int = 12) -> tuple[np.ndarray, int]:
    """Fill small cracks inside the bounding box of the annotated tile."""
    labeled = np.any(mask != (0, 0, 0), axis=2)
    coordinates = np.argwhere(labeled)
    if coordinates.size == 0:
        return mask.copy(), 0

    top, left = coordinates.min(axis=0)
    bottom, right = coordinates.max(axis=0)
    interior = np.zeros(labeled.shape, dtype=bool)
    interior[top + 1:bottom, left + 1:right] = True
    repaired = mask.copy()
    kernel = np.ones((3, 3), dtype=np.uint8)
    repaired_pixels = 0

    for _ in range(iterations):
        label_ids = np.zeros(labeled.shape, dtype=np.uint8)
        for label_id, color in enumerate(LABEL_COLORS, start=1):
            label_ids[np.all(repaired == color, axis=2)] = label_id

        unlabeled = interior & (label_ids == 0)
        neighboring_labels = cv2.dilate((label_ids > 0).astype(np.uint8), kernel).astype(bool)
        candidates = unlabeled & neighboring_labels
        if not np.any(candidates):
            break

        counts = np.stack([
            cv2.filter2D((label_ids == label_id).astype(np.uint8), cv2.CV_16U, kernel)
            for label_id in range(1, len(LABEL_COLORS) + 1)
        ])
        best_labels = np.argmax(counts, axis=0) + 1
        repaired_before = np.count_nonzero(candidates)
        for label_id, color in enumerate(LABEL_COLORS, start=1):
            repaired[candidates & (best_labels == label_id)] = color
        repaired_pixels += int(repaired_before)

    return repaired, repaired_pixels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument(
        "--max-hole-area",
        type=int,
        default=5000,
        help="Maximum enclosed black component size to fill, in pixels.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_hole_area < 1:
        raise ValueError("--max-hole-area must be positive")
    if not args.source.is_dir():
        raise FileNotFoundError(f"Mask directory does not exist: {args.source}")

    args.destination.mkdir(parents=True, exist_ok=True)
    total_repaired = 0
    processed = 0

    for source in sorted(args.source.glob("*.png")):
        mask = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if mask is None:
            print(f"Skipped unreadable file: {source.name}")
            continue

        repaired, enclosed_pixels = fill_enclosed_gaps(mask, args.max_hole_area)
        repaired, interior_pixels = fill_tile_interior_gaps(repaired)
        repaired_pixels = enclosed_pixels + interior_pixels
        destination = args.destination / source.name
        if not cv2.imwrite(str(destination), repaired):
            raise IOError(f"Could not write repaired mask: {destination}")

        processed += 1
        total_repaired += repaired_pixels
        print(f"{source.name}: filled {repaired_pixels} pixels")

    print(f"Processed {processed} masks")
    print(f"Filled {total_repaired} pixels")
    print(f"Wrote repaired masks to {args.destination}")


if __name__ == "__main__":
    main()