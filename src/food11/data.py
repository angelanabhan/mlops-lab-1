"""Prepare the Food-11 image files for training.

Reads the raw dataset at ``data/food11_raw`` (flat folders of ``<label>_<n>.jpg``
files, 512x512) and writes two derived datasets that match how ResNet expects an
image dataset to be laid out - one folder per class:

    data/food11_processed/<split>/<Category>/<label>_<n>.jpg      (all images)
    data/food11_processed_mini/<split>/<Category>/<label>_<n>.jpg (<=100 per class)

In both, images are resized to 128x128. The mini dataset is a tiny subset used
during development so we can check the algorithms are correct quickly.

Run with:
    uv run python ./src/food11/data.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Label index -> class name. The label is the first part of each raw file name,
# e.g. "3_87.jpg" is an "Egg" image.
CLASSES = [
    "Bread",            # 0
    "Dairy product",    # 1
    "Dessert",          # 2
    "Egg",              # 3
    "Fried food",       # 4
    "Meat",             # 5
    "Noodles-Pasta",    # 6
    "Rice",             # 7
    "Seafood",          # 8
    "Soup",             # 9
    "Vegetable-Fruit",  # 10
]

# Backward-compatible name used by the serving code.
CATEGORIES = CLASSES

SPLITS = ["training", "evaluation", "validation"]
IMAGE_SIZE = (128, 128)
MINI_PER_CATEGORY = 100

# Repo root, derived from this file's location (src/food11/data.py).
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "food11_raw"
PROCESSED_DIR = ROOT / "data" / "food11_processed"
MINI_DIR = ROOT / "data" / "food11_processed_mini"


def category_from_filename(filename: str) -> str:
    """Return the Food-11 category encoded in a filename."""
    label_text = Path(filename).name.split("_", 1)[0]
    if not label_text.isdigit():
        raise ValueError(f"Invalid Food-11 filename: {filename}")

    label = int(label_text)
    if not 0 <= label < len(CLASSES):
        raise ValueError(f"Invalid Food-11 label: {label}")

    return CLASSES[label]


def resize_image(img: Image.Image, size: int = 128) -> Image.Image:
    """Return an RGB square image resized to size x size."""
    return img.convert("RGB").resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )


def process_split(split: str) -> None:
    raw_split = RAW_DIR / split
    if not raw_split.is_dir():
        print(f"  skip {split!r}: {raw_split} not found")
        return

    files = sorted(p for p in raw_split.iterdir() if p.suffix.lower() == ".jpg")
    mini_counts = {name: 0 for name in CATEGORIES}
    written = mini_written = skipped = 0

    for i, src in enumerate(files, start=1):
        try:
            category = category_from_filename(src.name)
        except ValueError:
            skipped += 1
            continue

        with Image.open(src) as img:
            img = resize_image(img, IMAGE_SIZE[0])

            full_dst = PROCESSED_DIR / split / category / src.name
            full_dst.parent.mkdir(parents=True, exist_ok=True)
            img.save(full_dst, "JPEG", quality=90)
            written += 1

            if mini_counts[category] < MINI_PER_CATEGORY:
                mini_dst = MINI_DIR / split / category / src.name
                mini_dst.parent.mkdir(parents=True, exist_ok=True)
                img.save(mini_dst, "JPEG", quality=90)
                mini_counts[category] += 1
                mini_written += 1

        if i % 1000 == 0:
            print(f"  {split}: {i}/{len(files)}")

    print(
        f"  {split}: wrote {written} processed, {mini_written} mini"
        + (f", skipped {skipped} unrecognised" if skipped else "")
    )


def main() -> None:
    print(f"raw:       {RAW_DIR}")
    print(f"processed: {PROCESSED_DIR}")
    print(f"mini:      {MINI_DIR}")
    for split in SPLITS:
        process_split(split)
    print("done")


if __name__ == "__main__":
    main()
