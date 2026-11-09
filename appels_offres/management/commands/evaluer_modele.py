from django.core.management.base import BaseCommand
from appels_offres.models import AppelOffre
from appels_offres.ml.classifier import load_model
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd

class Command(BaseCommand):
    help = "Évalue le modèle IA avec une validation croisée (train/test)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Chargement des données...")
        appels = AppelOffre.objects.exclude(secteur__isnull=True).exclude(titre="")
        
        if appels.count() < 10:
            self.stdout.write(self.style.ERROR("Pas assez de données pour évaluer."))
            return

        # On utilise le texte (titre + description) et le secteur réel (étiquette)
        textes = [f"{a.titre} {a.description or ''}" for a in appels]
        labels_reels = [a.secteur.nom for a in appels]

        self.stdout.write(f"Évaluation sur {len(textes)} exemples...")
        
        modele = load_model()
        if not modele:
            self.stdout.write(self.style.ERROR("Le modèle n'est pas entraîné."))
            return

        # Prédictions
        predictions = modele.predict(textes)

        self.stdout.write("\n--- RAPPORT DE CLASSIFICATION ---")
        report = classification_report(labels_reels, predictions, zero_division=0)
        self.stdout.write(report)

        self.stdout.write("\n--- MATRICE DE CONFUSION ---")
        cm = confusion_matrix(labels_reels, predictions)
        # Affichage simple de la matrice
        labels_uniques = sorted(list(set(labels_reels)))
        df_cm = pd.DataFrame(cm, index=labels_uniques, columns=labels_uniques)
        self.stdout.write(str(df_cm))

        self.stdout.write(self.style.SUCCESS("Évaluation terminée avec succès !"))