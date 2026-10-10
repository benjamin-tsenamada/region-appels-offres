"""
Étiquetage automatique des AO par règles métier (mots-clés).
Utilisé pour créer un jeu d'entraînement de qualité à partir des données réelles.

Usage :
    python manage.py etiqueter_auto
"""

import re

from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre, Secteur


# Règles d'étiquetage basées sur des mots-clés (par ordre de priorité)
REGLES = [
    # 1. Prestations intellectuelles (avant Travaux car "étude de" est plus spécifique)
    ("Prestations intellectuelles", [
        r"\bétude\b", r"\bétudes\b", r"\baudit", r"\bexpertise",
        r"\bconseil", r"\bformation\b", r"\bassistance\s+technique",
        r"\bmaîtrise\s+d.ouvrage", r"\bconsultation", r"\bdiagnostic",
        r"\bévaluation", r"\bévaluations", r"\bplanification",
        r"\bschéma\s+directeur", r"\bstratégie", r"\bétat\s+des\s+lieux",
        r"\bréalisation\s+d.une\s+étude",
    ]),

    # 2. Travaux (construction, réhabilitation, etc.)
    ("Travaux", [
        r"\btravaux\b", r"\bconstruction", r"\bréhabilitation", r"\bréfection",
        r"\baménagement", r"\bréparation", r"\bbâtiment", r"\bbâtiments\b",
        r"\broute\b", r"\broutes\b", r"\bpont\b", r"\bponts\b",
        r"\bforage", r"\bforages\b", r"\badduction\s+d.eau",
        r"\bassainissement", r"\bdallage", r"\bmaçonnerie",
        r"\bpeinture", r"\btoiture", r"\bfondation", r"\bvoirie",
        r"\bterrassement", r"\bpavage", r"\bimmeuble",
        r"\bouvrage", r"\bouvrages\b", r"\bcanalisation",
        r"\bpiste", r"\bpistes\b", r"\btravaux\s+de",
    ]),

    # 3. Services (nettoyage, gardiennage, etc.)
    ("Services", [
        r"\bnettoyage", r"\bentretien", r"\bgardiennage", r"\bsécurité",
        r"\bsurveillance", r"\btransport", r"\blocation\s+de\s+véhicule",
        r"\bmaintenance", r"\brestauration", r"\bhôtellerie",
        r"\bhébergement", r"\breprographie", r"\bimpression\s+de\s+documents",
        r"\borganisation\s+de", r"\bprestation\s+de\s+service",
        r"\bassurance", r"\bnettoyages", r"\bentretiens",
    ]),

    # 4. Fournitures (par défaut, si rien d'autre ne correspond)
    ("Fournitures", [
        r"\bfourniture", r"\bfournitures\b", r"\bacqui", r"\bachat",
        r"\blivraison", r"\bmatériel", r"\bmatériels\b", r"\béquipement",
        r"\béquipements\b", r"\bconsommable", r"\bconsommables\b",
        r"\bproduit", r"\bproduits\b", r"\barticle", r"\barticles\b",
        r"\bfournir", r"\bapprovisionnement", r"\bmobilier",
        r"\binformatique", r"\bvéhicule", r"\bvéhicules\b",
        r"\bmédicament", r"\bmédicaments\b", r"\bpharmaceutique",
        r"\bsemence", r"\bsemences\b", r"\bengrais",
        r"\bpapeterie", r"\bmanuels?\s+scolaires",
    ]),
]


def deviner_secteur(texte):
    """Retourne le nom du secteur deviné par règles."""
    texte_lower = texte.lower()

    for secteur_nom, patterns in REGLES:
        for pattern in patterns:
            if re.search(pattern, texte_lower):
                return secteur_nom
    return None


class Command(BaseCommand):
    help = "Étiquette automatiquement les AO par règles (mots-clés) pour créer un jeu d'entraînement"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Réinitialise tous les secteurs avant étiquetage"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Étiquetage automatique ==="))

        # Récupérer ou créer les 4 secteurs
        secteurs = {}
        for nom in ["Travaux", "Fournitures", "Services", "Prestations intellectuelles"]:
            s, _ = Secteur.objects.get_or_create(nom=nom)
            secteurs[nom] = s

        # Option : reset
        if options["reset"]:
            AppelOffre.objects.update(secteur=None)
            self.stdout.write("[INFO] Tous les secteurs ont été réinitialisés")

        # Étiqueter les AO sans secteur
        a_etiqueter = AppelOffre.objects.filter(secteur__isnull=True)
        total = a_etiqueter.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("[INFO] Tous les AO ont déjà un secteur"))
            return

        self.stdout.write(f"[INFO] {total} AO à étiqueter...")

        stats = {"Travaux": 0, "Fournitures": 0, "Services": 0, "Prestations intellectuelles": 0}
        non_classes = 0

        for ao in a_etiqueter:
            texte = f"{ao.titre} {ao.description}"
            secteur_nom = deviner_secteur(texte)

            if secteur_nom and secteur_nom in secteurs:
                ao.secteur = secteurs[secteur_nom]
                ao.save(update_fields=["secteur"])
                stats[secteur_nom] += 1
            else:
                non_classes += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Étiquetage terminé ==="))
        for nom, nb in stats.items():
            self.stdout.write(f"  {nom:30} : {nb}")
        self.stdout.write(f"  Non classifiés : {non_classes}")
        self.stdout.write(f"  TOTAL          : {sum(stats.values()) + non_classes}")