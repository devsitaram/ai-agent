# Deployment Guide

## Prerequisites

- Python 3.11+
- pip
- A server or cloud platform account

## Environment Variables

Create a `.env` file in the project root:

```env
# Application
DEBUG=false
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db

# Optional: Use PostgreSQL in production
# DATABASE_URL=postgresql://user:password@localhost/dbname

# CORS
ALLOWED_ORIGINS=https://your-domain.com
```

## Local Deployment

### Using Uvicorn

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Linux)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --workers 4
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - SECRET_KEY=change-in-production
    volumes:
      - ./data:/app/data
```

### Build and Run

```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
```

## Cloud Deployment

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Add `vercel.json`:
```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```
3. Run `vercel --prod`

### Railway

1. Push code to GitHub
2. Create new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Set environment variables
5. Railway auto-detects Python/FastAPI

### Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your repository
3. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Monitoring

### Health Check
The application provides a health check endpoint at `/health`.

### Logging
Logs are output to stdout by default. Configure file logging in production:

```bash
uvicorn app.main:app --log-level info --log-config logging.conf
```

## Backup

### Database Backup
```bash
# SQLite
cp app.db app.db.backup

# PostgreSQL
pg_dump dbname > backup.sql
```

## Scaling

- Increase workers: `--workers 8`
- Use PostgreSQL for better concurrency
- Add caching with Redis
- Use a reverse proxy (nginx) for production
