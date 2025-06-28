#!/bin/bash

# LiteForexCryptoAPI Startup Script

set -e

echo "🚀 Starting LiteForexCryptoAPI..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting with Docker..."
    docker run -d --name liteforex_redis -p 6379:6379 redis:7-alpine
    echo "✅ Redis started"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A celery_app worker --loglevel=info --detach

# Start Celery beat in background
echo "⏰ Starting Celery beat..."
celery -A celery_app beat --loglevel=info --detach

# Start the API
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ LiteForexCryptoAPI is running!"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health" 