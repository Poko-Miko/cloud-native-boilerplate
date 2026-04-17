# Cloud Native DevOps Assignment

Production-ready sample for the Agnos DevOps assignment. The application is
intentionally small so the DevOps setup is the main deliverable.
.
## Architecture Overview

The system has two independent components:

- `agnos-api`: FastAPI HTTP service.
- `agnos-worker`: background worker that periodically updates the timestamp for
  today's records. In this assignment it is stubbed as a structured log event
  because no database is required.

Runtime configuration is provided through environment variables and a Kubernetes
ConfigMap. Docker builds are multi-stage. Kubernetes runs the API and worker as
separate deployments so they can scale, restart, and roll out independently.

## Repository Layout

- `src/api.py`: API service with health, readiness, metrics, and security
  headers.
- `src/worker.py`: background worker loop.
- `src/test_api.py`: API tests.
- `src/requirements.txt`: pinned Python dependencies.
- `Dockerfile.api`: multi-stage API container image.
- `Dockerfile.worker`: multi-stage worker container image.
- `k8s/configmap.yaml`: environment configuration.
- `k8s/api-deployment.yaml`: API deployment.
- `k8s/api-service.yaml`: API load balancer service.
- `k8s/api-pdb.yaml`: API PodDisruptionBudget.
- `k8s/worker-deployment.yaml`: worker deployment.
- `k8s/hpa.yaml`: API HorizontalPodAutoscaler.
- `.github/workflows/deploy.yml`: CI/CD pipeline.

## Application Endpoints

- `GET /`: service status and environment.
- `GET /health`: liveness endpoint.
- `GET /ready`: readiness endpoint with uptime.
- `GET /metrics`: Prometheus metrics.

Prometheus metrics include:

- `agnos_api_requests_total`: request counter labeled by method, path, and
  status.
- `agnos_api_request_duration_seconds`: request latency histogram labeled by
  method and path.

## Local Setup

Use Python 3.11 for parity with the container images.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r src\requirements.txt
```

## Local Usage

Run the API:

```bash
APP_ENV=DEV uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Run the worker:

```bash
APP_ENV=DEV WORKER_INTERVAL_SECONDS=60 python src/worker.py
```

Run tests and lint:

```bash
PYTHONPATH=src pytest -q src/test_api.py
flake8 src/
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
pytest -q src\test_api.py
flake8 src\
```

## Docker Usage

Build the API image:

```bash
docker build -f Dockerfile.api -t agnos-api:local .
```

Build the worker image:

```bash
docker build -f Dockerfile.worker -t agnos-worker:local .
```

Run the API image:

```bash
docker run --rm -p 8000:8000 -e APP_ENV=DEV agnos-api:local
```

Run the worker image:

```bash
docker run --rm -e APP_ENV=DEV -e WORKER_INTERVAL_SECONDS=60 agnos-worker:local
```

The runtime containers use a non-root UID, unbuffered Python output, and pinned
dependencies.

## Kubernetes Setup

Before deploying, replace `OWNER` in these files with the GitHub Container
Registry owner or organization:

- `k8s/api-deployment.yaml`
- `k8s/worker-deployment.yaml`

Apply the manifests:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-pdb.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/hpa.yaml
```

Verify the deployment:

```bash
kubectl get pods
kubectl get svc
kubectl get hpa
kubectl get pdb
kubectl logs -l app=agnos-api -f
kubectl logs -l app=agnos-worker -f
```

If using Minikube:

```bash
minikube service agnos-api
```

## Kubernetes Reliability Design

- API and worker are separate deployments.
- API starts with two replicas.
- API uses `maxUnavailable: 0` rolling updates to avoid planned downtime.
- API has preferred pod anti-affinity to spread pods across nodes when possible.
- API has a PodDisruptionBudget with `minAvailable: 1`.
- API has readiness and liveness probes.
- Worker has a liveness probe and Kubernetes restart behavior.
- CPU and memory requests/limits are set for both workloads.
- HPA scales the API from 2 to 5 replicas at 70 percent CPU utilization.
- Containers run as non-root, drop Linux capabilities, and disable privilege
  escalation.

## CI/CD

The GitHub Actions workflow runs on pushes to `main`.

Pipeline stages:

1. Check out source.
2. Install Python 3.11 dependencies.
3. Run `flake8`.
4. Run API tests.
5. Run Python dependency audit with `pip-audit`.
6. Build API and worker Docker images.
7. Scan both images with Trivy and fail on HIGH or CRITICAL issues.
8. Push SHA and `latest` tags to GitHub Container Registry.
9. Configure kubeconfig from `KUBE_CONFIG_DATA`.
10. Apply Kubernetes manifests.
11. Update deployments to the SHA-tagged images.
12. Wait for rollouts to finish.

Required GitHub Actions secret:

- `KUBE_CONFIG_DATA`: base64 encoded kubeconfig.

Generate it with:

```bash
base64 -w 0 ~/.kube/config
```

## Monitoring

The API exposes Prometheus metrics on `/metrics`, and the API pod template has
Prometheus scrape annotations.

Recommended dashboards:

- Request rate by path and status.
- P95/P99 request latency from `agnos_api_request_duration_seconds`.
- Error rate from `agnos_api_requests_total` where status starts with `5`.
- API replica count and HPA scaling events.
- Pod restart count for API and worker.

Recommended alerts:

- API high error rate: 5xx responses exceed 5 percent for 5 minutes.
- API high latency: P95 latency exceeds the service target for 5 minutes.
- Worker crash loop: worker pod restart count increases repeatedly.
- Kubernetes node down: any ready node becomes not ready for more than 5
  minutes.
- API unavailable: no ready API pods for 2 minutes.

Logs are structured JSON from both API and worker. They include timestamp,
level, service, and message fields.

## Failure Scenarios

### API Crashes During Peak Hours

Kubernetes restarts failed API containers through the liveness probe. The
readiness probe removes unhealthy pods from service endpoints before traffic is
sent to them. The API runs two replicas and can scale to five with HPA during
CPU pressure. During a bad rollout, use:

```bash
kubectl rollout undo deployment/agnos-api
```

### Worker Fails and Infinitely Retries

The worker catches loop errors, logs the exception, waits 5 seconds, and retries
instead of spinning tightly. If the process exits or becomes unhealthy,
Kubernetes restarts the pod. Investigate with:

```bash
kubectl logs -l app=agnos-worker --previous
kubectl describe pod -l app=agnos-worker
```

If the failure is caused by a bad deployment, roll back:

```bash
kubectl rollout undo deployment/agnos-worker
```

### Bad Deployment Is Released

The pipeline deploys immutable SHA-tagged images and waits for rollout status.
Kubernetes rolling updates keep the previous version serving while the new pods
become ready. Roll back either deployment with:

```bash
kubectl rollout undo deployment/agnos-api
kubectl rollout undo deployment/agnos-worker
```

### Kubernetes Node Goes Down

The API has two replicas, preferred pod anti-affinity, and a PodDisruptionBudget
so planned disruptions keep at least one API pod available. If a node becomes
not ready, Kubernetes reschedules affected pods onto healthy nodes when
capacity exists. Confirm node and pod state with:

```bash
kubectl get nodes
kubectl get pods -o wide
kubectl describe node <node-name>
```

## Assignment Checklist

- API service: implemented with FastAPI.
- API endpoint `GET /health`: implemented.
- Background worker: implemented.
- Worker updates timestamp of today's records: implemented as a stubbed
  structured log event.
- Multi-stage Docker builds: implemented for API and worker.
- Environment variable configuration: implemented with Docker env and
  Kubernetes ConfigMap for DEV/UAT/PROD style usage.
- Kubernetes high availability: API replicas, rolling update, anti-affinity,
  PDB, probes, HPA.
- Separate deployments for API and worker: implemented.
- Resource requests and limits: implemented.
- Readiness and liveness probes: implemented.
- HPA for API: implemented.
- CI/CD with GitHub Actions: implemented.
- CI stages for lint, test, build, security scan, and deploy: implemented.
- Structured JSON logs: implemented.
- Metrics for request latency and error rate: implemented through Prometheus
  metrics.
- Alerts for high error rate, stalled worker, and crash looping: documented.
- Failure scenario handling: documented.
