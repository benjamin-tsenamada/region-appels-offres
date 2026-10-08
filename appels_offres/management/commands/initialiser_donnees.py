"""
Commande Django pour initialiser la base de production :
- Crée un super-utilisateur admin si absent
- Crée les secteurs, types de procédure, districts
- Crée des appels d'offres de démonstration
- Crée des classifications IA (pour la page Performance IA)

Lancement :
    python manage.py initialiser_donnees

Cette commande est IDEMPOTENTE : si les données existent déjà, elle ne les recrée pas.
"""

import os
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from appels_offres.models import (
    Secteur, TypeProcedure, District, AppelOffre, ClassificationLog
)


class Command(BaseCommand):
    help = "Initialise la base de données avec les données de démonstration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Initialisation des données ==="))

        with transaction.atomic():

            # ============================================
            # 1. SUPER-UTILISATEUR
            # ============================================
            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "benjaminelphege@gmail.com")
            password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "Region2026!")

            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"[OK] Super-utilisateur '{username}' créé"))
            else:
                self.stdout.write(f"[SKIP] Super-utilisateur '{username}' existe déjà")

            # ============================================
            # 2. SECTEURS
            # ============================================
            secteurs_noms = ["Travaux", "Fournitures", "Services", "Prestations intellectuelles"]
            secteurs = {}
            for nom in secteurs_noms:
                s, created = Secteur.objects.get_or_create(nom=nom)
                secteurs[nom] = s
                if created:
                    self.stdout.write(self.style.SUCCESS(f"[OK] Secteur '{nom}' créé"))

            # ============================================
            # 3. TYPES DE PROCÉDURE
            # ============================================
            types_data = [
                ("AOO", "Appel d'Offres Ouvert"),
                ("AOR", "Appel d'Offres Restreint"),
                ("AMI", "Appel à Manifestation d'Intérêt"),
                ("APQ", "Appel à Prix Quotidien"),
            ]
            types_proc = {}
            for code, nom in types_data:
                t, created = TypeProcedure.objects.get_or_create(code=code, defaults={"nom": nom})
                types_proc[code] = t
                if created:
                    self.stdout.write(self.style.SUCCESS(f"[OK] Type '{code}' créé"))

            # ============================================
            # 4. DISTRICTS D'ATSIMO-ANDREFANA
            # ============================================
            districts_data = [
                ("Toliara I", -23.3560, 43.6667),
                ("Toliara II", -23.4167, 43.5833),
                ("Sakaraha", -22.9167, 44.5333),
                ("Betioky", -23.7167, 44.3833),
                ("Ampanihy", -24.7000, 44.7500),
                ("Ankazoabo", -22.2833, 44.5167),
                ("Benenitra", -23.4500, 45.0833),
                ("Beroroha", -21.6667, 45.1667),
                ("Morombe", -21.7500, 43.3667),
            ]
            districts = {}
            for nom, lat, lng in districts_data:
                d, created = District.objects.get_or_create(
                    nom=nom, defaults={"latitude": lat, "longitude": lng}
                )
                districts[nom] = d
                if created:
                    self.stdout.write(self.style.SUCCESS(f"[OK] District '{nom}' créé"))

            # ============================================
            # 5. APPELS D'OFFRES DE DÉMONSTRATION
            # ============================================
            aujourd_hui = date.today()
            appels_data = [
                {
                    "titre": "Acquisition de matériel informatique pour les services régionaux",
                    "description": "Fourniture de 50 ordinateurs portables, 20 imprimantes et accessoires pour les bureaux de la Région Atsimo-Andrefana.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("250000000"),
                    "secteur": "Fournitures",
                    "type": "AOO",
                    "district": "Toliara I",
                    "statut": "publie",
                    "date_limite_jours": 5,
                },
                {
                    "titre": "Prestation de nettoyage et d'entretien des locaux administratifs régionaux",
                    "description": "Nettoyage quotidien des bâtiments administratifs, désinfection et entretien des espaces verts.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("85000000"),
                    "secteur": "Services",
                    "type": "AOO",
                    "district": "Toliara II",
                    "statut": "publie",
                    "date_limite_jours": 8,
                },
                {
                    "titre": "Étude de faisabilité pour la construction de forages d'eau potable",
                    "description": "Réalisation d'une étude de faisabilité technique et environnementale pour 15 forages dans la zone sud de la région.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("120000000"),
                    "secteur": "Prestations intellectuelles",
                    "type": "AMI",
                    "district": "Ampanihy",
                    "statut": "attribue",
                    "date_limite_jours": 15,
                },
                {
                    "titre": "Fourniture de semences agricoles pour la campagne 2026",
                    "description": "Achat et distribution de semences de maïs, riz et manioc aux agriculteurs des districts du sud.",
                    "autorite_contractante": "Direction Régionale de l'Agriculture",
                    "montant": Decimal("350000000"),
                    "secteur": "Fournitures",
                    "type": "AOO",
                    "district": "Sakaraha",
                    "statut": "en_cours",
                    "date_limite_jours": 3,
                },
                {
                    "titre": "Réhabilitation de la route rurale reliant Betioky à Ejeda",
                    "description": "Travaux de réhabilitation de 45 km de route en terre, incluant le traitement des points critiques.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("850000000"),
                    "secteur": "Travaux",
                    "type": "AOO",
                    "district": "Betioky",
                    "statut": "publie",
                    "date_limite_jours": 12,
                },
                {
                    "titre": "Construction d'un centre de santé de base à Ankazoabo",
                    "description": "Construction d'un CSB2 avec 20 lits, bloc opératoire, pharmacie et logements pour le personnel.",
                    "autorite_contractante": "Direction Régionale de la Santé",
                    "montant": Decimal("620000000"),
                    "secteur": "Travaux",
                    "type": "AOR",
                    "district": "Ankazoabo",
                    "statut": "publie",
                    "date_limite_jours": 20,
                },
                {
                    "titre": "Audit technique et financier du programme d'adduction d'eau",
                    "description": "Audit des dépenses et de la mise en œuvre technique du programme régional d'AEP sur 3 ans.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("75000000"),
                    "secteur": "Prestations intellectuelles",
                    "type": "AMI",
                    "district": "Toliara I",
                    "statut": "attribue",
                    "date_limite_jours": 25,
                },
                {
                    "titre": "Acquisition de 4 véhicules tout-terrain pour les services techniques",
                    "description": "Achat de 4 pick-up 4x4 diesel, équipés pour les interventions techniques dans les zones enclavées.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("480000000"),
                    "secteur": "Fournitures",
                    "type": "AOO",
                    "district": "Toliara I",
                    "statut": "en_cours",
                    "date_limite_jours": 2,
                },
                {
                    "titre": "Prestation de gardiennage et sécurité des bâtiments régionaux",
                    "description": "Service de sécurité 24h/24 pour les 5 principaux bâtiments administratifs de la Région.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("95000000"),
                    "secteur": "Services",
                    "type": "AOO",
                    "district": "Toliara I",
                    "statut": "publie",
                    "date_limite_jours": 10,
                },
                {
                    "titre": "Aménagement de 12 km de pistes rurales dans le district de Morombe",
                    "description": "Travaux de désenclavement de la zone côtière : reprofilage, ouvrages de franchissement, signalisation.",
                    "autorite_contractante": "Région Atsimo-Andrefana",
                    "montant": Decimal("290000000"),
                    "secteur": "Travaux",
                    "type": "APQ",
                    "district": "Morombe",
                    "statut": "publie",
                    "date_limite_jours": 7,
                },
            ]

            crees = 0
            for data in appels_data:
                if AppelOffre.objects.filter(titre=data["titre"]).exists():
                    continue
                ao = AppelOffre.objects.create(
                    titre=data["titre"],
                    description=data["description"],
                    autorite_contractante=data["autorite_contractante"],
                    montant=data["montant"],
                    secteur=secteurs[data["secteur"]],
                    type_procedure=types_proc[data["type"]],
                    district=districts[data["district"]],
                    date_publication=aujourd_hui - timedelta(days=random.randint(1, 10)),
                    date_limite=aujourd_hui + timedelta(days=data["date_limite_jours"]),
                    statut=data["statut"],
                )
                crees += 1

                # Classification IA simulée
                confiance = round(random.uniform(0.70, 0.95), 2)
                ClassificationLog.objects.create(
                    appel_offre=ao,
                    texte_source=ao.description,
                    secteur_predit=secteurs[data["secteur"]],
                    confiance=confiance,
                )

            if crees > 0:
                self.stdout.write(self.style.SUCCESS(f"[OK] {crees} appels d'offres créés (avec classifications)"))

        self.stdout.write(self.style.SUCCESS("=== Initialisation terminée ==="))