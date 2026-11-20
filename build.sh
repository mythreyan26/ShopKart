#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "--- Installing dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

echo "--- Collecting static assets with WhiteNoise ---"
python manage.py collectstatic --noinput

echo "--- Applying database schema migrations ---"
python manage.py migrate

echo "--- ShopKart build completed successfully! ---"
