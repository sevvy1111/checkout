#!/usr/bin/env bash
# .build.sh

set -o errexit  # stop on error

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate --noinput

# Create superuser if it doesn’t exist (must use env vars from Render)
python manage.py shell -c "
from django.contrib.auth import get_user_model;
import os;
User = get_user_model();
username = os.environ['DJANGO_SUPERUSER_USERNAME'];
email = os.environ['DJANGO_SUPERUSER_EMAIL'];
password = os.environ['DJANGO_SUPERUSER_PASSWORD'];
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
"