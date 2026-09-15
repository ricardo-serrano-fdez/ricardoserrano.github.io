"""Tile catalog data provider and rendering utilities."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image

APP_ROOT = Path(__file__).resolve().parent
CATALOG_JSON_PATH = APP_ROOT / "carcassonne-zman-2014-catalog.json"
ANALYSIS_JSON_PATH = APP_ROOT / "tile_library_z-man_2014" / "tile_analysis.json"
CROPS_DIR = APP_ROOT / "tile_library_z-man_2014" / "crops"
MASKS_DIR = APP_ROOT / "tile_library_z-man_2014" / "masks"


def load_catalog() -> List[Dict[str, Any]]:
    """Load the base game tile catalog metadata."""
    if CATALOG_JSON_PATH.exists():
        with open(CATALOG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_analysis() -> Dict[str, Any]:
    """Load the extracted tile analysis results."""
    if ANALYSIS_JSON_PATH.exists():
        with open(ANALYSIS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {tile["id"]: tile for tile in data.get("tiles", [])}
    return {}


def get_crop_image(tile_id: str) -> Optional[Image.Image]:
    """Load cropped tile photo."""
    img_path = CROPS_DIR / f"{tile_id}.jpg"
    if img_path.exists():
        return Image.open(img_path).convert("RGB")
    return None


def get_mask_image(tile_id: str) -> Optional[Image.Image]:
    """Load segmentation mask image."""
    mask_path = MASKS_DIR / f"{tile_id}.png"
    if mask_path.exists():
        return Image.open(mask_path).convert("RGB")
    return None
