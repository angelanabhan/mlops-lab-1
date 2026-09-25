# Lab 3 Answers

## Question 1

The first registration of `food11` created **version 1**. My registry now contains versions 1 and 2, and the API currently uses **version 2**, which has the `champion` alias. A run's logged model contains the saved model files and metadata associated with training. Registering it creates a numbered version under a model name, with a reference to those artifacts and the source run. This allows me to manage deployment versions using aliases and tags.

## Question 2

Custom aliases such as `champion` and `challenger`, together with model version tags, replace the old fixed stages such as `Staging` and `Production`. These alias names are user-defined, not mandatory built-in stages. Runs record training parameters, metrics, and artifacts; registered versions identify models selected for deployment. An alias is flexible because I can move it to another version without changing the application's model URI. In my setup, `champion` points to version 2. [MLflow documentation](https://www.mlflow.org/docs/latest/ml/model-registry/workflow/)

## Question 3

Using `models:/food11@champion` lets MLflow resolve the registered version and load its saved model format, rather than tying the API to a particular `.pth` file path. To serve a newer model, I would register a new version, assign `champion` to it, and restart the API. My `serve.py` loads the model once at startup, so changing the alias does not replace the model already in memory. No API code change or image rebuild is needed if the new model uses compatible dependencies, preprocessing, and inputs and outputs.

## Question 4

Copying `pyproject.toml` and `uv.lock` before installing dependencies lets Docker cache dependency installation separately from the source code. If I change only `serve.py`, Docker can reuse the dependency layers and rebuild the `COPY src/` layer and subsequent steps. If all source files were copied before dependency installation, a source change would invalidate that installation layer too, making rebuilds slower. [Docker documentation](https://docs.docker.com/build/cache/)

## Question 5

I built a single-stage comparison image using `Dockerfile.single-stage`, with the same `python:3.10-slim` base, dependency installation commands, CPU PyTorch packages, and source code as the multi-stage build. It keeps the installation tools and project dependency files in the final image instead of copying only the virtual environment into a separate runtime stage.

Using `docker image ls food11-api`, I measured:

| Image | Build | Reported size |
| --- | --- | --- |
| `food11-api:single-stage` | Single-stage | **2.16 GB** |
| `food11-api:latest` | Multi-stage | **2.08 GB** |

The multi-stage image is approximately **0.08 GB (80 MB) smaller**, a reduction of about **3.7%** relative to the single-stage image. These calculations use Docker's rounded displayed sizes.

`docker history` shows that the largest single-stage layers are the CPU PyTorch installation (**755 MB**) and the other Python dependencies (**746 MB**). In the multi-stage image, these dependencies appear together in the copied virtual environment layer (**about 1.5 GB**). The single-stage image also retains the `uv`/`uvx` layer (**55.3 MB**) and dependency files (**1.05 MB**); the source layer is only **53.2 kB** in both images. The saving is modest because both builds already use a slim base and exclude the download cache through cache mounts, while both still require the large runtime dependencies. [Docker documentation](https://docs.docker.com/build/building/multi-stage/)

Commands used to build the comparison image and inspect both images:

```powershell
docker build -f Dockerfile.single-stage -t food11-api:single-stage .
docker image ls food11-api
docker history food11-api:single-stage
docker history food11-api:latest
```

## Question 6

Without `.dockerignore`, folders such as `data/`, `mlruns/`, and `.venv/` become eligible for inclusion in the build context, potentially increasing transfer and processing time. They also enlarge the final image if copied into it, for example with `COPY . .`. My Dockerfile copies only the dependency files and `src/`, so removing `.dockerignore` alone would not add all those folders to the image. None necessarily breaks the build merely by being sent to Docker. However, copying my Windows `.venv/` over the Linux virtual environment could break the application because its executables and paths are platform-specific. [Docker documentation](https://docs.docker.com/build/building/best-practices/)

## Question 7

With Docker's default networking, `127.0.0.1` inside a container refers to that container, not my Windows computer. Therefore, `127.0.0.1:5000` would look for MLflow inside the API container. Docker Desktop provides `host.docker.internal`, which resolves to the host's internal IP address. Setting `MLFLOW_TRACKING_URI=http://host.docker.internal:5000` lets the API reach MLflow on the host. The lab's Linux `--network host` example is different because it shares the host's network namespace. [Docker documentation](https://docs.docker.com/desktop/features/networking/networking-how-tos/)

## Question 8

Yes. In my earlier restart test, a new container created from `food11-api:latest` loaded the model without rebuilding the image. Testing `Bread/0_15.jpg` returned `{"category":"Bread","confidence":0.5084409713745117}`.

The image contains the API code and Python dependencies, while the model weights remain external. At startup, the API resolves `models:/food11@champion` through MLflow. In my setup, the registered artifact location is a Windows file URI, so the container reads the weights through a mounted host folder rather than downloading them over HTTP. Starting a new container therefore requires access to both MLflow and the mounted model files.

## Question 9

I still need to push the image to a container registry, such as Docker Hub or GitHub Container Registry, so another machine can pull it. I would give the image a release or Git commit tag and record its immutable digest to identify the exact image; a tag such as `latest` can change. The other machine also needs registry access, a compatible platform, and access to MLflow and the model artifacts. My local Windows artifact-folder mount must be replaced with storage accessible to that machine. To reproduce the exact model as well as the image, I would also record or pin the registered model version, because `champion` can later point to another version.
