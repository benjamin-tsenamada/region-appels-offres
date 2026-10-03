"""
Commande : python manage.py evaluate_model

Calcule les métriques du modèle à partir des ClassificationLog
où le secteur_reel a été renseigné manuellement.
Affiche : précision, rappel, F1-score + matrice de confusion.
"""
from django.core.management.base import BaseCommand
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)
from appels_offres.models import ClassificationLog


class Command(BaseCommand):
    help = "Évalue le modèle ML (précision, rappel, F1) via les ClassificationLog vérifiés"

    def handle(self, *args, **options):
        # On ne garde que les logs où on a renseigné le secteur réel
        logs = ClassificationLog.objects.filter(
            secteur_reel__isnull=False,
            secteur_predit__isnull=False,
        ).select_related("secteur_reel", "secteur_predit")

        if logs.count() < 2:
            self.stdout.write(self.style.ERROR(
                "❌ Il faut au moins 2 ClassificationLog avec secteur_reel renseigné."
            ))
            return

        y_true = [log.secteur_reel.nom for log in logs]
        y_pred = [log.secteur_predit.nom for log in logs]

        self.stdout.write(f"\n📊 Évaluation sur {logs.count()} prédictions vérifiées\n")

        # Métriques globales
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

        self.stdout.write(self.style.SUCCESS(f"✅ Accuracy  : {acc:.3f}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Précision : {prec:.3f}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Rappel    : {rec:.3f}"))
        self.stdout.write(self.style.SUCCESS(f"✅ F1-score  : {f1:.3f}\n"))

        # Rapport détaillé
        self.stdout.write("📋 Rapport par classe :\n")
        self.stdout.write(classification_report(y_true, y_pred, zero_division=0))

        # Matrice de confusion
        self.stdout.write("\n🧩 Matrice de confusion :")
        labels = sorted(set(y_true) | set(y_pred))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        self.stdout.write("      " + "  ".join(f"{l[:8]:>8}" for l in labels))
        for i, lab in enumerate(labels):
            row = "  ".join(f"{v:>8}" for v in cm[i])
            self.stdout.write(f"{lab[:6]:>6} {row}")