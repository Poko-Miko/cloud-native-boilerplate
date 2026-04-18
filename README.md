# Cloud-Native Boilerplate (FastAPI + Worker + Kubernetes)

A production-ready cloud-native boilerplate featuring a FastAPI service, background worker, Dockerized builds, and Kubernetes deployment with CI/CD.

## 🚀 Overview

This project demonstrates a minimal cloud-native architecture with:

* **API Service** – FastAPI-based HTTP service
* **Worker Service** – Background process for periodic tasks
* **Containerization** – Multi-stage Docker builds
* **Orchestration** – Kubernetes deployments with scaling and reliability
* **CI/CD** – GitHub Actions pipeline with security scanning

## 🧱 Architecture

* API and worker run as **independent deployments**
* Stateless design using environment-based configuration
* Kubernetes handles scaling, rollout, and recovery
* Prometheus-compatible metrics exposed by the API

## 📂 Project Structure

```
.
├── src/
│   ├── api.py              # FastAPI application
│   ├── worker.py           # Background worker
│   ├── test_api.py         # Tests
│   └── requirements.txt    # Dependencies
├── k8s/                    # Kubernetes manifests
├── Dockerfile.api
├── Dockerfile.worker
└── .github/workflows/      # CI/CD pipeline
```

## ⚙️ API Endpoints

| Endpoint   | Description        |
| ---------- | ------------------ |
| `/`        | Service info       |
| `/health`  | Liveness probe     |
| `/ready`   | Readiness probe    |
| `/metrics` | Prometheus metrics |

## 🖥️ Local Setup

**Requirements:** Python 3.11+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

## ▶️ Run Locally

**Start API**

```bash
APP_ENV=DEV uvicorn src.api:app --host 0.0.0.0 --port 8000
```

**Start Worker**

```bash
APP_ENV=DEV WORKER_INTERVAL_SECONDS=60 python src/worker.py
```

**Run Tests**

```bash
PYTHONPATH=src pytest -q src/test_api.py
```

## 🐳 Docker

**Build images**

```bash
docker build -f Dockerfile.api -t api:local .
docker build -f Dockerfile.worker -t worker:local .
```

**Run containers**

```bash
docker run -p 8000:8000 -e APP_ENV=DEV api:local
docker run -e APP_ENV=DEV worker:local
```

## ☸️ Kubernetes Deployment

Update image registry (`OWNER`) in manifests, then:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/
```

Check status:

```bash
kubectl get pods
kubectl get svc
kubectl logs -l app=cloud-api
```

## 📈 Scaling & Reliability

* Horizontal Pod Autoscaler (HPA)
* Rolling updates with zero downtime
* PodDisruptionBudget for availability
* Health checks (liveness/readiness)
* Resource limits and requests
* Non-root, secure containers

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:

* Linting (`flake8`)
* Testing (`pytest`)
* Dependency audit (`pip-audit`)
* Docker build
* Security scan (Trivy)
* Push to container registry
* Deploy to Kubernetes

**Required Secret**

```
KUBE_CONFIG_DATA = base64 encoded kubeconfig
```

## 📊 Monitoring

* Prometheus metrics exposed at `/metrics`
* Ready for integration with Grafana dashboards

## 🛡️ Security

* Non-root containers
* Minimal base images
* Dependency and image vulnerability scanning
* Restricted container privileges

---