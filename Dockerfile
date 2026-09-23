# syntax=docker/dockerfile:1

FROM python:3.10-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

ENV UV_HTTP_TIMEOUT=300 \
    UV_HTTP_RETRIES=10

# The lock pins CUDA-enabled PyTorch for local training. Keep the reproducible
# locked environment, but omit GPU-only packages from this CPU serving image.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project \
    --no-install-package torch --no-install-package torchvision \
    --no-install-package triton --no-install-package cuda-bindings \
    --no-install-package nvidia-cublas --no-install-package nvidia-cuda-cupti \
    --no-install-package nvidia-cuda-nvrtc --no-install-package nvidia-cuda-runtime \
    --no-install-package nvidia-cudnn-cu13 --no-install-package nvidia-cufft \
    --no-install-package nvidia-cufile --no-install-package nvidia-curand \
    --no-install-package nvidia-cusolver --no-install-package nvidia-cusparse \
    --no-install-package nvidia-cusparselt-cu13 --no-install-package nvidia-nccl-cu13 \
    --no-install-package nvidia-nvjitlink --no-install-package nvidia-nvshmem-cu13
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

FROM python:3.10-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["uvicorn", "src.food11.serve:app", "--host", "0.0.0.0", "--port", "8000"]
