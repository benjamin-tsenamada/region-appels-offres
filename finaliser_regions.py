import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from appels_offres.models import AppelOffre


# Les 2 valeurs résiduelles à corriger
CORRECTIONS = {
    "Ambatosoa": "Alaotra-Mangoro",
    "REGION : AMBATOSOA (10 avis)": "Alaotra-Mangoro",
}


def main():
    print("=" * 60)
    print("FINITION DES RÉGIONS")
    print("=" * 60)

    total = 0
    for ancien, nouveau in CORRECTIONS.items():
        nb = AppelOffre.objects.filter(region=ancien).update(region=nouveau)
        if nb > 0:
            print(f"  {ancien!r:45} → {nouveau!r:20} ({nb} AO)")
            total += nb

    print()
    print(f"Total AO corrigés : {total}")

    print()
    print("=" * 60)
    print("VÉRIFICATION FINALE")
    print("=" * 60)

    valeurs = (
        AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
        .values_list("region", flat=True)
    )
    from collections import Counter
    compteur = Counter(valeurs)
    for v, nb in sorted(compteur.items()):
        print(f"  {v:30} : {nb} AO")

    print()
    print(f"Total régions distinctes : {len(compteur)}")


if __name__ == "__main__":
    main()