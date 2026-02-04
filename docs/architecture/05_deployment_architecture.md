# Deployment Architecture - Agentic Workflow Platform

**Document Version:** 1.0  
**Date:** February 4, 2026  
**Audience:** DevOps, SRE, Platform Engineering  
**Status:** Implementation Ready

---

## Deployment Environments

| Environment | Purpose | Infrastructure | Data Persistence |
|-------------|---------|----------------|------------------|
| **Local (MVP)** | Development, MVP demo | Docker Compose | SQLite + local FS |
| **Staging** | Pre-production testing | Cloud VM / K8s | PostgreSQL + S3 |
| **Production** | Customer-facing | Kubernetes (GKE/EKS/AKS) | PostgreSQL (HA) + S3 |

---

## MVP: Local Docker Compose Deployment

### Architecture Diagram

```mermaid
graph TB
    User[User Browser<br/>localhost:3000]
    
    subgraph "Docker Compose Network"
        subgraph "Web Container"
            NextJS[Next.js 15<br/>Node.js 20<br/>Port 3000]
        end
        
        subgraph "API Container"
            FastAPI[FastAPI<br/>Python 3.11<br/>Uvicorn<br/>Port 8000]
        end
        
        subgraph "Volumes (Host-Mounted)"
            DB[(SQLite DB<br/>/data/db/workflows.db)]
            Artifacts[Artifacts<br/>/data/artifacts/]
        end
    end

    User -->|HTTP| NextJS
    NextJS -->|REST API| FastAPI
    FastAPI -->|Read/Write| DB
    FastAPI -->|Write| Artifacts

    style NextJS fill:#61DAFB,color:#000
    style FastAPI fill:#009688,color:#fff
    style DB fill:#4DB33D,color:#fff
    style Artifacts fill:#FFA726,color:#000
```

### docker-compose.yml (Production-Ready)

```yaml
version: '3.8'

services:
  # Backend API
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: agentic_workflow_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/db/workflows.db
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - ARTIFACTS_PATH=/app/data/artifacts
      - SECRET_KEY=${SECRET_KEY}
      - PYTHONUNBUFFERED=1
    volumes:
      # Mount data for persistence
      - ./data:/app/data
      # Mount source for hot-reload (dev only)
      - ./apps/api/src:/app/src:ro
    env_file:
      - .env
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Frontend Web
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=http://localhost:8000
    container_name: agentic_workflow_web
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
      - NODE_ENV=development
    volumes:
      # Mount source for hot-reload (dev only)
      - ./apps/web/src:/app/src:ro
      - ./apps/web/public:/app/public:ro
      # Exclude node_modules
      - /app/node_modules
    depends_on:
      api:
        condition: service_healthy
    networks:
      - app_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  app_network:
    driver: bridge

volumes:
  # Named volume for production (optional)
  db_data:
    driver: local
  artifacts_data:
    driver: local
```

### Startup Commands

```bash
# First-time setup
cp .env.example .env
# Edit .env with your configuration

# Build and start
docker-compose up --build

# Background mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Clean rebuild (if needed)
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Resource Allocation (Docker)

```yaml
# Resource limits (production)
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
  
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## Staging/Production: Kubernetes Deployment

### High-Level Architecture

```mermaid
graph TB
    subgraph "Ingress Layer"
        LB[Cloud Load Balancer<br/>ALB / GCP LB]
        Ingress[Nginx Ingress Controller<br/>TLS Termination]
    end

    subgraph "Application Pods"
        Web1[Web Pod 1<br/>Next.js]
        Web2[Web Pod 2<br/>Next.js]
        API1[API Pod 1<br/>FastAPI]
        API2[API Pod 2<br/>FastAPI]
        API3[API Pod 3<br/>FastAPI]
    end

    subgraph "Worker Pods (Future)"
        Worker1[Worker Pod 1<br/>Celery]
        Worker2[Worker Pod 2<br/>Celery]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>RDS / Cloud SQL<br/>Primary + Replica)]
        Redis[(Redis<br/>ElastiCache / MemoryStore<br/>Task Queue)]
        S3[Object Storage<br/>S3 / GCS<br/>Artifacts]
    end

    subgraph "Observability"
        Prometheus[Prometheus<br/>Metrics]
        Grafana[Grafana<br/>Dashboards]
        Loki[Loki<br/>Logs]
    end

    LB --> Ingress
    Ingress --> Web1
    Ingress --> Web2
    Ingress --> API1
    Ingress --> API2
    Ingress --> API3

    Web1 --> API1
    Web2 --> API2

    API1 --> PG
    API2 --> PG
    API3 --> PG

    API1 --> Redis
    API2 --> Redis
    API3 --> Redis

    API1 --> S3
    API2 --> S3
    API3 --> S3

    Worker1 --> Redis
    Worker2 --> Redis
    Worker1 --> PG
    Worker2 --> PG
    Worker1 --> S3
    Worker2 --> S3

    API1 --> Prometheus
    API2 --> Prometheus
    Worker1 --> Prometheus

    Prometheus --> Grafana
    Loki --> Grafana

    style LB fill:#FFD700
    style Web1 fill:#61DAFB
    style API1 fill:#009688
    style PG fill:#336791
    style Redis fill:#DC382D
    style S3 fill:#569A31
```

### Kubernetes Manifests

**Namespace:**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentic-workflows
  labels:
    name: agentic-workflows
    environment: production
```

**ConfigMap:**
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: agentic-workflows
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DATABASE_URL: "postgresql+asyncpg://user:password@postgres-service:5432/workflows"
  ARTIFACTS_STORAGE: "s3"
  S3_BUCKET: "agentic-workflows-artifacts"
  REDIS_URL: "redis://redis-service:6379/0"
```

**Secret:**
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: agentic-workflows
type: Opaque
data:
  SECRET_KEY: <base64-encoded-value>
  DATABASE_PASSWORD: <base64-encoded-value>
  OPENAI_API_KEY: <base64-encoded-value>  # Optional default
```

**API Deployment:**
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: agentic-workflows
  labels:
    app: api
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: v1
    spec:
      containers:
      - name: api
        image: gcr.io/project/agentic-workflow-api:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: API_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: API_HOST
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: SECRET_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
```

**API Service:**
```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: agentic-workflows
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
```

**Web Deployment:**
```yaml
# k8s/web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: agentic-workflows
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: gcr.io/project/agentic-workflow-web:v1.0.0
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://api.workflows.example.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**Ingress:**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: agentic-workflows
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - workflows.example.com
    - api.workflows.example.com
    secretName: tls-secret
  rules:
  - host: workflows.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 3000
  - host: api.workflows.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

**Horizontal Pod Autoscaler:**
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: agentic-workflows
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Database Migration Strategy

### SQLite → PostgreSQL

**Phase 1: Preparation**
```bash
# Export SQLite data
sqlite3 data/db/workflows.db .dump > backup.sql

# Transform to PostgreSQL compatible
sed 's/AUTOINCREMENT/SERIAL/g' backup.sql > postgres_backup.sql
```

**Phase 2: Schema Migration (Alembic)**
```python
# apps/api/alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('encrypted_value', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    op.create_index('idx_settings_provider', 'settings', ['provider'])
    op.create_index('idx_settings_user_id', 'settings', ['user_id'])
    
    # ... other tables
```

**Phase 3: Data Migration**
```python
# Migration script
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def migrate_data():
    sqlite_engine = create_async_engine("sqlite+aiosqlite:///data/db/workflows.db")
    postgres_engine = create_async_engine("postgresql+asyncpg://user:pass@host/db")
    
    # Migrate settings
    async with sqlite_engine.connect() as src_conn:
        result = await src_conn.execute("SELECT * FROM settings")
        rows = result.fetchall()
        
        async with postgres_engine.connect() as dst_conn:
            for row in rows:
                await dst_conn.execute(
                    "INSERT INTO settings VALUES (...)",
                    row
                )
            await dst_conn.commit()
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: gcr.io
  PROJECT_ID: my-gcp-project

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          cd apps/api
          pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-api:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to GCR
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Build and push API image
        run: |
          gcloud auth configure-docker gcr.io
          docker build -t $REGISTRY/$PROJECT_ID/api:$GITHUB_SHA apps/api
          docker push $REGISTRY/$PROJECT_ID/api:$GITHUB_SHA
          docker tag $REGISTRY/$PROJECT_ID/api:$GITHUB_SHA $REGISTRY/$PROJECT_ID/api:latest
          docker push $REGISTRY/$PROJECT_ID/api:latest

  build-web:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Web image
        run: |
          docker build -t $REGISTRY/$PROJECT_ID/web:$GITHUB_SHA apps/web
          docker push $REGISTRY/$PROJECT_ID/web:$GITHUB_SHA

  deploy-staging:
    needs: [build-api, build-web]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to GKE Staging
        run: |
          gcloud container clusters get-credentials staging-cluster --region us-central1
          kubectl set image deployment/api api=$REGISTRY/$PROJECT_ID/api:$GITHUB_SHA -n agentic-workflows-staging
          kubectl set image deployment/web web=$REGISTRY/$PROJECT_ID/web:$GITHUB_SHA -n agentic-workflows-staging
          kubectl rollout status deployment/api -n agentic-workflows-staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to GKE Production
        run: |
          gcloud container clusters get-credentials prod-cluster --region us-central1
          kubectl set image deployment/api api=$REGISTRY/$PROJECT_ID/api:$GITHUB_SHA -n agentic-workflows
          kubectl set image deployment/web web=$REGISTRY/$PROJECT_ID/web:$GITHUB_SHA -n agentic-workflows
          kubectl rollout status deployment/api -n agentic-workflows
```

---

## Monitoring & Observability

### Prometheus Metrics

```python
# apps/api/src/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Workflow execution metrics
workflow_runs_total = Counter(
    'workflow_runs_total',
    'Total workflow runs',
    ['workflow_id', 'status', 'run_mode']
)

workflow_duration_seconds = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_id', 'run_mode'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# Provider metrics
provider_api_calls_total = Counter(
    'provider_api_calls_total',
    'Total LLM provider API calls',
    ['provider', 'status']
)

provider_api_latency_seconds = Histogram(
    'provider_api_latency_seconds',
    'LLM provider API latency',
    ['provider']
)

# System metrics
active_runs = Gauge(
    'active_runs',
    'Number of currently running workflows'
)
```

### Grafana Dashboard (JSON)

```json
{
  "dashboard": {
    "title": "Agentic Workflows - Production",
    "panels": [
      {
        "title": "Workflow Runs (Last 24h)",
        "targets": [
          {
            "expr": "sum(rate(workflow_runs_total[5m])) by (status)"
          }
        ]
      },
      {
        "title": "API Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(workflow_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Runs",
        "targets": [
          {
            "expr": "active_runs"
          }
        ]
      }
    ]
  }
}
```

---

## Backup & Disaster Recovery

### Database Backups

**PostgreSQL Automated Backups:**
```bash
# Cronjob for daily backups
0 2 * * * pg_dump -h postgres-host -U user workflows > /backups/workflows_$(date +\%Y\%m\%d).sql

# Retention policy (30 days)
find /backups/ -name "workflows_*.sql" -mtime +30 -delete
```

**S3 Artifacts Backup:**
```bash
# S3 versioning enabled (automatic)
aws s3api put-bucket-versioning \
  --bucket agentic-workflows-artifacts \
  --versioning-configuration Status=Enabled

# Cross-region replication
aws s3api put-bucket-replication \
  --bucket agentic-workflows-artifacts \
  --replication-configuration file://replication.json
```

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** 4 hours  
**RPO (Recovery Point Objective):** 24 hours

**Runbook:**
1. Detect outage (alerts, monitoring)
2. Assess scope (database, application, infrastructure)
3. Restore from backup (last known good state)
4. Verify data integrity
5. Re-deploy application (blue-green deployment)
6. Test functionality (smoke tests)
7. Communicate status to users

---

## Cost Optimization

### Cloud Cost Estimate (AWS/GCP)

| Component | Specs | Monthly Cost |
|-----------|-------|--------------|
| **Kubernetes Cluster** | 3 nodes, e2-standard-4 | $300 |
| **PostgreSQL (RDS/Cloud SQL)** | db.t3.medium, HA | $200 |
| **Redis (ElastiCache)** | cache.t3.micro | $15 |
| **S3/GCS Storage** | 1TB, standard | $23 |
| **Load Balancer** | ALB/GCP LB | $20 |
| **Egress** | 500GB/month | $45 |
| **Monitoring (Prometheus/Grafana)** | Managed service | $50 |
| **LLM API Costs** | Variable (user-paid) | $0 |
| **Total** | | **~$653/month** |

**Cost Optimization Strategies:**
- Use spot instances for worker pods (70% discount)
- Enable auto-scaling (scale to zero during low traffic)
- Use reserved instances for database (40% discount)
- Implement caching (reduce LLM calls)
- Compress artifacts before S3 upload

---

## Deployment Checklist

### Pre-Deployment
- [ ] Run all tests (unit, integration, e2e)
- [ ] Security scan (dependency vulnerabilities)
- [ ] Database migration tested on staging
- [ ] Environment variables configured
- [ ] Secrets rotated (if needed)
- [ ] Backup current database
- [ ] Communication sent to users (planned downtime)

### Deployment
- [ ] Deploy to staging first
- [ ] Smoke tests pass on staging
- [ ] Deploy to production (blue-green or canary)
- [ ] Monitor error rates (Sentry, logs)
- [ ] Verify health checks pass
- [ ] Test critical user flows (run workflow)

### Post-Deployment
- [ ] Monitor metrics (CPU, memory, latency)
- [ ] Check error logs (no critical errors)
- [ ] Verify backup completed
- [ ] Update documentation (changelog)
- [ ] Post deployment summary (blameless)

---

## Next Steps

1. ✅ Review deployment architecture
2. → Set up local Docker Compose environment
3. → Test one-command launch
4. → Plan Kubernetes migration (post-MVP)
5. → Configure monitoring (Prometheus + Grafana)

---

**Approved By:** _[Pending DevOps Review]_  
**Date:** _[Pending]_
