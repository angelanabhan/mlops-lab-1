"""Promote a model version only when it passes an accuracy quality gate."""

import argparse
import math
import os
from pathlib import Path

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "food11"
METRIC_NAME = "test_accuracy"
DEFAULT_TRACKING_URI = "http://127.0.0.1:5000"
DEFAULT_TEST_DATA = Path("data/food11_processed/evaluation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the quality gate to a registered model version."
    )
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--test-data", type=Path, default=DEFAULT_TEST_DATA)
    return parser.parse_args()
def count_test_images(test_data: Path) -> int:
    extensions = {".jpg", ".jpeg", ".png"}
    count = sum(
        1
        for path in test_data.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    )
    if count == 0:
        raise ValueError(f"No test images found under {test_data}")
    return count


def get_accuracy(client: MlflowClient, version: int) -> float:
    model_version = client.get_model_version(MODEL_NAME, str(version))
    if not model_version.run_id:
        raise ValueError(f"Model version {version} has no associated run")

    metrics = client.get_run(model_version.run_id).data.metrics
    if METRIC_NAME not in metrics:
        raise ValueError(
            f"Run for model version {version} has no {METRIC_NAME!r} metric"
        )

    return metrics[METRIC_NAME]
def main() -> None:
    args = parse_args()

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
    champion_version = int(champion.version)

    candidate_accuracy = get_accuracy(client, args.version)
    champion_accuracy = get_accuracy(client, champion_version)
    test_size = count_test_images(args.test_data)

    if not 0.0 <= champion_accuracy <= 1.0:
        raise ValueError("Champion accuracy must be between 0 and 1")

    standard_error = math.sqrt(
        champion_accuracy * (1.0 - champion_accuracy) / test_size
    )
    threshold = champion_accuracy + 2 * standard_error

    if candidate_accuracy >= threshold:
        decision = "promoted"
        client.set_registered_model_alias(
            MODEL_NAME,
            "champion",
            str(args.version),
        )
    else:
        decision = "challenger"
        client.set_registered_model_alias(
            MODEL_NAME,
            "challenger",
            str(args.version),
        )

    tags = {
        "promotion_decision": decision,
        "candidate_accuracy": str(candidate_accuracy),
        "champion_accuracy": str(champion_accuracy),
        "promotion_threshold": str(threshold),
    }

    for key, value in tags.items():
        client.set_model_version_tag(
            MODEL_NAME,
            str(args.version),
            key,
            value,
        )

    print(f"Candidate version: {args.version}")
    print(f"Champion version: {champion_version}")
    print(f"Test size: {test_size}")
    print(f"Candidate accuracy: {candidate_accuracy:.4f}")
    print(f"Champion accuracy: {champion_accuracy:.4f}")
    print(f"Two standard errors: {2 * standard_error:.4f}")
    print(f"Required accuracy: {threshold:.4f}")
    print(f"Decision: {decision}")


if __name__ == "__main__":
    main()
    