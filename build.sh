#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files into STATIC_ROOT for WhiteNoise
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
