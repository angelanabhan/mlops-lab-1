FROM python:3.11-slim

RUN pip install --no-cache-dir --retries 10 --timeout 300 "mlflow==3.16.0"

EXPOSE 5000

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", "--port", "5000", \
     "--allowed-hosts", "*", \
     "--backend-store-uri", "sqlite:////mlflow-data/mlflow.db", \
     "--serve-artifacts", \
     "--artifacts-destination", "/mlflow-data/mlruns"]
