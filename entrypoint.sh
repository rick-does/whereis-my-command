#!/bin/sh
set -e

cd /app/backend
exec .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
