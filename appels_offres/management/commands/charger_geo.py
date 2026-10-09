"""
Commande Django : charger les 22 régions et 119 districts de Madagascar.

Usage :
    python manage.py charger_geo
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from appels_offres.models import Region, District
from data.madagascar import REGIONS_DISTRICTS


class Command(BaseCommand):
    help = "Charge les régions et districts de Madagascar en base"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Chargement des régions et districts ==="))

        regions_creees = 0
        districts_crees = 0
        districts_maj = 0

        with transaction.atomic():
            for code, (nom_region, districts) in REGIONS_DISTRICTS.items():
                region, cree = Region.objects.get_or_create(nom=nom_region)
                if cree:
                    regions_creees += 1

                for nom_district, lat, lng in districts:
                    district, cree = District.objects.get_or_create(
                        nom=nom_district,
                        region=region,
                        defaults={"latitude": lat, "longitude": lng},
                    )
                    if cree:
                        districts_crees += 1
                    else:
                        # Mettre à jour les coordonnées si manquantes
                        if district.latitude is None or district.longitude is None:
                            district.latitude = lat
                            district.longitude = lng
                            district.save()
                            districts_maj += 1

        self.stdout.write(self.style.SUCCESS("=== Terminé ==="))
        self.stdout.write(f"Régions créées     : {regions_creees}")
        self.stdout.write(f"Districts créés    : {districts_crees}")
        self.stdout.write(f"Districts mis à jour : {districts_maj}")
        self.stdout.write(f"Total régions en base : {Region.objects.count()}")
        self.stdout.write(f"Total districts en base : {District.objects.count()}")