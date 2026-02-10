# DEPLOYMENT_GUIDE.md - Production Deployment Instructions

# 🚀 Agri-Mind Deployment Guide

Complete guide for deploying Agri-Mind in production environments.

## Prerequisites

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- GitHub account (for Streamlit Cloud)
- Sentinel Hub account with OAuth credentials
- Optional: AWS/GCP account (for cloud deployment)

## 1. Local Deployment

### Development Environment

```bash
# Clone and setup
git clone "https://github.com/Eng-Khalaf/Agri-Mind/tree/main"
cd agri-mind
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials:
# SENTINELHUB_CLIENT_ID=your_id
# SENTINELHUB_CLIENT_SECRET=your_secret

# Run
streamlit run app.py
```

**Access**: `http://localhost:8501`

### Production Local Deployment

```bash
# Using production Python interpreter
python -m streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --logger.level=info \
  --client.showErrorDetails=false
```

## 2. Docker Deployment

### Build Image

```bash
# Standard build
docker build -t agri-mind:latest .

# With build arguments
docker build -t agri-mind:1.0 \
  --build-arg PYTHON_VERSION=3.10 \
  .

# Push to registry (optional)
docker tag agri-mind:latest myregistry/agri-mind:latest
docker push myregistry/agri-mind:latest
```

### Run Container

```bash
# Basic run
docker run -p 8501:8501 \
  -e SENTINELHUB_CLIENT_ID="your_id" \
  -e SENTINELHUB_CLIENT_SECRET="your_secret" \
  agri-mind:latest

# With persistent volumes
docker run -p 8501:8501 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/cache:/app/.streamlit/cache \
  -e SENTINELHUB_CLIENT_ID="your_id" \
  -e SENTINELHUB_CLIENT_SECRET="your_secret" \
  agri-mind:latest

# With resource limits
docker run -p 8501:8501 \
  --memory="2g" \
  --cpus="2" \
  -e SENTINELHUB_CLIENT_ID="your_id" \
  -e SENTINELHUB_CLIENT_SECRET="your_secret" \
  agri-mind:latest
```

### Docker Compose (Recommended)

```bash
# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# View logs
docker-compose logs -f agri-mind

# Stop services
docker-compose down

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Access**: `http://localhost:8501`

## 3. Streamlit Cloud Deployment

### Step 1: Prepare Repository

```bash
# Ensure these files exist:
# - app.py
# - requirements.txt
# - config.py
# - utils/ directory
# - README.md

# Push to GitHub
git add .
git commit -m "Production deployment"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Visit: https://share.streamlit.io
2. Click "New app"
3. Select repository, branch, and main file (app.py)
4. Click "Deploy"

### Step 3: Configure Secrets

In Streamlit Cloud App Settings → Secrets → Add:

```toml
# .streamlit/secrets.toml
SENTINELHUB_CLIENT_ID = "your_client_id"
SENTINELHUB_CLIENT_SECRET = "your_client_secret"
OPENWEATHER_API_KEY = "your_key"
DEMO_MODE = "false"
```

**Access**: `https://your-username-agri-mind.streamlit.app`

## 4. AWS Deployment

### Option A: EC2 + Docker

```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium)
# 2. Connect to instance

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone and deploy
git clone <repo-url> agri-mind
cd agri-mind
cp .env.example .env
# Edit .env

docker-compose up -d

# Configure nginx reverse proxy (optional)
# See nginx.conf example below
```

### Option B: AWS App Runner

```bash
# Prerequisites: Docker image in ECR

# Using AWS CLI
aws apprunner create-service \
  --service-name agri-mind \
  --source-configuration ImageRepository={ImageIdentifier=<your-ecr-uri>,ImageRepositoryType=ECR,ImageConfiguration={Port=8501}} \
  --instance-configuration Cpu=1024,Memory=2048 \
  --auto-scaling-configuration MaxConcurrency=100

# Get service URL
aws apprunner list-services --query 'ServiceSummaryList[0].ServiceUrl'
```

### Option C: AWS ECS Fargate

```bash
# Create ECS task definition, service, and cluster
# Reference: ECS deployment template in infrastructure/ directory

# Using CloudFormation (optional)
aws cloudformation create-stack \
  --stack-name agri-mind \
  --template-body file://infrastructure/ecs-template.yaml \
  --parameters ParameterKey=ImageUri,ParameterValue=<your-ecr-uri>
```

## 5. Google Cloud Deployment

### Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/<project-id>/agri-mind

# Deploy
gcloud run deploy agri-mind \
  --image gcr.io/<project-id>/agri-mind \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars SENTINELHUB_CLIENT_ID=<id>,SENTINELHUB_CLIENT_SECRET=<secret>

# Get service URL
gcloud run services describe agri-mind --region us-central1 --format 'value(status.url)'
```

### App Engine

```bash
# Create app.yaml
cat > app.yaml << EOF
runtime: python310
env: standard

env_variables:
  SENTINELHUB_CLIENT_ID: "your_id"
  SENTINELHUB_CLIENT_SECRET: "your_secret"

automatic_scaling:
  min_instances: 1
  max_instances: 5
EOF

# Deploy
gcloud app deploy

# View
gcloud app browse
```

## 6. Nginx Reverse Proxy Configuration

**nginx.conf**
```nginx
upstream streamlit {
    server localhost:8501;
}

server {
    listen 80;
    server_name agri-mind.example.com;
    client_max_body_size 50M;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    # SSL configuration (optional)
    # listen 443 ssl;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
}
```

**Start Nginx**
```bash
docker run -d \
  -p 80:80 \
  -p 443:443 \
  -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v $(pwd)/certs:/etc/nginx/certs:ro \
  nginx:latest
```

## 7. Performance Tuning

### Streamlit Configuration

**~/.streamlit/config.toml**
```toml
[server]
maxUploadSize = 200
enableXsrfProtection = true
enableCORS = false
headless = true
logger.level = "error"

[client]
showErrorDetails = false
toolbarMode = "minimal"

[theme]
primaryColor = "#2E7D32"
backgroundColor = "#F1F8E9"
secondaryBackgroundColor = "#C5E1A5"
textColor = "#1B5E20"
font = "sans serif"

[logger]
level = "info"
messageFormat = "%(asctime)s - %(message)s"

[cache]
maxMessageCacheUtilizationFraction = 0.5
```

### Caching Strategy

```python
# 6-hour cache for expensive operations
@st.cache_data(ttl=21600)
def fetch_satellite_data(bbox, dates):
    return client.fetch_satellite_data(bbox, dates)

# Resource caching (persistent)
@st.cache_resource
def get_sentinel_client():
    return SentinelHubClient()
```

### Database Caching (Optional)

For high-traffic deployments, consider Redis:

```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Install Redis client
pip install redis

# Configure in app.py
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

## 8. Monitoring & Logging

### Health Checks

```bash
# Test endpoint
curl -f http://localhost:8501/_stcore/health || echo "Unhealthy"

# Docker health check (in docker-compose)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Logging

```bash
# Docker logs
docker-compose logs -f agri-mind

# Log rotation
cat > /etc/logrotate.d/agri-mind << EOF
/var/log/agri-mind/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 appuser appgroup
}
EOF
```

### Monitoring (Prometheus + Grafana)

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Grafana URL: http://localhost:3000
# Prometheus: http://localhost:9090
```

## 9. Backup & Recovery

### Data Backup

```bash
# Backup cache and logs
tar -czf agri-mind-backup-$(date +%Y%m%d).tar.gz \
  .streamlit/cache \
  logs/

# Upload to S3
aws s3 cp agri-mind-backup-*.tar.gz s3://your-bucket/backups/
```

### Disaster Recovery

```bash
# Restore from backup
tar -xzf agri-mind-backup-YYYYMMDD.tar.gz
docker-compose down
docker-compose up -d
```

## 10. SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly \
  --standalone \
  -d agri-mind.example.com \
  -d www.agri-mind.example.com

# Update Nginx
sudo certbot install --nginx

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Self-Signed Certificate

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365
```

## 11. Rollback Procedure

```bash
# Tag current version
docker tag agri-mind:latest agri-mind:backup

# Revert to previous version
docker pull agri-mind:v1.0
docker tag agri-mind:v1.0 agri-mind:latest
docker-compose restart

# Or using git
git checkout v1.0
docker-compose build --no-cache
docker-compose up -d
```

## 12. Troubleshooting

### App Won't Start

```bash
# Check logs
docker-compose logs agri-mind

# Verify dependencies
pip install -r requirements.txt --verbose

# Test imports
python -c "from utils.satellite import *"
```

### High Memory Usage

```bash
# Reduce cache size
# In config: reduce CACHE_TTL_HOURS
# Use @st.cache_data(max_entries=100)

# Monitor memory
docker stats agri-mind

# Set resource limits
docker run --memory="2g" --cpus="2" agri-mind
```

### API Rate Limiting

```bash
# Add rate limiter middleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

## Production Checklist

- [ ] Environment variables configured (.env or secrets)
- [ ] Sentinel Hub credentials tested
- [ ] SSL/TLS enabled
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Error logging enabled
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] CORS restrictions in place
- [ ] Rate limiting enabled
- [ ] Demo mode disabled in production
- [ ] Database connected (if applicable)
- [ ] CDN configured (if applicable)
- [ ] DDoS protection enabled
- [ ] Regular security updates scheduled

---

**Last Updated**: Feb 2026  
**Version**: 1.0.0 Production Ready ✅
