from django.db import models
from django.contrib.auth.models import User


class Secteur(models.Model):
    """Travaux, Fournitures, Services, Prestations intellectuelles"""
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class TypeProcedure(models.Model):
    """AOO, AOR, AMI, APQ, gré à gré..."""
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # ex: "AOO"

    def __str__(self):
        return f"{self.code} - {self.nom}"


class District(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nom


class AppelOffre(models.Model):
    STATUT_CHOICES = [
        ("publie", "Publié"),
        ("en_cours", "En cours"),
        ("attribue", "Attribué"),
        ("infructueux", "Infructueux"),
    ]

    titre = models.CharField(max_length=255)
    description = models.TextField(help_text="Texte source utilisé pour la classification automatique")
    autorite_contractante = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    secteur = models.ForeignKey(Secteur, on_delete=models.SET_NULL, null=True, related_name="appels_offre")
    type_procedure = models.ForeignKey(TypeProcedure, on_delete=models.SET_NULL, null=True, related_name="appels_offre")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name="appels_offre")

    date_publication = models.DateField()
    date_limite = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="publie")

    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="appels_offre_crees")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

    class Meta:
        ordering = ["-date_publication"]


class ClassificationLog(models.Model):
    """
    Trace chaque prédiction du modèle NLP : indispensable pour l'évaluation
    (précision / rappel / F1-score) demandée dans le mémoire.
    """
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE, related_name="classifications")
    texte_source = models.TextField()
    secteur_predit = models.ForeignKey(Secteur, on_delete=models.SET_NULL, null=True)
    secteur_reel = models.ForeignKey(
        Secteur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verifications",
        help_text="Rempli manuellement lors de la vérification, pour calculer les métriques du modèle"
    )
    confiance = models.FloatField(help_text="Score de confiance du modèle (0 à 1)")
    date_prediction = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prédiction #{self.id} - {self.appel_offre.titre}"