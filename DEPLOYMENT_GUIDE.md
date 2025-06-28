# 🚀 LiteForexCryptoAPI Deployment Guide

> Complete guide to deploy LiteForexCryptoAPI on various platforms

## 📋 Prerequisites

- Python 3.11+
- Redis server
- Git
- Docker (optional, for containerized deployment)

---

## 🐳 Docker Deployment (Recommended)

### Quick Start with Docker Compose

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/liteforex-api.git
cd liteforex-api
```

2. **Create environment file:**
```bash
cp env.example .env
# Edit .env with your configuration
```

3. **Start services:**
```bash
docker-compose up -d
```

4. **Check status:**
```bash
docker-compose ps
```

5. **View logs:**
```bash
docker-compose logs -f api
```

### Manual Docker Deployment

1. **Build the image:**
```bash
docker build -t liteforex-api .
```

2. **Run with Redis:**
```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start API
docker run -d --name liteforex-api \
  -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  liteforex-api
```

---

## ☁️ Cloud Platform Deployment

### Railway Deployment

1. **Create Railway account and project**

2. **Connect your repository:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

3. **Set environment variables in Railway dashboard:**
```
REDIS_URL=your-redis-url
ENVIRONMENT=production
```

### Render Deployment

1. **Create Render account**

2. **Create new Web Service**

3. **Connect your GitHub repository**

4. **Configure build settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add environment variables:**
   - `REDIS_URL`
   - `ENVIRONMENT=production`

### Heroku Deployment

1. **Install Heroku CLI**

2. **Create Heroku app:**
```bash
heroku create your-app-name
```

3. **Add Redis addon:**
```bash
heroku addons:create heroku-redis:hobby-dev
```

4. **Deploy:**
```bash
git push heroku main
```

5. **Scale workers:**
```bash
heroku ps:scale worker=1
```

### DigitalOcean App Platform

1. **Create DigitalOcean account**

2. **Create new App**

3. **Connect your repository**

4. **Configure services:**
   - **Main service:** Python app
   - **Redis service:** Managed Redis database

5. **Set environment variables**

---

## 🖥️ VPS/Server Deployment

### Ubuntu/Debian Server

1. **Update system:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install dependencies:**
```bash
sudo apt install -y python3 python3-pip python3-venv redis-server nginx
```

3. **Clone repository:**
```bash
git clone https://github.com/yourusername/liteforex-api.git
cd liteforex-api
```

4. **Setup Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configure Redis:**
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

6. **Create systemd service:**
```bash
sudo nano /etc/systemd/system/liteforex-api.service
```

```ini
[Unit]
Description=LiteForexCryptoAPI
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/liteforex-api
Environment=PATH=/path/to/liteforex-api/venv/bin
ExecStart=/path/to/liteforex-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

7. **Start service:**
```bash
sudo systemctl enable liteforex-api
sudo systemctl start liteforex-api
```

8. **Configure Nginx:**
```bash
sudo nano /etc/nginx/sites-available/liteforex-api
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

9. **Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/liteforex-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### CentOS/RHEL Server

1. **Install dependencies:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip redis nginx
```

2. **Follow similar steps as Ubuntu, but use `yum` instead of `apt`**

---

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# API Configuration
API_TITLE=LiteForexCryptoAPI
API_VERSION=1.0.0
ENVIRONMENT=production

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Data Sources
ECB_API_URL=https://api.exchangerate.host/latest
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Optional Environment Variables

```bash
# Monitoring
SENTRY_DSN=your-sentry-dsn
ENABLE_METRICS=true

# External APIs (optional)
COINMARKETCAP_API_KEY=your-api-key
ALPHA_VANTAGE_API_KEY=your-api-key

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 🔄 Background Tasks Setup

### Celery Worker Setup

1. **Start Celery worker:**
```bash
celery -A celery_app worker --loglevel=info
```

2. **Start Celery beat (scheduler):**
```bash
celery -A celery_app beat --loglevel=info
```

3. **For production, use systemd services:**

```bash
sudo nano /etc/systemd/system/liteforex-celery.service
```

```ini
[Unit]
Description=LiteForexCryptoAPI Celery Worker
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/liteforex-api
Environment=PATH=/path/to/liteforex-api/venv/bin
ExecStart=/path/to/liteforex-api/venv/bin/celery -A celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo nano /etc/systemd/system/liteforex-celerybeat.service
```

```ini
[Unit]
Description=LiteForexCryptoAPI Celery Beat
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/liteforex-api
Environment=PATH=/path/to/liteforex-api/venv/bin
ExecStart=/path/to/liteforex-api/venv/bin/celery -A celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Enable and start services:**
```bash
sudo systemctl enable liteforex-celery
sudo systemctl start liteforex-celery
sudo systemctl enable liteforex-celerybeat
sudo systemctl start liteforex-celerybeat
```

---

## 🔒 SSL/HTTPS Setup

### Let's Encrypt (Recommended)

1. **Install Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Obtain certificate:**
```bash
sudo certbot --nginx -d your-domain.com
```

3. **Auto-renewal:**
```bash
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Manual SSL Setup

1. **Generate SSL certificate**

2. **Update Nginx configuration:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 📊 Monitoring & Logging

### Health Checks

1. **API Health Endpoint:**
```bash
curl https://your-domain.com/health
```

2. **Redis Health Check:**
```bash
redis-cli ping
```

3. **Celery Health Check:**
```bash
celery -A celery_app inspect ping
```

### Logging Setup

1. **Create log directory:**
```bash
mkdir -p /var/log/liteforex-api
sudo chown www-data:www-data /var/log/liteforex-api
```

2. **Configure log rotation:**
```bash
sudo nano /etc/logrotate.d/liteforex-api
```

```
/var/log/liteforex-api/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### Monitoring with Prometheus/Grafana

1. **Add Prometheus metrics endpoint**
2. **Configure Grafana dashboard**
3. **Set up alerts**

---

## 🔄 Updates & Maintenance

### Update Application

1. **Pull latest changes:**
```bash
git pull origin main
```

2. **Update dependencies:**
```bash
pip install -r requirements.txt
```

3. **Restart services:**
```bash
sudo systemctl restart liteforex-api
sudo systemctl restart liteforex-celery
sudo systemctl restart liteforex-celerybeat
```

### Database Maintenance

1. **Redis backup:**
```bash
redis-cli BGSAVE
```

2. **Cache cleanup:**
```bash
redis-cli FLUSHDB
```

### Performance Optimization

1. **Enable Redis persistence**
2. **Configure connection pooling**
3. **Optimize Celery settings**
4. **Setup CDN for static files**

---

## 🚨 Troubleshooting

### Common Issues

1. **Redis Connection Error:**
```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server
```

2. **API Not Responding:**
```bash
# Check API status
sudo systemctl status liteforex-api

# Check API logs
sudo journalctl -u liteforex-api -f
```

3. **Celery Tasks Not Running:**
```bash
# Check Celery status
sudo systemctl status liteforex-celery

# Check Celery logs
sudo journalctl -u liteforex-celery -f
```

4. **Rate Limiting Issues:**
```bash
# Check Redis keys
redis-cli keys "ratelimit:*"

# Clear rate limits (if needed)
redis-cli keys "ratelimit:*" | xargs redis-cli del
```

### Performance Issues

1. **High Response Times:**
   - Check Redis connection
   - Verify cache is working
   - Monitor external API calls

2. **Memory Usage:**
   - Monitor Redis memory usage
   - Check for memory leaks
   - Optimize cache TTL

3. **CPU Usage:**
   - Monitor Celery worker processes
   - Check for long-running tasks
   - Optimize data processing

---

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs` or `sudo journalctl`
2. Verify environment variables
3. Test Redis connection
4. Check firewall settings
5. Verify DNS configuration

---

## 🎯 Next Steps

After successful deployment:
1. Set up monitoring and alerting
2. Configure backup strategies
3. Implement CI/CD pipeline
4. Set up staging environment
5. Plan scaling strategy 