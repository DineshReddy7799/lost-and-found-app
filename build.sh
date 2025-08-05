#!/usr/bin/env bash
# Install system dependencies
apt-get update && apt-get install -y gdal-bin

# Install Python dependencies
pip install -r requirements.txt

# Django collect static files & migrate
python manage.py collectstatic --no-input
python manage.py migrate
