"""Create square reference crops from white-background tile photos.

Run from the project root after HEIC images have been converted to JPEGs in
tile_library_z-man_2014/derived-jpeg.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path("tile_library_z-man_2014")
SOURCE = ROOT / "derived-jpeg"
DESTINATION = ROOT / "crops"


def crop_tile(image: np.ndarray) -> tuple[np.ndarray, list[int]]:
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # The tile artwork is more saturated/darker than the neutral white backdrop.
    mask = cv2.inRange(hsv, np.array([0, 35, 0]), np.array([180, 255, 245]))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = np.array([width / 2, height / 2])
    choices = []
    for contour in contours:
        x, y, box_width, box_height = cv2.boundingRect(contour)
        area = box_width * box_height
        if area < 400:
            continue
        distance = np.linalg.norm(np.array([x + box_width / 2, y + box_height / 2]) - center)
        choices.append((distance - area / 2000, x, y, box_width, box_height))
    if not choices:
        raise ValueError("Could not isolate a tile")
    _, x, y, box_width, box_height = min(choices)
    side = int(max(box_width, box_height) * 1.34)
    left = max(0, int(x + box_width / 2 - side / 2))
    top = max(0, int(y + box_height / 2 - side / 2))
    right = min(width, left + side)
    bottom = min(height, top + side)
    # Keep the output square even when a crop reaches a photograph edge.
    crop = image[top:bottom, left:right]
    crop = cv2.copyMakeBorder(
        crop,
        0,
        side - crop.shape[0],
        0,
        side - crop.shape[1],
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )
    return cv2.resize(crop, (512, 512), interpolation=cv2.INTER_AREA), [left, top, right, bottom]


def main() -> None:
    DESTINATION.mkdir(exist_ok=True)
    catalog = []
    for source in sorted(SOURCE.glob("IMG_*.jpg")):
        image = cv2.imread(str(source))
        if image is None:
            continue
        crop, bounds = crop_tile(image)
        destination = DESTINATION / source.name
        cv2.imwrite(str(destination), crop, [cv2.IMWRITE_JPEG_QUALITY, 94])
        catalog.append({"id": source.stem, "source": str(source), "image": str(destination), "cropBounds": bounds})
    (DESTINATION / "catalog-draft.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Created {len(catalog)} tile crops in {DESTINATION}")


if __name__ == "__main__":
    main()
