"""
Commande Django : python manage.py train_classifier
Entraîne le modèle de classification à partir des AO ayant un secteur défini.
"""
from collections import Counter

from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre
from appels_offres.ml.classifier import train_and_save


class Command(BaseCommand):
    help = "Entraîne le modèle de classification du secteur"

    def handle(self, *args, **options):
        appels = AppelOffre.objects.exclude(secteur__isnull=True)

        total = appels.count()
        if total < 10:
            self.stdout.write(self.style.ERROR(
                f"Seulement {total} AO étiquetés. Il en faut au moins 10 pour entraîner."
            ))
            return

        textes = [f"{a.titre} {a.description}" for a in appels]
        labels = [a.secteur.nom for a in appels]

        # Statistiques par secteur
        repartition = Counter(labels)
        self.stdout.write(self.style.WARNING(f"=== Entraînement sur {total} exemples ==="))
        for secteur, nb in sorted(repartition.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  {secteur:30} : {nb} exemples")

        if len(set(labels)) < 2:
            self.stdout.write(self.style.ERROR(
                "Il faut au moins 2 secteurs différents pour entraîner."
            ))
            return

        self.stdout.write("")
        self.stdout.write("Entraînement du modèle SVM en cours...")

        train_and_save(textes, labels)

        self.stdout.write(self.style.SUCCESS(
            f"Modèle entraîné avec succès sur {total} exemples "
            f"({len(set(labels))} secteurs)."
        ))