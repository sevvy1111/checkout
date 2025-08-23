#!/usr/bin/env bash
# .build.sh

set -o errexit  # stop on error

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate --noinput
