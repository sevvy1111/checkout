# checkout/build.sh

#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
daphne marketplace.asgi:application --bind 0.0.0.0 --port $PORT