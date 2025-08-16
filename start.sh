#!/usr/bin/env bash
# exit on error
set -o errexit

# Force a clean installation of dependencies
pip install --upgrade pip
pip install --no-cache-dir --force-reinstall -r requirements.txt

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Start the Daphne server
daphne -b 0.0.0.0 -p 8000 marketplace.asgi:application