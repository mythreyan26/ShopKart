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

echo "--- Loading sample seed data (products, categories, users) ---"
python manage.py loaddata seed_data.json || echo "Seed data already loaded or skipped."

echo "--- ShopKart build completed successfully! ---"
