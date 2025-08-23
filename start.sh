# checkout/start.sh

#!/usr/bin/env bash
# exit on error
set -o errexit

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
echo "Starting Daphne..."
daphne marketplace.asgi:application --bind 0.0.0.0 --port $PORT