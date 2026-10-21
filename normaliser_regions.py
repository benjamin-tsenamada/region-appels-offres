"""
Normalise les noms de régions dans la base.
Transforme :
    'REGION : ATSIMO ANDREFANA (21 avis)'  →  'Atsimo-Andrefana'
    'ATSIMO ANDREFANA'                     →  'Atsimo-Andrefana'
    'Analamanga'                           →  'Analamanga' (inchangé)
"""

import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from appels_offres.models import AppelOffre, Region


# Mapping : toutes les variantes → nom officiel
MAPPING_REGIONS = {
    # Analamanga
    "CENTRALE": "Analamanga",
    "ANALAMANGA": "Analamanga",
    # Vakinankaratra
    "VAKINANKARATRA": "Vakinankaratra",
    # Itasy
    "ITASY": "Itasy",
    # Bongolava
    "BONGOLAVA": "Bongolava",
    # Vatovavy
    "VATOVAVY": "Vatovavy",
    # Fitovinany
    "FITOVINANY": "Fitovinany",
    # Amoron'i Mania
    "AMORON'IMANIA": "Amoron'i Mania",
    "AMORONIMANIA": "Amoron'i Mania",
    # Haute Matsiatra
    "HAUTE MATSIATRA": "Haute Matsiatra",
    # Atsimo-Atsinanana
    "ATSIMO ATSINANANA": "Atsimo-Atsinanana",
    "ATSIMO-ATSINANANA": "Atsimo-Atsinanana",
    # Ihorombe
    "IHOROMBE": "Ihorombe",
    # Menabe
    "MENABE": "Menabe",
    # Atsimo-Andrefana
    "ATSIMO ANDREFANA": "Atsimo-Andrefana",
    "ATSIMO-ANDREFANA": "Atsimo-Andrefana",
    # Androy
    "ANDROY": "Androy",
    # Anosy
    "ANOSY": "Anosy",
    # Sava
    "SAVA": "Sava",
    # Diana
    "DIANA": "Diana",
    # Sofia
    "SOFIA": "Sofia",
    # Boeny
    "BOENY": "Boeny",
    # Betsiboka
    "BETSIBOKA": "Betsiboka",
    # Melaky
    "MELAKY": "Melaky",
    # Alaotra-Mangoro
    "ALAOTRA-MANGORO": "Alaotra-Mangoro",
    "ALAOTRA MANGORO": "Alaotra-Mangoro",
    # Atsinanana
    "ATSINANANA": "Atsinanana",
    # Analanjirofo
    "ANALANJIROFO": "Analanjirofo",
}


def normaliser_nom(region):
    """
    Prend une valeur de région et renvoie le nom officiel.
    Gère : 'REGION : XXX (N avis)', 'XXX', 'Xxx-Yyy', None
    """
    if not region:
        return None

    # 1. Nettoyer : enlever "REGION :", ":", et "(N avis)"
    texte = region.strip()
    texte = re.sub(r"^REGION\s*:\s*", "", texte, flags=re.IGNORECASE)
    texte = re.sub(r"\s*\(\d+\s*avis\)\s*$", "", texte, flags=re.IGNORECASE)
    texte = texte.strip().upper()

    # 2. Chercher dans le mapping
    if texte in MAPPING_REGIONS:
        return MAPPING_REGIONS[texte]

    # 3. Sinon, on garde tel quel (mais propre)
    return region.strip()


def main():
    print("=" * 60)
    print("NORMALISATION DES RÉGIONS")
    print("=" * 60)

    # 1. Récupérer toutes les valeurs uniques
    valeurs_uniques = set(
        AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
        .values_list("region", flat=True)
    )

    print(f"\n{len(valeurs_uniques)} valeurs uniques à traiter :\n")

    # 2. Compter les modifications
    modifications = 0
    compteur = {}

    for valeur in valeurs_uniques:
        nouvelle_valeur = normaliser_nom(valeur)

        if nouvelle_valeur != valeur:
            nb = AppelOffre.objects.filter(region=valeur).update(region=nouvelle_valeur)
            modifications += nb
            compteur[valeur] = (nouvelle_valeur, nb)
            print(f"  {repr(valeur)[:55]:55} → {nouvelle_valeur:25} ({nb} AO)")

    print()
    print("=" * 60)
    print("BILAN")
    print("=" * 60)
    print(f"AO modifiés : {modifications}")

    # 3. Vérification : afficher les nouvelles valeurs
    print("\nNouvelles valeurs en base :")
    nouvelles_valeurs = set(
        AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
        .values_list("region", flat=True)
    )
    for v in sorted(nouvelles_valeurs):
        nb = AppelOffre.objects.filter(region=v).count()
        print(f"  {v:30} : {nb} AO")


if __name__ == "__main__":
    main()