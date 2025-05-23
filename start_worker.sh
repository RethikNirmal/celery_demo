#!/bin/bash

# Clean up any old processes
echo "Stopping any running Celery workers..."
pkill -f 'celery worker' || true

# Start worker with proper settings for priority
echo "Starting Celery worker with priority settings..."
celery -A app worker \
  --loglevel=info \
  --prefetch-multiplier=1 \
  --concurrency=1 \
  --without-gossip \
  --without-mingle \
  -Q queue1,queue2,queue3 