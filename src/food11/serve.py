"""Serve the food11 champion model over a small FastAPI app."""

import io
import os

import mlflow
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms

from .data import CATEGORIES

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_URI = "models:/food11@champion"

# Must match the preprocessing used in training (src/food11/train.py).
TRANSFORM = transforms.Compose(
    [
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=(0.485, 0.456, 0.406),
            std=(0.229, 0.224, 0.225),
        ),
    ]
)

app = FastAPI(title="food11")
model = None


@app.on_event("startup")
def load_model():
    global model
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model = mlflow.pyfunc.load_model(MODEL_URI)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    input_tensor = TRANSFORM(image).unsqueeze(0)
    logits = model.predict(input_tensor.numpy())
    probabilities = torch.softmax(torch.from_numpy(logits), dim=1)[0]

    predicted_index = int(probabilities.argmax())
    return {
        "category": CATEGORIES[predicted_index],
        "confidence": float(probabilities[predicted_index]),
    }
