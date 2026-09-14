"""Run SegFormer inference on tile crops and save color-coded masks."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
from transformers import SegformerForSemanticSegmentation


ROOT = Path(__file__).resolve().parent.parent / "tile_library_z-man_2014"
IMAGE_SOURCE = ROOT / "crops"
MASK_DESTINATION = ROOT / "masks"

CHECKPOINT_CANDIDATES = [
    Path.cwd() / "best_carcassonne_model.pth",
    Path(__file__).resolve().parent / "best_carcassonne_model.pth",
    ROOT / "best_carcassonne_model.pth",
]

CLASS_COLORS_BGR = np.array(
    [
        [0, 0, 0],
        [80, 80, 178],
        [255, 221, 51],
        [61, 245, 61],
        [103, 157, 250],
        [83, 50, 250],
        [209, 240, 170],
        [183, 50, 250],
        [23, 102, 169],
    ],
    dtype=np.uint8,
)

ID_TO_LABEL = {
    0: "Background",
    1: "City",
    2: "Farm",
    3: "Field",
    4: "Garden",
    5: "Monastery",
    6: "Road",
    7: "RoadBlock",
    8: "Shield",
}


def find_checkpoint() -> Path:
    checkpoint = next(
        (path for path in CHECKPOINT_CANDIDATES if path.exists()),
        None,
    )
    if checkpoint is None:
        checked_paths = ", ".join(str(path) for path in CHECKPOINT_CANDIDATES)
        raise FileNotFoundError(f"Could not find model checkpoint. Checked: {checked_paths}")
    return checkpoint


def load_model(checkpoint_path: Path, device: torch.device):
    model = SegformerForSemanticSegmentation.from_pretrained(
        "nvidia/mit-b0",
        num_labels=9,
        id2label=ID_TO_LABEL,
        label2id={label: index for index, label in ID_TO_LABEL.items()},
        ignore_mismatched_sizes=True,
    )
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval()
    return model


def predict_mask(
    model,
    image_bgr: np.ndarray,
    device: torch.device,
    mean: torch.Tensor,
    std: torch.Tensor,
) -> np.ndarray:
    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(image_rgb, (256, 256), interpolation=cv2.INTER_LINEAR)
    image_tensor = torch.from_numpy(resized_rgb).permute(2, 0, 1).float() / 255.0
    image_tensor = image_tensor.unsqueeze(0).to(device)
    image_tensor = (image_tensor - mean) / std

    with torch.no_grad():
        outputs = model(pixel_values=image_tensor)
        # Match training: resize logits to 256x256 before taking argmax.
        logits = torch.nn.functional.interpolate(
            outputs.logits,
            size=(256, 256),
            mode="bilinear",
            align_corners=False,
        )

    class_mask = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype(np.uint8)
    if (height, width) != (256, 256):
        class_mask = cv2.resize(class_mask, (width, height), interpolation=cv2.INTER_NEAREST)
    return CLASS_COLORS_BGR[class_mask]


def main() -> None:
    checkpoint_path = find_checkpoint()
    MASK_DESTINATION.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        path
        for path in IMAGE_SOURCE.iterdir()
        if path.is_file()
        and path.name.startswith("IMG")
        and path.suffix == ".jpg"
    )
    if not image_paths:
        raise FileNotFoundError(f"No IMG*.jpg files found in {IMAGE_SOURCE}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(checkpoint_path, device)
    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(device)
    std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(device)

    processed = 0
    for image_path in image_paths:
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            print(f"Skipped unreadable image: {image_path.name}")
            continue

        mask = predict_mask(model, image_bgr, device, mean, std)
        output_path = MASK_DESTINATION / f"{image_path.stem}.png"
        if not cv2.imwrite(str(output_path), mask):
            raise IOError(f"Could not write mask: {output_path}")
        processed += 1
        print(f"Saved {output_path}")

    print(f"Loaded checkpoint: {checkpoint_path}")
    print(f"Processed {processed} images on {device}")
    print(f"Masks saved to: {MASK_DESTINATION}")


if __name__ == "__main__":
    main()
