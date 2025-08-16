#!/usr/bin/env bash
# Exit on first error
set -e

# Install Python dependencies from requirements.txt
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Daphne ASGI server
echo "Starting Daphne server..."
DJANGO_SETTINGS_MODULE=marketplace.settings daphne -b 0.0.0.0 -p 8000 marketplace.asgi:application