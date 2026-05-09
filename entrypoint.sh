#!/bin/bash
set -e

MODE=${START_MODE:-web}

if [ "$MODE" = "web" ]; then
    echo "Starting Control Plane (FastAPI)..."
    exec uvicorn services.control_plane.main:app --host 0.0.0.0 --port 8000
elif [ "$MODE" = "worker" ]; then
    echo "Starting Compute Plane (Celery)..."
    exec celery -A services.compute_plane.celery_app worker --loglevel=info
else
    echo "Unknown START_MODE: $MODE. Please set to 'web' or 'worker'."
    exit 1
fi
