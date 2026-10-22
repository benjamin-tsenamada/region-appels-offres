#!/usr/bin/env bash
# Script de build pour Render

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py charger_geo
python manage.py import_armp
python normaliser_regions.py
python finaliser_regions.py
python manage.py forcer_reclassifier