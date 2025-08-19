# checkout/start.sh

#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Daphne..."
daphne marketplace.asgi:application --bind 0.0.0.0 --port $PORT