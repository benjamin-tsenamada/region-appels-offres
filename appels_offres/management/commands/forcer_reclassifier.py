"""
Force une reclassification complète :
1. Supprime TOUS les ClassificationLog
2. Vide le secteur de TOUS les AppelOffre
3. Reclasse tout avec le modèle NLP actuel

Usage :
    python manage.py forcer_reclassifier
"""

from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre, Secteur, ClassificationLog
from appels_offres.ml.classifier import predict_secteur


class Command(BaseCommand):
    help = "Force une reclassification complète de tous les AO"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== Forçage de la reclassification ==="))

        # Étape 1 : Nettoyer les logs
        nb_logs = ClassificationLog.objects.count()
        ClassificationLog.objects.all().delete()
        self.stdout.write(f"[OK] {nb_logs} ClassificationLog supprimés")

        # Étape 2 : Vider les secteurs
        nb_ao = AppelOffre.objects.count()
        AppelOffre.objects.update(secteur=None)
        self.stdout.write(f"[OK] {nb_ao} AO - secteur vidé")

        # Étape 3 : Reclassifier
        secteurs_db = {s.nom.lower(): s for s in Secteur.objects.all()}
        if not secteurs_db:
            self.stdout.write(self.style.ERROR("[ERREUR] Aucun secteur en base"))
            return

        total = AppelOffre.objects.count()
        self.stdout.write(f"[INFO] Reclassification de {total} AO...")

        classes = 0
        erreurs = 0

        for i, ao in enumerate(AppelOffre.objects.all(), 1):
            try:
                texte = f"{ao.titre} {ao.description}"
                secteur_nom, confiance = predict_secteur(texte)

                if secteur_nom:
                    secteur_obj = secteurs_db.get(secteur_nom.lower())
                    if secteur_obj:
                        ao.secteur = secteur_obj
                        ao.save(update_fields=["secteur"])
                        ClassificationLog.objects.create(
                            appel_offre=ao,
                            texte_source=texte[:2000],
                            secteur_predit=secteur_obj,
                            confiance=confiance,
                        )
                        classes += 1

                if i % 200 == 0:
                    self.stdout.write(f"  ... {i}/{total} traités")

            except Exception as e:
                erreurs += 1
                self.stdout.write(self.style.WARNING(f"[ERREUR] AO #{ao.id} : {e}"))

        # Bilan
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Forçage terminé ==="))
        self.stdout.write(f"Classifiés : {classes}")
        self.stdout.write(f"Erreurs    : {erreurs}")

        # Confiance moyenne
        if classes > 0:
            moyenne = sum(l.confiance for l in ClassificationLog.objects.all()) / classes * 100
            self.stdout.write(self.style.SUCCESS(f"Confiance moyenne : {moyenne:.1f}%"))