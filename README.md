# fscart — End-to-End GitOps Automation on EKS

A production-grade shopping cart microservice with full CI/CD, GitOps deployment, and observability on AWS EKS.

```
GitHub Push → GitHub Actions CI (lint → test → build → push to Docker Hub)
           → GitHub Actions CD (update image tag in Git)
           → ArgoCD (detects Git change → syncs to EKS)
           → EKS (runs fscart with Istio sidecar)
           → Grafana + Loki + Tempo + Kiali (observability)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                          │
│  app/  k8s/  argocd/  terraform/  .github/workflows/               │
└────────────┬────────────────────────────────┬───────────────────────┘
             │ push                           │ ArgoCD watches
             ▼                                ▼
┌────────────────────┐            ┌───────────────────────┐
│  GitHub Actions CI │            │       AWS EKS          │
│  lint → test →     │            │  ┌─────────────────┐  │
│  build → push      │            │  │  fscart-dev     │  │
│  (Docker Hub)      │            │  │  fscart-staging │  │
└────────┬───────────┘            │  │  fscart-prod    │  │
         │ CD: update             │  └─────────────────┘  │
         │ image tag in Git       │                        │
         └──────────────────────► │  ArgoCD               │
                                  │  Istio + Kiali         │
                                  │  Loki + Tempo          │
                                  │  Grafana               │
                                  └───────────────────────┘
```

### Components

| Layer | Technology | Purpose |
|-------|-----------|---------|
| App | FastAPI (Python 3.12) | REST API — products, cart, orders |
| Container | Docker (multi-stage) | Image: `fathimasalam/fscart` |
| Orchestration | AWS EKS 1.30 | Kubernetes cluster |
| Networking | Istio + Ingress Gateway | Service mesh, traffic management |
| GitOps | ArgoCD (app-of-apps) | Declarative continuous delivery |
| CI | GitHub Actions | Lint, test, build, push |
| CD | GitHub Actions + ArgoCD | Tag update → auto-sync |
| Logs | Loki + Promtail | Log aggregation |
| Traces | Tempo | Distributed tracing (OTLP) |
| Metrics | Prometheus + Grafana | Dashboards and alerting |
| Mesh viz | Kiali | Service graph and traffic flow |
| Infra | Terraform | EKS, VPC, observability stack |

---

## Repository Structure

```
fscart/
├── app/                        # FastAPI application
│   ├── main.py                 # App entry point, router registration
│   ├── config.py               # Settings (pydantic-settings)
│   ├── db/database.py          # Async SQLAlchemy engine
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── routers/                # API route handlers
│   └── services/               # Business logic layer
├── tests/                      # pytest test suite (31 tests)
├── requirements.txt
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml          # Local stack (app + postgres + redis)
├── docker-compose.override.yml # Dev overrides (hot reload)
├── k8s/
│   ├── base/                   # Base Kustomize manifests
│   └── overlays/
│       ├── dev/                # 1 replica, debug logging
│       ├── staging/            # 2 replicas
│       └── prod/               # 3 replicas, strict anti-affinity
├── argocd/
│   ├── projects/fscart-project.yaml
│   └── apps/
│       ├── root-app.yaml       # App-of-apps bootstrap
│       ├── fscart-dev.yaml
│       ├── fscart-staging.yaml
│       └── fscart-prod.yaml    # Manual sync (no auto)
├── terraform/
│   ├── main.tf                 # Root: VPC + EKS modules
│   ├── versions.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── vpc/                # VPC, subnets, IGW, NAT GWs
│       ├── eks/                # EKS cluster, node groups, OIDC
│       └── observability/      # Istio, Kiali, Loki, Tempo, Grafana
├── observability/
│   ├── grafana-values.yaml
│   ├── kiali-cr.yaml
│   ├── loki-values.yaml
│   └── tempo-values.yaml
└── .github/
    └── workflows/
        ├── ci.yml              # lint → test → build → push
        ├── cd.yml              # update tag → ArgoCD sync
        ├── pr-checks.yml       # k8s validate, trivy scan, tf lint
        └── destroy.yml         # Manual terraform destroy
```

---

## API Endpoints

Base URL: `http://localhost:8000` (local) or `https://fscart.example.com` (cluster)

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/health/ready` | Readiness check (DB ping) |

### Products
| Method | Path | Description |
|--------|------|-------------|
| GET | `/products` | List all products (paginated) |
| GET | `/products/{id}` | Get product by ID |
| POST | `/products` | Create product |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |

### Cart
| Method | Path | Description |
|--------|------|-------------|
| GET | `/cart/{user_id}` | Get user's cart |
| POST | `/cart/{user_id}/items` | Add item to cart |
| PUT | `/cart/{user_id}/items/{item_id}` | Update item quantity |
| DELETE | `/cart/{user_id}/items/{item_id}` | Remove item |
| DELETE | `/cart/{user_id}` | Clear cart |

### Orders
| Method | Path | Description |
|--------|------|-------------|
| POST | `/orders` | Create order from cart |
| GET | `/orders/{order_id}` | Get order by ID |
| GET | `/orders/user/{user_id}` | List orders for user |
| PUT | `/orders/{order_id}/status` | Update order status |

Interactive docs: `http://localhost:8000/docs`

---

## Local Development

### Prerequisites
- Docker Desktop
- Python 3.12+
- `make` (optional)

### Run with Docker Compose

```bash
# Copy env file
cp .env.example .env

# Start the full stack (app + postgres + redis)
docker compose up -d

# View logs
docker compose logs -f app

# API is live at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### Run without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Uses SQLite by default
export DATABASE_URL="sqlite+aiosqlite:///./fscart.db"
uvicorn app.main:app --reload
```

### Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Infrastructure Setup

### Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5
- kubectl
- helm
- argocd CLI

### 1. Provision EKS cluster

```bash
cd terraform

# Edit variables or create terraform.tfvars
cat > terraform.tfvars <<EOF
aws_region   = "us-east-1"
cluster_name = "fscart"
node_groups = {
  system = {
    instance_types = ["t3.medium"]
    desired_size   = 2
    min_size       = 1
    max_size       = 4
  }
}
EOF

terraform init
terraform plan
terraform apply
```

### 2. Configure kubectl

```bash
# Output from terraform apply, or run:
aws eks update-kubeconfig --region us-east-1 --name fscart
kubectl get nodes
```

### 3. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server \
  -n argocd --timeout=120s

# Get initial admin password
kubectl get secret argocd-initial-admin-secret \
  -n argocd -o jsonpath="{.data.password}" | base64 -d && echo
```

### 4. Bootstrap app-of-apps

```bash
# Update the repo URL in argocd/apps/root-app.yaml first
# Then apply the root app
kubectl apply -f argocd/apps/root-app.yaml

# ArgoCD will automatically deploy dev, staging from root-app
# Port-forward to ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
```

### 5. Install observability stack

```bash
cd terraform

# Add to terraform.tfvars:
# grafana_admin_password = "your-secure-password"

# Apply the observability module
terraform apply -target=module.observability
```

---

## CI/CD Pipeline

### Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | `fathimasalam` |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `GH_PAT` | GitHub Personal Access Token (repo scope) for CD tag update commits |
| `ARGOCD_SERVER` | ArgoCD server hostname (without https://) |
| `ARGOCD_USERNAME` | ArgoCD username (e.g. `admin`) |
| `ARGOCD_PASSWORD` | ArgoCD password |
| `AWS_ACCESS_KEY_ID` | AWS credentials for Terraform |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for Terraform |
| `AWS_REGION` | e.g. `us-east-1` |

### CI Flow (`ci.yml`)

```
push to main/develop
    │
    ├── lint       ruff check app/ tests/
    ├── test       pytest (SQLite in-memory)
    └── build-push docker buildx (linux/amd64 + arm64)
                   → fathimasalam/fscart:<sha>
                   → fathimasalam/fscart:latest  (main only)
```

### CD Flow (`cd.yml`)

```
CI completes on main
    │
    ├── update-image-tag   kustomize edit set image
    │                      git commit + push
    └── notify-argocd      argocd app sync fscart-staging
                           argocd app wait fscart-staging --health
                           # prod requires manual sync in ArgoCD UI
```

### PR Checks (`pr-checks.yml`)

Every pull request to `main` runs:
- **k8s validate** — `kustomize build` + `kubectl apply --dry-run` for all overlays
- **security scan** — Trivy for HIGH/CRITICAL CVEs (SARIF uploaded to GitHub Security)
- **terraform lint** — `terraform fmt -check` + `terraform validate`

---

## Observability

### Access UIs via port-forward

```bash
# Grafana (dashboards, logs, traces)
kubectl port-forward svc/grafana -n monitoring 3000:80
# Open http://localhost:3000  (admin / your-password)

# Kiali (service mesh topology)
kubectl port-forward svc/kiali -n istio-system 20001:20001
# Open http://localhost:20001

# ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
```

### What to look at

| Tool | What you see |
|------|-------------|
| Grafana → Explore → Loki | Application logs from all pods, filter by namespace/pod |
| Grafana → Explore → Tempo | Distributed traces for each API request |
| Grafana → Dashboards → Istio | Request rate, error rate, P99 latency per service |
| Kiali → Graph | Live service mesh topology with traffic rates |
| Kiali → Workloads | Health, logs, traces per workload |

### Sending traces from the app

Add to your app (optional OpenTelemetry instrumentation):

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp
```

Set env var:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo.monitoring.svc.cluster.local:4317
```

---

## Environments

| Environment | Namespace | Replicas | Sync | Image Tag |
|-------------|-----------|----------|------|-----------|
| dev | fscart-dev | 1 | Auto | `dev` |
| staging | fscart-staging | 2 | Auto | `<git-sha>` |
| prod | fscart-prod | 3 | **Manual** | `<git-sha>` |

### Promoting to production

1. Verify staging is healthy in ArgoCD and Grafana
2. Open ArgoCD UI → `fscart-prod` → **Sync**
3. Or via CLI: `argocd app sync fscart-prod`

---

## Clean Up

```bash
# Destroy all AWS resources
cd terraform
terraform destroy

# Or use the manual GitHub Actions workflow:
# Actions → destroy.yml → Run workflow → environment: prod → type DESTROY
```

> NAT Gateways (~$32/month each) and the EKS cluster (~$0.10/hour) are the main cost drivers. Destroy when not in use.

---

## License

MIT
