# Lab 4 - Orchestrating the app with Docker Compose

> This project uses MLflow's current `champion` alias instead of the deprecated
> `Staging` stage named in the lab instructions.

**Question 1:** Without a volume, files written under `/mlflow-data` live only in
the container's writable layer. They remain if that same container is merely
stopped and restarted, but they disappear when the container is removed. A new
container created from the image starts with an empty MLflow database and UI.

**Question 2:** A named volume is managed by Docker, is independent of the repo's
host path, and persists when Compose recreates containers. It also avoids common
host permission and cross-platform filesystem issues. A bind mount would work,
and can be useful during local development when the files need to be inspected
directly, but it couples the stack to a particular host directory.

**Question 3:** Docker Compose creates a private network and provides embedded
DNS for its services. On that network, the name `mlflow` resolves to the MLflow
container, so inference can use `http://mlflow:5000`. In Lab 3, MLflow ran on the
host rather than the container network, so `mlflow` was not a resolvable service
name and the container needed `host.docker.internal` instead.

**Question 4:** Reading `INFERENCE_URL` from an environment variable keeps the
frontend usable in different environments. Compose sets it to
`http://inference:8000`, while a standalone frontend can use the default
`http://127.0.0.1:8000` or another URL without changing or rebuilding the code.

**Question 5:** Inference does not publish port 8000 because a person does not
need to access it directly in this architecture. The frontend reaches it over
the private Compose network using `http://inference:8000`, where Compose DNS
resolves `inference` to the correct container. Only MLflow on port 5000 and the
frontend on port 8501 are published to the host.

**Question 6:** `depends_on` starts the MLflow container before inference, but it
does not wait until the tracking server is ready. If inference tries to load the
model too early, its startup handler raises a connection error, Uvicorn reports
that application startup failed, and the inference container exits. Once MLflow
is ready, starting or restarting inference lets it load the model successfully.

**Question 7:** `docker compose ps` showed host mappings for MLflow
(`5000:5000`) and the frontend (`8501:8501`). Inference showed only `8000/tcp`,
with no host mapping. This matches `docker-compose.yml`: browser-facing services
publish ports, while service-to-service inference traffic stays on the Compose
network.

**Question 8:** I re-registered the same model as version 2 and moved the
`champion` alias to it. Refreshing the frontend alone did not make the running
inference process reload the model because it loads the model once at startup.
`docker compose restart inference` made it resolve `champion` again and load
version 2. The visible prediction stayed the same because versions 1 and 2
contained the same model artifact.

**Question 9:** Restarting works without rebuilding because the inference image
contains the application code and Python dependencies, while the selected model
is fetched from MLflow when the container starts. Moving the alias changes
registry state, not the Docker image, so restarting the service is enough to
load the newly selected version.

**Question 10:** After `docker compose down` followed by `docker compose up`, the
`food11` model, its versions, and the `champion` alias were still present because
the `mlflow-data` named volume was preserved. After `docker compose down -v`,
the model URL returned 404 and the registry was empty because `-v` deleted the
volume containing `mlflow.db` and the model artifacts.

**Question 11:** Docker Compose coordinates containers on one machine but does
not provide a multi-node scheduler, automatic replica placement, or a resilient
cluster load balancer. Running three inference replicas and surviving machine
failure would require an orchestrator such as Kubernetes or Docker Swarm, a
load-balanced service, health checks, and shared external storage. MLflow would
also need a highly available database and remote artifact storage such as object
storage instead of a SQLite database and a volume tied to one Docker host.
