# 🚀 Project 1: GitOps Microservices Platform

[![CI/CD](https://github.com/your-org/gitops-microservices/actions/workflows/ci-cd.yml/badge.svg)](https://github.com)
[![ArgoCD](https://img.shields.io/badge/GitOps-ArgoCD-orange)](https://argoproj.github.io/argo-cd/)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                     │
│  Code Push → Test → Security Scan → Build → Push → GitOps  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    ┌─────▼──────┐
                    │   ArgoCD   │ (GitOps Operator)
                    └─────┬──────┘
                          │ Sync manifests
          ┌───────────────▼────────────────────┐
          │         Kubernetes Cluster          │
          │  ┌──────────┐  ┌──────────────────┐│
          │  │  API GW   │  │   Prometheus +   ││
          │  │  (Nginx)  │  │   Grafana        ││
          │  └─────┬─────┘  └──────────────────┘│
          │        │                             │
          │  ┌─────▼──────┐  ┌──────────────┐  │
          │  │User Service│  │Order Service │  │
          │  │(Node.js)   │  │(Python)      │  │
          │  └────────────┘  └──────────────┘  │
          └────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Services | Node.js 20, Python 3.12 FastAPI |
| Container | Docker multi-stage builds |
| Orchestration | Kubernetes + Helm |
| GitOps | ArgoCD |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
| Service Mesh | Nginx (API Gateway) |

## 🚀 Quick Start

### Local Development
```bash
# Clone and start all services
git clone https://github.com/your-org/gitops-microservices-platform
cd gitops-microservices-platform

# Start all services
docker-compose up -d

# Verify services
curl http://localhost/health
curl http://localhost/api/v1/users

# View metrics
open http://localhost:9090   # Prometheus
open http://localhost:3000   # Grafana (admin/admin@123)
```

### Deploy to Kubernetes
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply ArgoCD apps
kubectl apply -f argocd/application.yaml

# Watch sync
argocd app list
argocd app sync microservices-dev
```

## 📁 Project Structure

```
.
├── services/
│   ├── user-service/      # Node.js user management API
│   ├── order-service/     # Python order management API
│   └── api-gateway/       # Nginx reverse proxy + rate limiting
├── helm/
│   ├── charts/            # Helm chart per service
│   └── environments/      # dev/staging/prod values
├── argocd/                # ArgoCD application manifests
├── monitoring/
│   ├── prometheus/        # Metrics + alerting rules (SLO-based)
│   └── grafana/           # Dashboards provisioning
└── .github/workflows/     # CI/CD pipeline (8 stages)
```

## 🔄 CI/CD Flow

```
1. Code Push
   ↓
2. Run Tests (unit + integration)
   ↓
3. Security Scan (Trivy filesystem)
   ↓
4. Build Docker image (multi-arch: amd64 + arm64)
   ↓
5. Scan Container Image (Trivy)
   ↓
6. Push to GitHub Container Registry
   ↓
7. Update Helm values (GitOps - commit new tag)
   ↓
8. ArgoCD auto-sync → Deploy to DEV
   ↓
9. Manual gate → Deploy to STAGING
   ↓
10. Manual approval → Deploy to PROD
```

## 📊 Monitoring

- **Prometheus**: Metrics scraping every 15s
- **Grafana**: Pre-built dashboards for all services
- **Alertmanager**: Alerts for SLO breaches, high error rates
- **SLO**: 99.9% availability, P95 < 500ms

## 🔐 Security Features

- Non-root containers
- Read-only root filesystem
- Resource limits on all containers
- Network policies (restrict inter-service traffic)
- Secrets from Kubernetes Secrets (+ Vault ready)
- RBAC for ArgoCD service accounts

## 📚 Learning Objectives

1. ✅ Microservices architecture with multiple languages
2. ✅ Docker multi-stage builds
3. ✅ Helm chart templating
4. ✅ GitOps with ArgoCD (auto-sync, self-heal)
5. ✅ GitHub Actions (parallel jobs, matrix builds)
6. ✅ Prometheus metrics instrumentation
7. ✅ SLO-based alerting
8. ✅ Container security best practices
