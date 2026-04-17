# Agnos DevOps Assignment

This repository contains a production-ready DevOps setup for a simple API service and a background worker. The focus is on containerization, high availability, automated CI/CD, and basic observability.

## 1. Architecture Overview

Here is a quick breakdown of how the system is put together:

* **Application:** We have two main Python components. A simple FastAPI service that exposes a `/health` endpoint, and a background worker script that simulates updating records. Both output structured JSON logs for easier monitoring.
* **Containerization:** Both apps are packaged using multi-stage Docker builds. This keeps the final production images lightweight and secure (running as a non-root user).
* **Kubernetes:** The workloads run on K8s. 
    * We use a `Deployment` to ensure the API is managed properly.
    * `ConfigMaps` are used to inject environment variables (like `APP_ENV`).
    * For the API, I've added a `HorizontalPodAutoscaler` (HPA) to scale pods based on CPU usage, along with Liveness and Readiness probes to handle pod health.
* **CI/CD:** The pipeline is built with GitHub Actions. It runs linting (`flake8`), builds the Docker images, scans them for vulnerabilities using Trivy, and simulates a deployment to K8s.

## 2. Setup Instructions

To run this locally, you will need Docker and a local Kubernetes cluster (like Minikube, Kind, or Docker Desktop's built-in K8s).

1. Ensure your local K8s cluster is running and `kubectl` is configured.
2. Apply the configuration first:
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```
3. Apply the deployments and HPA:
   ```bash
   kubectl apply -f k8s/api-deployment.yaml
   kubectl apply -f k8s/hpa.yaml
   ```

## 3. Usage Instructions

**To test the API:**
Since this is a local setup without a load balancer or ingress configured, you can use port-forwarding to access the service:

```bash
kubectl port-forward deployment/agnos-api 8000:8000
```

Then, open a new terminal and run:

```bash
curl http://localhost:8000/health
```

You should get a JSON response showing `"status": "ok"`.

**To check the Logs:**
We output structured JSON logs. You can tail the logs directly from the pods to see them in action:

```bash
kubectl logs -l app=agnos-api -f
```

## 4. Failure Scenario Handling

Here is how we would handle the following common production issues:

**a. API crashes during peak hours:**
If the application process hangs or crashes, the K8s **Liveness Probe** will detect that the `/health` endpoint isn't responding and will automatically restart the failing pod. If the crash is due to a sudden traffic spike causing high CPU load, the **HPA** will automatically spin up new replica pods to handle the load. As an engineer, I would then check the JSON logs and metrics to find the root cause (e.g., memory leaks, slow DB queries) and fix the code.

**b. Worker fails and infinitely retries:**
An infinite retry loop will quickly eat up CPU and memory. We should have Prometheus alerts set up to trigger on "high error rates" or "frequent container restarts" (CrashLoopBackOff). To fix the code, the worker needs an **Exponential Backoff** mechanism for its retries, and a Dead Letter Queue (DLQ) to eventually drop or park the failing job after a maximum number of attempts.

**c. Bad deployment is released:**
First priority is mitigating the impact. We would immediately revert to the previous stable version using `kubectl rollout undo deployment/agnos-api`. This provides a zero-downtime rollback. To prevent this from happening again, we need to improve the CI/CD pipeline by adding integration tests before the deploy step, and consider moving to a Blue/Green or Canary deployment strategy instead of rolling updates.

**d. Kubernetes node downs:**
If we configured our cluster with multiple nodes, the system is designed to survive this. By using `podAntiAffinity` in the deployment spec, we force K8s to schedule the API replicas across different nodes. If one node dies, the Kubernetes Control Plane notices the node is "NotReady", evicts the pods, and automatically reschedules them onto the remaining healthy nodes. The service remains available through the surviving replicas during this transition.
```