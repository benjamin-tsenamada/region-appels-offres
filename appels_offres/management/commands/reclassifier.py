"""
Re-classifie tous les AO qui n'ont pas encore de secteur prédit.
Utile après un import ARMP massif ou pour rattraper les AO non classifiés.

Usage :
    python manage.py reclassifier
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from appels_offres.models import AppelOffre, Secteur, ClassificationLog
from appels_offres.ml.classifier import predict_secteur


class Command(BaseCommand):
    help = "Classifie automatiquement tous les AO qui n'ont pas encore de secteur prédit"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Reclassification démarrée ==="))

        # AO sans secteur
        a_classifier = AppelOffre.objects.filter(secteur__isnull=True)
        total = a_classifier.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("[INFO] Tous les AO sont déjà classifiés."))
            return

        self.stdout.write(f"[INFO] {total} AO à classifier...")

        secteurs_db = {s.nom.lower(): s for s in Secteur.objects.all()}
        classes = 0
        erreurs = 0

        for i, ao in enumerate(a_classifier, 1):
            texte = f"{ao.titre} {ao.description}"
            try:
                secteur_predit_nom, confiance = predict_secteur(texte)

                if secteur_predit_nom:
                    secteur_obj = secteurs_db.get(secteur_predit_nom.lower())
                    if secteur_obj:
                        ao.secteur = secteur_obj
                        ao.save()

                        ClassificationLog.objects.create(
                            appel_offre=ao,
                            texte_source=texte[:2000],
                            secteur_predit=secteur_obj,
                            confiance=confiance,
                        )
                        classes += 1

                if i % 100 == 0:
                    self.stdout.write(f"  ... {i}/{total} traités")

            except Exception as e:
                erreurs += 1
                self.stdout.write(self.style.WARNING(f"[ERREUR] AO #{ao.id} : {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Reclassification terminée ==="))
        self.stdout.write(f"Classifiés : {classes}")
        self.stdout.write(f"Erreurs    : {erreurs}")
        self.stdout.write(f"Total      : {total}")