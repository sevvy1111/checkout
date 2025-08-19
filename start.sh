# checkout/start.sh

#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting both Gunicorn and Daphne with Honcho..."
honcho start