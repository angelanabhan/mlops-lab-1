"""Validate a processed Food-11 dataset against its data contract."""

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from data import CLASSES  # pyright: ignore[reportMissingImports]

SPLITS = ("training", "validation", "evaluation")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def report(name: str, passed: bool) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"{status}: {name}")


def validate(dataset: Path, min_per_class: int, tau: float) -> bool:
    results = []

    folders_ok = all(
        split_path.is_dir()
        and {path.name for path in split_path.iterdir() if path.is_dir()}
        == set(CLASSES)
        for split in SPLITS
        if (split_path := dataset / split)
    )
    report("each split contains exactly the 11 class folders", folders_ok)
    results.append(folders_ok)

    counts = defaultdict(int)
    hashes = defaultdict(set)
    images_ok = True

    for split in SPLITS:
        for category in CLASSES:
            class_directory = dataset / split / category
            if not class_directory.is_dir():
                continue

            for path in class_directory.iterdir():
                if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                counts[(split, category)] += 1
                digest = hashlib.md5(path.read_bytes()).hexdigest()
                hashes[digest].add(split)

                try:
                    with Image.open(path) as image:
                        if image.mode != "RGB" or image.size != (128, 128):
                            images_ok = False
                except (OSError, UnidentifiedImageError):
                    images_ok = False

    report("every image is readable, RGB and 128x128", images_ok)
    results.append(images_ok)

    minimum_ok = all(
        counts[(split, category)] >= min_per_class
        for split in SPLITS
        for category in CLASSES
    )
    report(f"every class has at least {min_per_class} images", minimum_ok)
    results.append(minimum_ok)

    duplicates_ok = all(len(split_names) == 1 for split_names in hashes.values())
    report("no image appears in multiple splits", duplicates_ok)
    results.append(duplicates_ok)

    training_total = sum(counts[("training", category)] for category in CLASSES)
    validation_total = sum(counts[("validation", category)] for category in CLASSES)

    distribution_ok = training_total > 0 and validation_total > 0
    if distribution_ok:
        for category in CLASSES:
            training_share = counts[("training", category)] / training_total
            validation_share = counts[("validation", category)] / validation_total
            if abs(training_share - validation_share) > tau:
                distribution_ok = False

    report(f"training and validation class shares differ by at most {tau}", distribution_ok)
    results.append(distribution_ok)

    return all(results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)
    args = parser.parse_args()

    if not validate(args.dataset, args.min_per_class, args.tau):
        sys.exit(1)


if __name__ == "__main__":
    main()
