"""
Commande Django : normalise les noms de régions dans la base.
Convertit les libellés bruts de l'ARMP en noms officiels.

Usage :
    python manage.py normaliser_regions

Exemples :
    'REGION : ATSIMO ANDREFANA (21 avis)'  →  'Atsimo-Andrefana'
    'ATSIMO ANDREFANA'                     →  'Atsimo-Andrefana'
    'Analamanga'                           →  'Analamanga' (inchangé)
    'Ambatosoa'                            →  'Alaotra-Mangoro' (fusion)
"""

import re
from collections import Counter

from django.core.management.base import BaseCommand

from appels_offres.models import AppelOffre


MAPPING_REGIONS = {
    "CENTRALE": "Analamanga",
    "ANALAMANGA": "Analamanga",
    "VAKINANKARATRA": "Vakinankaratra",
    "ITASY": "Itasy",
    "BONGOLAVA": "Bongolava",
    "VATOVAVY": "Vatovavy",
    "FITOVINANY": "Fitovinany",
    "AMORON'IMANIA": "Amoron'i Mania",
    "AMORONIMANIA": "Amoron'i Mania",
    "HAUTE MATSIATRA": "Haute Matsiatra",
    "ATSIMO ATSINANANA": "Atsimo-Atsinanana",
    "ATSIMO-ATSINANANA": "Atsimo-Atsinanana",
    "IHOROMBE": "Ihorombe",
    "MENABE": "Menabe",
    "ATSIMO ANDREFANA": "Atsimo-Andrefana",
    "ATSIMO-ANDREFANA": "Atsimo-Andrefana",
    "ANDROY": "Androy",
    "ANOSY": "Anosy",
    "SAVA": "Sava",
    "DIANA": "Diana",
    "SOFIA": "Sofia",
    "BOENY": "Boeny",
    "BETSIBOKA": "Betsiboka",
    "MELAKY": "Melaky",
    "ALAOTRA-MANGORO": "Alaotra-Mangoro",
    "ALAOTRA MANGORO": "Alaotra-Mangoro",
    "ATSINANANA": "Atsinanana",
    "ANALANJIROFO": "Analanjirofo",
    # Anciennes valeurs résiduelles à fusionner
    "AMBATOSOA": "Alaotra-Mangoro",
}


def normaliser_nom(region):
    """Prend une valeur de région ARMP et renvoie le nom officiel."""
    if not region:
        return None

    texte = region.strip()
    texte = re.sub(r"^REGION\s*:\s*", "", texte, flags=re.IGNORECASE)
    texte = re.sub(r"\s*\(\d+\s*avis\)\s*$", "", texte, flags=re.IGNORECASE)
    texte = texte.strip().upper()

    if texte in MAPPING_REGIONS:
        return MAPPING_REGIONS[texte]

    return region.strip()


class Command(BaseCommand):
    help = "Normalise les noms de régions ARMP en noms officiels"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Normalisation des régions ==="))

        valeurs_uniques = set(
            AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
            .values_list("region", flat=True)
        )

        self.stdout.write(f"{len(valeurs_uniques)} valeurs uniques à traiter\n")

        modifications = 0
        for valeur in valeurs_uniques:
            nouvelle_valeur = normaliser_nom(valeur)

            if nouvelle_valeur != valeur:
                nb = AppelOffre.objects.filter(region=valeur).update(region=nouvelle_valeur)
                modifications += nb
                self.stdout.write(
                    f"  {repr(valeur)[:55]:55} → {nouvelle_valeur:25} ({nb} AO)"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"AO modifiés : {modifications}"))

        self.stdout.write("\nValeurs finales en base :")
        compteur = Counter(
            AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
            .values_list("region", flat=True)
        )
        for v, nb in sorted(compteur.items()):
            self.stdout.write(f"  {v:30} : {nb} AO")