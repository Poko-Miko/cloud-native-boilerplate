- Prerequisite: Docker, kubectl
- Step 1: `kubectl apply -f k8s/configmap.yaml`
- Step 2: `kubectl apply -f k8s/api-deployment.yaml`
...

- How to test API: `curl http://<minikube-ip>:8000/health`
- How to view worker logs: `kubectl logs -l app=agnos-worker -f`