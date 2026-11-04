"""
Script de nettoyage géographique — usage unique.
Corrige :
- Suppression de la région doublon "Ambatosoa"
- Rattachement des 9 districts orphelins à Atsimo-Andrefana
- Fusion des districts doublons (Betioky Atsimo → Betioky, Ampanihy Ouest → Ampanihy)
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from appels_offres.models import Region, District, AppelOffre


def main():
    print("=" * 60)
    print("NETTOYAGE GEOGRAPHIQUE")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Supprimer la région "Ambatosoa" (doublon d'Alaotra-Mangoro)
    # ---------------------------------------------------------
    try:
        ambatosoa = Region.objects.get(nom="Ambatosoa")
        alaotra = Region.objects.get(nom="Alaotra-Mangoro")
        # Réassigner les districts d'Ambatosoa vers Alaotra-Mangoro
        District.objects.filter(region=ambatosoa).update(region=alaotra)
        ambatosoa.delete()
        print("[OK] Région 'Ambatosoa' supprimée (fusionnée dans Alaotra-Mangoro)")
    except Region.DoesNotExist:
        print("[SKIP] Région 'Ambatosoa' déjà absente")

    # ---------------------------------------------------------
    # 2. Rattacher les districts orphelins à Atsimo-Andrefana
    # ---------------------------------------------------------
    atsimo = Region.objects.get(nom="Atsimo-Andrefana")

    orphelins = District.objects.filter(region__isnull=True)
    nb_orphelins = orphelins.count()
    if nb_orphelins > 0:
        orphelins.update(region=atsimo)
        print(f"[OK] {nb_orphelins} districts orphelins rattachés à Atsimo-Andrefana")
    else:
        print("[SKIP] Aucun district orphelin")

    # ---------------------------------------------------------
    # 3. Fusionner les districts doublons
    # ---------------------------------------------------------
    # Cas : "Betioky Atsimo" (ancien, sans région) → "Betioky" (nouveau, avec région)
    # Cas : "Ampanihy Ouest" (ancien) → "Ampanihy" (nouveau)

    fusions = [
        ("Betioky Atsimo", "Betioky", "Atsimo-Andrefana"),
        ("Ampanihy Ouest", "Ampanihy", "Atsimo-Andrefana"),
    ]

    for ancien_nom, nouveau_nom, region_nom in fusions:
        try:
            ancien = District.objects.get(nom=ancien_nom)
            nouveau = District.objects.filter(nom=nouveau_nom, region__nom=region_nom).first()
            if nouveau and ancien.id != nouveau.id:
                # Transférer les AO liés
                nb_ao = AppelOffre.objects.filter(district=ancien).count()
                AppelOffre.objects.filter(district=ancien).update(district=nouveau)
                ancien.delete()
                print(f"[OK] '{ancien_nom}' fusionné dans '{nouveau_nom}' ({nb_ao} AO transférés)")
            elif not nouveau:
                # Pas de doublon en face, on renomme simplement
                ancien.nom = nouveau_nom
                ancien.save()
                print(f"[OK] '{ancien_nom}' renommé en '{nouveau_nom}'")
        except District.DoesNotExist:
            print(f"[SKIP] '{ancien_nom}' introuvable")

    # ---------------------------------------------------------
    # 4. Bilan final
    # ---------------------------------------------------------
    print()s
    print("=" * 60)
    print("BILAN")
    print("=" * 60)
    print("Régions  :", Region.objects.count())
    print("Districts:", District.objects.count())
    print()
    print("Détail par région :")
    for r in Region.objects.all().order_by("nom"):
        print(f"  {r.nom:30} : {r.districts.count()} districts")


if __name__ == "__main__":
    main()