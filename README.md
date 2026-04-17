## 1\. Architecture Overview

  * **Application:** Two Python components (FastAPI for the API and a custom background worker). Both are instrumented with structured JSON logging for easy log aggregation.
  * **Containerization:** Multi-stage Docker builds to ensure minimal image size and security. Containers run as non-root (nobody).
  * **Kubernetes:**
      * **Deployments:** Managed API and Worker nodes.
      * **ConfigMaps:** Decoupled environment variables (DEV/UAT/PROD).
      * **Scalability & Health:** HPA handles auto-scaling via CPU metrics. Liveness/Readiness probes ensure traffic only hits healthy pods.
  * **CI/CD:** Automated via GitHub Actions. The pipeline includes flake8 linting, Trivy security scanning, Docker builds, and mock deployment.

## 2\. Setup

Prerequisites: Docker and a local K8s cluster (Minikube, Kind, or Docker Desktop).

1.  Check your K8s context: `kubectl config current-context`
2.  Apply ConfigMap:
    ```bash
    kubectl apply -f k8s/configmap.yaml
    ```
3.  Deploy Apps & HPA:
    ```bash
    kubectl apply -f k8s/api-deployment.yaml
    kubectl apply -f k8s/hpa.yaml
    ```

## 3\. Usage

**Testing the API:**
Port-forward to access the service locally:

```bash
kubectl port-forward deployment/agnos-api 8000:8000
```

Then hit the health endpoint:

```bash
curl http://localhost:8000/health
```

**Monitoring Logs:**
Tail JSON logs directly from the pods:

```bash
kubectl logs -l app=agnos-api -f
```

## 4\. Failure Scenarios & Mitigation

  * **API Crash (Peak Hours):** K8s Liveness Probes automatically restart failed pods. HPA handles traffic spikes by spinning up additional replicas. Engineers can then investigate root causes via JSON logs/metrics.
  * **Worker Infinite Retries:** Prometheus alerts (CrashLoopBackOff/High Error Rate) notify the team. Mitigation involves implementing Exponential Backoff and Dead Letter Queues (DLQ) in the worker logic.
  * **Bad Release:** Immediate rollback using `kubectl rollout undo`. Long-term fix includes stronger integration tests and moving toward Canary/Blue-Green deployment strategies.
  * **Node Failure:** HA is maintained via `podAntiAffinity`, ensuring replicas are spread across different nodes. K8s automatically reschedules pods from the dead node to healthy ones.

-----