# Deployment Guide: HR Knowledge Assistant

## 1. Docker Compose (Local Deployment)

```bash
cp .env.example .env
# Edit .env with your LLM_API_KEY
docker compose up --build -d
```

## 2. Kubernetes Deployment

Ensure you have a running Kubernetes cluster with `kubectl` configured:

```bash
# 1. Create Namespace
kubectl apply -f deployment/kubernetes/namespace.yaml

# 2. Apply ConfigMap and Secret
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/secret.example.yaml  # Use real secret in production

# 3. Deploy PostgreSQL with pgvector
kubectl apply -f deployment/kubernetes/postgres.yaml

# 4. Deploy Backend & Frontend
kubectl apply -f deployment/kubernetes/backend-deployment.yaml
kubectl apply -f deployment/kubernetes/frontend-deployment.yaml

# 5. Apply Ingress & HPA
kubectl apply -f deployment/kubernetes/ingress.yaml
kubectl apply -f deployment/kubernetes/hpa.yaml
```

## 3. Jenkins CI/CD Pipeline

The project includes a production declarative `Jenkinsfile` at `deployment/jenkins/Jenkinsfile` that automates:
1. Linting with `ruff` and `eslint`
2. Static type checks with `mypy` and `tsc`
3. Unit & integration test execution
4. Container image builds for frontend and backend
5. Automated rollout to Kubernetes cluster on `main` branch merges.
