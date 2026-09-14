"""Extract Carcassonne tile edges, terrain connections, and special features."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MASK_DIRECTORY = APP_ROOT / "tile_library_z-man_2014" / "masks"
DEFAULT_LABELMAP = DEFAULT_MASK_DIRECTORY / "labelmap.txt"
DEFAULT_OUTPUT = APP_ROOT / "tile_library_z-man_2014" / "tile_analysis.json"

CANONICAL_TERRAINS = ("city", "road", "field")
TERRAIN_ALIASES = {
    "City": "city",
    "Road": "road",
    "Field": "field",
    "Farm": "field",
}
SPECIAL_FEATURES = ("Monastery", "Shield", "Garden")


def parse_labelmap(path: Path) -> dict[str, tuple[int, int, int]]:
    colors: dict[str, tuple[int, int, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 2:
            continue
        name, rgb_text = parts[0].strip(), parts[1].strip()
        rgb = tuple(int(value.strip()) for value in rgb_text.split(","))
        if len(rgb) != 3:
            raise ValueError(f"Invalid RGB value for {name!r} in {path}")
        colors[name] = rgb  # type: ignore[assignment]
    return colors


def load_mask(path: Path, colors: dict[str, tuple[int, int, int]]) -> np.ndarray:
    image = np.asarray(Image.open(path).convert("RGB"))
    color_to_label = {rgb: label for label, rgb in colors.items()}
    labels = np.full(image.shape[:2], "Unknown", dtype=object)
    for rgb, label in color_to_label.items():
        labels[np.all(image == rgb, axis=2)] = label
    unknown = np.count_nonzero(labels == "Unknown")
    if unknown:
        raise ValueError(f"{path.name} contains {unknown} pixels not in the label map")
    return labels


def find_tile_box(labels: np.ndarray) -> tuple[int, int, int, int]:
    foreground = np.char.lower(labels.astype(str)) != "background"
    coordinates = np.argwhere(foreground)
    if coordinates.size == 0:
        raise ValueError("Mask has no labeled tile pixels")
    top, left = coordinates.min(axis=0)
    bottom, right = coordinates.max(axis=0)
    width = right - left + 1
    height = bottom - top + 1
    if abs(width - height) > max(4, round(max(width, height) * 0.05)):
        raise ValueError(f"Inferred tile box is not square: {(left, top, right, bottom)}")
    side = max(width, height)
    return int(left), int(top), int(left + side - 1), int(top + side - 1)


def canonical_label(label: str) -> str | None:
    return TERRAIN_ALIASES.get(label)


def classify_center(labels: np.ndarray, box: tuple[int, int, int, int]) -> str:
    left, top, right, bottom = box
    tile = labels[top : bottom + 1, left : right + 1]
    side = tile.shape[0]
    center = tile[side // 3 : 2 * side // 3, side // 3 : 2 * side // 3]
    terrain_counts = Counter(
        canonical_label(label)
        for label in center.reshape(-1)
        if canonical_label(label) is not None
    )
    return terrain_counts.most_common(1)[0][0] if terrain_counts else "unknown"


def segment_slices(side: int) -> list[tuple[str, slice, slice]]:
    third = side / 3
    return [
        ("top", slice(0, max(1, round(side * 0.08))), slice(round(third * 0), round(third * 1))),
        ("top", slice(0, max(1, round(side * 0.08))), slice(round(third * 1), round(third * 2))),
        ("top", slice(0, max(1, round(side * 0.08))), slice(round(third * 2), side)),
        ("right", slice(round(third * 0), round(third * 1)), slice(side - max(1, round(side * 0.08)), side)),
        ("right", slice(round(third * 1), round(third * 2)), slice(side - max(1, round(side * 0.08)), side)),
        ("right", slice(round(third * 2), side), slice(side - max(1, round(side * 0.08)), side)),
        ("bottom", slice(side - max(1, round(side * 0.08)), side), slice(round(third * 2), side)),
        ("bottom", slice(side - max(1, round(side * 0.08)), side), slice(round(third * 1), round(third * 2))),
        ("bottom", slice(side - max(1, round(side * 0.08)), side), slice(0, round(third * 1))),
        ("left", slice(round(third * 2), side), slice(0, max(1, round(side * 0.08)))),
        ("left", slice(round(third * 1), round(third * 2)), slice(0, max(1, round(side * 0.08)))),
        ("left", slice(0, round(third * 1)), slice(0, max(1, round(side * 0.08)))),
    ]


def classify_edges(labels: np.ndarray, box: tuple[int, int, int, int]) -> list[dict[str, Any]]:
    left, top, right, bottom = box
    tile = labels[top : bottom + 1, left : right + 1]
    result = []
    for number, (side_name, rows, columns) in enumerate(segment_slices(tile.shape[0]), start=1):
        sample = tile[rows, columns].reshape(-1)
        terrain_counts = Counter(
            canonical_label(label) for label in sample if canonical_label(label) is not None
        )
        if terrain_counts:
            if terrain_counts.get("road", 0) and not terrain_counts.get("city", 0):
                terrain = "road"
            else:
                terrain = terrain_counts.most_common(1)[0][0]
            confidence = terrain_counts[terrain] / sum(terrain_counts.values())
        else:
            terrain = "unknown"
            confidence = 0.0
        result.append(
            {
                "segment": number,
                "side": side_name,
                "terrain": terrain,
                "confidence": round(confidence, 4),
                "raw_labels": dict(Counter(str(label) for label in sample if label != "Background")),
            }
        )
    return result


def terrain_components(
    labels: np.ndarray,
    box: tuple[int, int, int, int],
    edge_data: list[dict[str, Any]],
    min_area: int,
    closing_radius: int,
    center_terrain: str,
) -> list[dict[str, Any]]:
    left, top, right, bottom = box
    tile = labels[top : bottom + 1, left : right + 1]
    all_components: list[dict[str, Any]] = []
    kernel_size = max(1, closing_radius * 2 + 1)
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)

    for terrain in CANONICAL_TERRAINS:
        terrain_mask = np.zeros(tile.shape, dtype=np.uint8)
        for label, canonical in TERRAIN_ALIASES.items():
            if canonical == terrain:
                terrain_mask[labels[top : bottom + 1, left : right + 1] == label] = 1
        if closing_radius:
            terrain_mask = cv2.morphologyEx(terrain_mask, cv2.MORPH_CLOSE, kernel)
        count, component_map, stats, centroids = cv2.connectedComponentsWithStats(terrain_mask, 8)
        for component_id in range(1, count):
            area = int(stats[component_id, cv2.CC_STAT_AREA])
            if area < min_area:
                continue
            component = component_map == component_id
            touched_segments = []
            for edge in edge_data:
                if edge["terrain"] != terrain:
                    continue
                for segment_number, (_, rows, columns) in enumerate(segment_slices(tile.shape[0]), start=1):
                    if segment_number == edge["segment"] and np.any(component[rows, columns]):
                        touched_segments.append(segment_number)
            all_components.append(
                {
                    "terrain": terrain,
                    "area_pixels": area,
                    "centroid": [round(float(centroids[component_id][0]), 2), round(float(centroids[component_id][1]), 2)],
                    "edge_segments": sorted(set(touched_segments)),
                }
            )
    city_edge_records = [
        component
        for component in all_components
        if component["terrain"] == "city" and component["edge_segments"]
    ]
    city_edge_segments = [edge for edge in edge_data if edge["terrain"] == "city"]
    if city_edge_records and city_edge_segments and center_terrain in {"city", "field"}:
        if center_terrain == "city":
            groups = [city_edge_segments]
        else:
            groups = [
                [edge for edge in city_edge_segments if edge["side"] == side_name]
                for side_name in ("top", "right", "bottom", "left")
            ]
            groups = [group for group in groups if group]

        retained = [component for component in all_components if component not in city_edge_records]
        for group in groups:
            segments = sorted(edge["segment"] for edge in group)
            matching = [
                component
                for component in city_edge_records
                if set(component["edge_segments"]) & set(segments)
            ]
            area = sum(component["area_pixels"] for component in matching)
            total_area = max(1, area)
            centroid = [
                round(
                    sum(component["centroid"][axis] * component["area_pixels"] for component in matching)
                    / total_area,
                    2,
                )
                for axis in (0, 1)
            ]
            retained.append(
                {
                    "terrain": "city",
                    "area_pixels": area,
                    "centroid": centroid,
                    "edge_segments": segments,
                }
            )
        all_components = retained
    return all_components


def analyze_mask(
    path: Path,
    colors: dict[str, tuple[int, int, int]],
    min_component_area: int,
    closing_radius: int,
) -> dict[str, Any]:
    labels = load_mask(path, colors)
    box = find_tile_box(labels)
    center_terrain = classify_center(labels, box)
    edge_data = classify_edges(labels, box)
    features = {
        feature.lower(): bool(np.any(labels == feature)) for feature in SPECIAL_FEATURES
    }
    features["roadblock"] = bool(np.any(labels == "RoadBlock"))
    return {
        "id": path.stem,
        "source": path.name,
        "mask_size": [int(labels.shape[1]), int(labels.shape[0])],
        "tile_box": list(box),
        "center_terrain": center_terrain,
        "edges": edge_data,
        "connections": terrain_components(
            labels, box, edge_data, min_component_area, closing_radius, center_terrain
        ),
        "features": features,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_MASK_DIRECTORY)
    parser.add_argument("--labelmap", type=Path, default=DEFAULT_LABELMAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-component-area", type=int, default=100)
    parser.add_argument("--closing-radius", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.source.is_dir():
        raise FileNotFoundError(f"Mask directory does not exist: {args.source}")
    if args.min_component_area < 1 or args.closing_radius < 0:
        raise ValueError("Component area must be positive and closing radius cannot be negative")

    colors = parse_labelmap(args.labelmap)
    masks = sorted(args.source.glob("IMG_*.png"))
    if not masks:
        raise FileNotFoundError(f"No IMG_*.png masks found in {args.source}")

    tiles = []
    for mask_path in masks:
        try:
            tiles.append(
                analyze_mask(mask_path, colors, args.min_component_area, args.closing_radius)
            )
        except (OSError, ValueError) as error:
            raise ValueError(f"Could not analyze {mask_path.name}: {error}") from error

    output = {
        "schema_version": 1,
        "terrain_labels": list(CANONICAL_TERRAINS),
        "edge_numbering": "1 top-left, then clockwise; 3 segments per side",
        "raw_to_canonical": TERRAIN_ALIASES,
        "tiles": tiles,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(output, indent=2)
    args.output.write_text(serialized, encoding="utf-8")
    script_output = args.output.with_suffix(".js")
    script_output.write_text(f"window.tileAnalysis = {serialized};\n", encoding="utf-8")
    print(f"Analyzed {len(tiles)} masks")
    print(f"Wrote {args.output}")
    print(f"Wrote {script_output}")


if __name__ == "__main__":
    main()