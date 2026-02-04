# Agentic Workflow Platform - Deployment Guide

Complete guide for deploying the Agentic Workflow Platform (Backend + Frontend).

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Considerations](#production-considerations)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Node.js 18+ and npm**
   - Download from: https://nodejs.org/
   ```bash
   node --version  # Should be 18 or higher
   npm --version
   ```

3. **Docker and Docker Compose** (for containerized deployment)
   - Download from: https://www.docker.com/

4. **Git**
   ```bash
   git --version
   ```

### API Keys

You'll need API keys for at least one AI provider:

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **DeepSeek**: https://platform.deepseek.com/

## 📁 Project Structure

```
Agentic_WorkFlow_Platform/
├── apps/
│   ├── api/              # Backend FastAPI application
│   │   ├── src/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   ├── run.py
│   │   └── Dockerfile
│   └── web/              # Frontend Next.js application
│       ├── app/
│       ├── components/
│       ├── lib/
│       ├── types/
│       ├── package.json
│       └── Dockerfile
├── data/                 # Persistent data (SQLite DB, artifacts)
│   ├── db/
│   └── artifacts/
├── docker-compose.yml    # Docker orchestration
└── docs/                 # Documentation
```

## 🚀 Backend Deployment

### Local Development

1. **Navigate to backend directory**:
   ```bash
   cd apps/api
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional):
   Create `apps/api/.env`:
   ```env
   # Database
   DATABASE_URL=sqlite:///../../data/db/workflows.db
   
   # Security
   SECRET_KEY=your-secret-key-here-min-32-chars
   
   # CORS
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   
   # Logging
   LOG_LEVEL=INFO
   ```

5. **Run the server**:
   ```bash
   python run.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Verify deployment**:
   - API: http://localhost:8000
   - Health check: http://localhost:8000/api/v1/health
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Production Deployment

1. **Use Gunicorn with Uvicorn workers**:
   ```bash
   gunicorn src.main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --timeout 120 \
     --access-logfile - \
     --error-logfile -
   ```

2. **Configure environment variables**:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost/workflows
   SECRET_KEY=<generate-secure-key-32-chars+>
   CORS_ORIGINS=https://your-frontend-domain.com
   LOG_LEVEL=WARNING
   ```

3. **Use a reverse proxy** (Nginx/Caddy):
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Running Tests

```bash
cd apps/api

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api_workflows.py

# Verbose output
pytest -v -s
```

Expected output: **36/36 tests passing** ✅

## 🎨 Frontend Deployment

### Local Development

1. **Install Node.js** (if not installed):
   - Download from: https://nodejs.org/
   - Verify: `node --version` (should be 18+)

2. **Navigate to frontend directory**:
   ```bash
   cd apps/web
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```
   
   This installs:
   - Next.js 14
   - React 19
   - TanStack Query
   - Tailwind CSS
   - Axios
   - UI components
   - And more...

4. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

5. **Run development server**:
   ```bash
   npm run dev
   ```
   
   Frontend available at: http://localhost:3000

6. **Verify deployment**:
   - Landing page: http://localhost:3000
   - Dashboard: http://localhost:3000/dashboard
   - Workflows: http://localhost:3000/workflows
   - Settings: http://localhost:3000/settings

### Production Build

1. **Build the application**:
   ```bash
   npm run build
   ```
   
   This creates an optimized production build in `.next/`

2. **Start production server**:
   ```bash
   npm start
   ```
   
   Or use PM2 for process management:
   ```bash
   npm install -g pm2
   pm2 start npm --name "agentic-web" -- start
   pm2 save
   pm2 startup
   ```

3. **Configure production environment**:
   ```env
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
   NODE_ENV=production
   ```

### Deploy to Vercel (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy**:
   ```bash
   cd apps/web
   vercel
   ```

3. **Configure environment**:
   - Go to your project settings on Vercel
   - Add environment variable: `NEXT_PUBLIC_API_URL`
   - Redeploy if needed

### Deploy to Netlify

1. **Build command**: `npm run build`
2. **Publish directory**: `.next`
3. **Environment variables**:
   - `NEXT_PUBLIC_API_URL`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Ensure Docker is installed**:
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Review docker-compose.yml**:
   ```yaml
   services:
     api:
       build: ./apps/api
       ports:
         - "8000:8000"
       volumes:
         - ./data:/app/data
       environment:
         - DATABASE_URL=sqlite:///data/db/workflows.db
         - SECRET_KEY=${SECRET_KEY}
     
     web:
       build: ./apps/web
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
       depends_on:
         - api
   ```

3. **Start all services**:
   ```bash
   # From project root
   docker-compose up -d
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Stop services**:
   ```bash
   docker-compose down
   ```

### Individual Docker Builds

**Backend**:
```bash
cd apps/api
docker build -t agentic-api .
docker run -p 8000:8000 -v $(pwd)/../../data:/app/data agentic-api
```

**Frontend**:
```bash
cd apps/web
docker build -t agentic-web .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 agentic-web
```

## 🔐 Production Considerations

### Security

1. **Generate secure SECRET_KEY**:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Use HTTPS**: Always use SSL/TLS in production
   - Let's Encrypt (free): https://letsencrypt.org/
   - Cloudflare (free tier): https://cloudflare.com/

3. **Secure API keys**: Never commit API keys to version control
   - Use environment variables
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)

4. **CORS Configuration**: Only allow your frontend domain
   ```env
   CORS_ORIGINS=https://yourdomain.com
   ```

### Database

**SQLite** (Development):
```env
DATABASE_URL=sqlite:///data/db/workflows.db
```

**PostgreSQL** (Production):
```env
DATABASE_URL=postgresql://user:password@localhost:5432/workflows
```

Migration steps:
1. Export data from SQLite
2. Create PostgreSQL database
3. Update `DATABASE_URL`
4. Restart application

### Monitoring

1. **Application logs**:
   ```bash
   # Backend
   tail -f logs/app.log
   
   # Frontend (PM2)
   pm2 logs agentic-web
   ```

2. **Health checks**:
   - Backend: `GET /api/v1/health`
   - Frontend: `GET /` (should return 200)

3. **Metrics** (recommended tools):
   - Prometheus + Grafana
   - Datadog
   - New Relic

### Backup Strategy

1. **Database backups**:
   ```bash
   # SQLite
   cp data/db/workflows.db backups/workflows-$(date +%Y%m%d).db
   
   # PostgreSQL
   pg_dump workflows > backups/workflows-$(date +%Y%m%d).sql
   ```

2. **Artifact backups**:
   ```bash
   tar -czf backups/artifacts-$(date +%Y%m%d).tar.gz data/artifacts/
   ```

3. **Automated backups** (cron):
   ```bash
   0 2 * * * /path/to/backup-script.sh
   ```

## 🔧 Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=sqlite:///../../data/db/workflows.db

# Security
SECRET_KEY=your-secret-key-min-32-characters-long

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Logging
LOG_LEVEL=INFO

# File Storage
ARTIFACTS_DIR=../../data/artifacts

# API Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=Agentic Workflow Platform
```

### Frontend (.env.local)

```env
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Optional: Analytics
NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

## 🐛 Troubleshooting

### Backend Issues

**Port already in use**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

**Database locked**:
```bash
# Stop all instances
# Delete lock file
rm data/db/workflows.db-journal
```

**Import errors**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**npm command not found**:
- Install Node.js from https://nodejs.org/

**Port 3000 in use**:
```bash
# Run on different port
PORT=3001 npm run dev
```

**API connection failed**:
- Check backend is running: http://localhost:8000/api/v1/health
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS settings in backend

**Build errors**:
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

### Docker Issues

**Port conflicts**:
```yaml
# Edit docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

**Volume permissions**:
```bash
# Linux
sudo chown -R $USER:$USER data/
```

**Out of memory**:
```yaml
# Add to docker-compose.yml
services:
  api:
    mem_limit: 1g
```

## 📊 Performance Optimization

### Backend

1. **Use PostgreSQL** instead of SQLite for production
2. **Enable caching** for frequently accessed data
3. **Use connection pooling** for database
4. **Add CDN** for static artifacts

### Frontend

1. **Enable compression**:
   ```javascript
   // next.config.js
   module.exports = {
     compress: true,
   };
   ```

2. **Optimize images**: Use Next.js Image component
3. **Code splitting**: Automatic with Next.js App Router
4. **Add CDN**: CloudFlare, Vercel Edge Network

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd apps/api
          pip install -r requirements.txt
          pytest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Your deployment commands here
```

## 📝 Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Environment variables configured (both backend and frontend)
- [ ] Database initialized
- [ ] Backend tests passing (36/36)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] API keys added via Settings page
- [ ] Test workflow created and executed
- [ ] CORS configured correctly
- [ ] SSL/TLS enabled (production)
- [ ] Backups configured
- [ ] Monitoring set up

## 🆘 Support

For issues or questions:

1. Check this deployment guide
2. Review API documentation: `docs/API_DOCUMENTATION.md`
3. Check backend status: `docs/BACKEND_STATUS.md`
4. Review logs for error messages
5. Open an issue on GitHub (if applicable)

## 📚 Additional Resources

- [Backend API Documentation](../API_DOCUMENTATION.md)
- [Backend Status Report](../BACKEND_STATUS.md)
- [Frontend README](../apps/web/README.md)
- [Architecture Documentation](architecture/)

---

**Last Updated**: December 2024
**Platform Version**: 1.0.0

---

Happy Deploying! 🚀
