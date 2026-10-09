"""
Import des AO depuis le portail ARMP + classification automatique par le modèle NLP.
"""

from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from appels_offres.models import (
    AppelOffre, Secteur, TypeProcedure, ClassificationLog
)
from appels_offres.scrapers.armp import extraire_tous_les_ao
from appels_offres.ml.classifier import predict_secteur


class Command(BaseCommand):
    help = "Importe les AO depuis le portail ARMP et les classifie automatiquement"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Import ARMP démarré ==="))

        try:
            tous_les_ao = extraire_tous_les_ao()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERREUR] {e}"))
            return

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(tous_les_ao)} AO extraits"))

        limit = options.get("limit")
        if limit:
            tous_les_ao = tous_les_ao[:limit]

        types_proc = {t.code: t for t in TypeProcedure.objects.all()}
        secteurs_db = {s.nom.lower(): s for s in Secteur.objects.all()}

        numeros_existants = set(
            AppelOffre.objects.filter(source="ARMP").exclude(numero_armp__isnull=True)
            .values_list("numero_armp", flat=True)
        )

        crees = 0
        ignores = 0
        classes = 0

        for ao in tous_les_ao:
            numero = ao.get("numero") or ""

            if numero and numero in numeros_existants:
                ignores += 1
                continue

            date_publication = None
            date_limite = None
            try:
                if ao.get("date_debut"):
                    date_publication = datetime.strptime(ao["date_debut"], "%Y-%m-%d").date()
                if ao.get("date_fin"):
                    date_limite = datetime.strptime(ao["date_fin"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

            if not date_publication or not date_limite:
                ignores += 1
                continue

            type_proc = types_proc.get(ao.get("mode", ""))

            try:
                with transaction.atomic():
                    nouveau = AppelOffre.objects.create(
                        titre=ao.get("objet", "")[:500],
                        description=ao.get("objet", ""),
                        autorite_contractante=ao.get("entite", "")[:255],
                        type_procedure=type_proc,
                        date_publication=date_publication,
                        date_limite=date_limite,
                        statut="publie",
                        source="ARMP",
                        region=ao.get("region_officielle", "")[:150] if ao.get("region_officielle") else None,
                        reference_armp=(ao.get("reference") or "")[:255] or None,
                        numero_armp=numero[:100] if numero else None,
                        mode_passation=(ao.get("mode") or "")[:20] or None,
                        url_source=(ao.get("lien_fiche") or "")[:500] or None,
                    )
                    crees += 1
                    if numero:
                        numeros_existants.add(numero)

                    # ---- CLASSIFICATION AUTOMATIQUE ----
                    texte_a_classifier = f"{nouveau.titre} {nouveau.description}"
                    secteur_predit_nom, confiance = predict_secteur(texte_a_classifier)

                    if secteur_predit_nom:
                        secteur_obj = secteurs_db.get(secteur_predit_nom.lower())
                        if secteur_obj:
                            nouveau.secteur = secteur_obj
                            nouveau.save()

                            ClassificationLog.objects.create(
                                appel_offre=nouveau,
                                texte_source=texte_a_classifier[:2000],
                                secteur_predit=secteur_obj,
                                confiance=confiance,
                            )
                            classes += 1

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"[SKIP] {e}"))
                ignores += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Import terminé ==="))
        self.stdout.write(f"Créés        : {crees}")
        self.stdout.write(f"Classifiés   : {classes}")
        self.stdout.write(f"Ignorés      : {ignores}")