"""
Commande : python manage.py classify_ao

Classe automatiquement tous les appels d'offres qui n'ont pas encore
de ClassificationLog, ou dont le secteur est NULL.
"""
from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre, Secteur, ClassificationLog
from appels_offres.ml.classifier import predict_secteur


class Command(BaseCommand):
    help = "Classifie automatiquement le secteur des appels d'offres via le modèle ML"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tout",
            action="store_true",
            help="Reclassifier TOUS les AO (même ceux déjà classés)",
        )

    def handle(self, *args, **options):
        # 1. Récupérer les AO à classer
        if options["tout"]:
            appels = AppelOffre.objects.all()
        else:
            appels = AppelOffre.objects.filter(secteur__isnull=True)

        if not appels.exists():
            self.stdout.write(self.style.WARNING("Aucun appel d'offres à classifier."))
            return

        self.stdout.write(f"📊 {appels.count()} appel(s) d'offres à classifier...\n")

        ok, echecs = 0, 0

        for ao in appels:
            texte = f"{ao.titre} {ao.description}"
            secteur_nom, confiance = predict_secteur(texte)

            if secteur_nom is None:
                self.stdout.write(self.style.ERROR(
                    f"  ❌ [{ao.id}] {ao.titre[:60]} → modèle introuvable"
                ))
                echecs += 1
                continue

            # Récupérer ou créer le Secteur
            secteur, _ = Secteur.objects.get_or_create(nom=secteur_nom)

            # Mettre à jour l'AO
            ao.secteur = secteur
            ao.save(update_fields=["secteur"])

            # Tracer dans ClassificationLog
            ClassificationLog.objects.create(
                appel_offre=ao,
                texte_source=texte,
                secteur_predit=secteur,
                confiance=confiance,
            )

            self.stdout.write(self.style.SUCCESS(
                f"  ✅ [{ao.id}] {ao.titre[:60]} → {secteur_nom} ({confiance:.2f})"
            ))
            ok += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Terminé : {ok} classifié(s), {echecs} échec(s)."
        ))