"""Train Food-11 with a pretrained ResNet-18 and track runs in MLflow."""

import argparse
import random
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


ROOT = Path(__file__).resolve().parents[2]
DATA_DIRS = {
    "mini": ROOT / "data" / "food11_processed_mini",
    "processed": ROOT / "data" / "food11_processed",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Train a Food-11 classifier")
    parser.add_argument("--dataset", choices=["mini", "processed"], default="mini")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    if args.epochs < 1 or args.lr <= 0 or args.batch_size < 1:
        parser.error("epochs, lr, and batch-size must be positive")
    return args


def make_loaders(dataset_name, batch_size, use_cuda):
    data_dir = DATA_DIRS[dataset_name]
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Dataset not found: {data_dir}")

    # Lab 1 already resized the images to 128×128.
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225),
            ),
        ]
    )

    train_data = datasets.ImageFolder(data_dir / "training", transform=transform)
    val_data = datasets.ImageFolder(data_dir / "validation", transform=transform)
    test_data = datasets.ImageFolder(data_dir / "evaluation", transform=transform)

    if len(train_data.classes) != 11:
        raise ValueError("Expected 11 Food-11 classes")
    if train_data.classes != val_data.classes or train_data.classes != test_data.classes:
        raise ValueError("Class names differ between dataset splits")

    def loader(data, shuffle):
        return DataLoader(
            data,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=0,
            pin_memory=use_cuda,
        )

    return (
        loader(train_data, shuffle=True),
        loader(val_data, shuffle=False),
        loader(test_data, shuffle=False),
    )


def make_model(device):
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # Train the new classifier head while keeping pretrained features fixed.
    for parameter in model.parameters():
        parameter.requires_grad = False

    model.fc = nn.Linear(model.fc.in_features, 11)
    return model.to(device)


def train_one_epoch(model, loader, loss_fn, optimizer, device):
    # Keep the frozen backbone's batch-normalization statistics unchanged.
    model.eval()

    total_loss = 0.0
    total_images = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        predictions = model(images)
        loss = loss_fn(predictions, labels)
        loss.backward()
        optimizer.step()

        count = labels.size(0)
        total_loss += loss.item() * count
        total_images += count

    return total_loss / total_images


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()

    total_loss = 0.0
    correct = 0
    total_images = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        predictions = model(images)
        loss = loss_fn(predictions, labels)

        count = labels.size(0)
        total_loss += loss.item() * count
        correct += (predictions.argmax(dim=1) == labels).sum().item()
        total_images += count

    return total_loss / total_images, correct / total_images


def main():
    args = parse_args()
    random.seed(42)
    torch.manual_seed(42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("food11")

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "dataset": args.dataset,
                "epochs": args.epochs,
                "lr": args.lr,
                "batch_size": args.batch_size,
                "architecture": "resnet18",
                "pretrained": True,
                "trained_layer": "fc",
                "seed": 42,
            }
        )

        train_loader, val_loader, test_loader = make_loaders(
            args.dataset, args.batch_size, device.type == "cuda"
        )
        model = make_model(device)
        loss_fn = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.fc.parameters(), lr=args.lr)

        print(f"Run ID: {run.info.run_id} | Device: {device}")

        for epoch in range(1, args.epochs + 1):
            train_loss = train_one_epoch(
                model, train_loader, loss_fn, optimizer, device
            )
            val_loss, val_accuracy = evaluate(model, val_loader, loss_fn, device)

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_accuracy", val_accuracy, step=epoch)

            print(
                f"Epoch {epoch}/{args.epochs}: "
                f"train_loss={train_loss:.4f}, "
                f"val_loss={val_loss:.4f}, "
                f"val_accuracy={val_accuracy:.4f}"
            )

        _, test_accuracy = evaluate(model, test_loader, loss_fn, device)
        mlflow.log_metric("test_accuracy", test_accuracy)

        # MLflow 3 recommends `name`; `artifact_path` is deprecated.
        model_info = mlflow.pytorch.log_model(
            model.cpu(), name="model", serialization_format="pickle"
        )

        print(f"Test accuracy: {test_accuracy:.4f}")
        print(f"Model URI: {model_info.model_uri}")


if __name__ == "__main__":
    main()