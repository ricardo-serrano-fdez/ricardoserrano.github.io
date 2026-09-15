"""Computer vision analysis for Carcassonne board photos."""

from __future__ import annotations
import io
import math
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
from PIL import Image, ImageDraw
import cv2

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False


def load_image_from_bytes(file_bytes: bytes) -> Image.Image:
    """Open an image from bytes (PNG, JPEG, HEIC)."""
    return Image.open(io.BytesIO(file_bytes)).convert("RGB")


def compute_sobel_edges(image: Image.Image, max_dim: int = 700) -> Tuple[np.ndarray, Image.Image, float]:
    """Compute normalized Sobel edge strength map."""
    orig_w, orig_h = image.size
    scale = min(max_dim / max(orig_w, orig_h), 1.0)
    resized_w, resized_h = int(round(orig_w * scale)), int(round(orig_h * scale))
    resized_img = image.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
    
    np_img = np.array(resized_img)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.hypot(gx, gy)
    
    threshold = np.percentile(magnitude, 86)
    maximum = np.max(magnitude)
    if maximum <= threshold:
        maximum = threshold + 1e-5
        
    normalized = np.clip((magnitude - threshold) / (maximum - threshold), 0, 1)
    return normalized, resized_img, scale


def sample_edge(edge_map: np.ndarray, x: float, y: float) -> float:
    """Sample edge strength at float coordinates."""
    h, w = edge_map.shape
    rx, ry = int(round(x)), int(round(y))
    if 0 <= rx < w and 0 <= ry < h:
        return float(edge_map[ry, rx])
    return 0.0


def square_edge_score(edge_map: np.ndarray, cx: float, cy: float, size: float, angle_rad: float) -> float:
    """Calculate average edge alignment score along 4 square sides."""
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    half = size / 2.0
    
    def rot(px: float, py: float) -> Tuple[float, float]:
        return (cx + px * cos_a - py * sin_a, cy + px * sin_a + py * cos_a)
    
    corners = [rot(-half, -half), rot(half, -half), rot(half, half), rot(-half, half)]
    total_score, samples = 0.0, 24
    for side in range(4):
        p1, p2 = corners[side], corners[(side + 1) % 4]
        for s in range(samples):
            ratio = s / (samples - 1)
            total_score += sample_edge(edge_map, p1[0] + (p2[0] - p1[0]) * ratio, p1[1] + (p2[1] - p1[1]) * ratio)
            
    return total_score / (samples * 4)


def detect_reference_tile(edge_map: np.ndarray) -> Optional[Dict[str, Any]]:
    """Detect high-confidence square reference tile using Sobel edges."""
    h, w = edge_map.shape
    min_dim = min(w, h)
    best = None
    
    for size in np.linspace(min_dim * 0.10, min_dim * 0.28, 7):
        step_xy = max(20.0, size * 0.35)
        for y in np.arange(size, h - size, step_xy):
            for x in np.arange(size, w - size, step_xy):
                for deg in range(-20, 25, 10):
                    score = square_edge_score(edge_map, x, y, size, math.radians(deg))
                    if best is None or score > best["score"]:
                        best = {"x": x, "y": y, "size": size, "degrees": deg, "score": score}
                        
    if not best:
        return None
        
    rad = math.radians(best["degrees"])
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    half = best["size"] / 2.0
    
    def rot(px: float, py: float) -> Tuple[float, float]:
        return (best["x"] + px * cos_a - py * sin_a, best["y"] + px * sin_a + py * cos_a)
        
    points = [rot(-half, -half), rot(half, -half), rot(half, half), rot(-half, half)]
    return {
        "points": points,
        "confidence": float(best["score"]),
        "center": (best["x"], best["y"]),
        "size": best["size"],
        "degrees": best["degrees"]
    }


def draw_photo_overlay(
    image: Image.Image,
    edge_map: Optional[np.ndarray] = None,
    show_edges: bool = False,
    calibration_points: Optional[List[Tuple[float, float]]] = None,
    tiles: Optional[List[Dict[str, Any]]] = None,
) -> Image.Image:
    """Draw Sobel edges, calibration boundary and tile grid annotations."""
    img = image.copy()
    w, h = img.size
    
    if show_edges and edge_map is not None:
        colored_edge = np.zeros((h, w, 4), dtype=np.uint8)
        colored_edge[..., 0] = 46
        colored_edge[..., 1] = 102
        colored_edge[..., 2] = 82
        colored_edge[..., 3] = (edge_map * 180).astype(np.uint8)
        edge_pil = Image.fromarray(colored_edge, mode="RGBA")
        img = Image.alpha_composite(img.convert("RGBA"), edge_pil).convert("RGB")
        
    draw = ImageDraw.Draw(img)
    
    if calibration_points and len(calibration_points) == 4:
        poly_pts = [(float(p[0]), float(p[1])) for p in calibration_points]
        draw.polygon(poly_pts, outline="#2e6652", width=3)
        for i, (px, py) in enumerate(poly_pts, 1):
            draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill="#fffdf7", outline="#2e6652", width=2)
            draw.text((px - 3, py - 6), str(i), fill="#2e6652")
            
    if tiles:
        for i, t in enumerate(tiles, 1):
            tx, ty = t.get("x", 0), t.get("y", 0)
            draw.ellipse((tx - 9, ty - 9, tx + 9, ty + 9), fill="#ffd54f", outline="#614a00", width=2)
            draw.text((tx - 4, ty - 6), str(i), fill="#28281e")
            
    return img
