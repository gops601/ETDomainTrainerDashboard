#!/bin/sh

# Wait for database to be ready
echo "Waiting for database..."
python migrate.py

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn "app:create_app()" \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
