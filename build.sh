#!/usr/bin/env bash
# Script de build pour Render

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Les commandes ci-dessous sont commentées pour éviter de bloquer Render 
# lors du déploiement. Tu pourras les lancer manuellement ensuite.
# python manage.py charger_geo
# python manage.py import_armp
# python manage.py normaliser_regions
# python manage.py forcer_reclassifier