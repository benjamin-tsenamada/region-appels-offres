"""
Commande Django : python manage.py train_classifier
Entraîne le modèle de classification à partir des appels d'offres déjà saisis.
"""
from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre
from appels_offres.ml.classifier import train_and_save


class Command(BaseCommand):
    help = "Entraîne le modèle de classification du secteur à partir des appels d'offres en base."

    def handle(self, *args, **options):
        appels = AppelOffre.objects.exclude(secteur__isnull=True)

        if appels.count() < 4:
            self.stdout.write(self.style.WARNING(
                f"Seulement {appels.count()} appel(s) d'offres trouvé(s). "
                "Ajoute plus d'exemples pour un modèle plus fiable."
            ))

        textes = [f"{a.titre} {a.description}" for a in appels]
        labels = [a.secteur.nom for a in appels]

        if len(set(labels)) < 2:
            self.stdout.write(self.style.ERROR(
                "Il faut au moins 2 secteurs différents en base pour entraîner un modèle."
            ))
            return

        train_and_save(textes, labels)

        self.stdout.write(self.style.SUCCESS(
            f"Modèle entraîné avec succès sur {len(textes)} exemples "
            f"({len(set(labels))} secteurs différents)."
        ))