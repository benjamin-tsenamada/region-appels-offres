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
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.code} - {self.nom}"


class Region(models.Model):
    """Les 22 régions de Madagascar."""
    nom = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.nom

    class Meta:
        ordering = ["nom"]


class District(models.Model):
    nom = models.CharField(max_length=150)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts", null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.region.nom if self.region else '—'})"

    class Meta:
        ordering = ["region__nom", "nom"]


class AppelOffre(models.Model):
    STATUT_CHOICES = [
        ("publie", "Publié"),
        ("en_cours", "En cours"),
        ("attribue", "Attribué"),
        ("infructueux", "Infructueux"),
    ]

    SOURCE_CHOICES = [
        ("DEMO", "Données de démonstration"),
        ("ARMP", "Portail ARMP"),
    ]

    titre = models.CharField(max_length=500)
    description = models.TextField(help_text="Texte source utilisé pour la classification automatique")
    autorite_contractante = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    secteur = models.ForeignKey(Secteur, on_delete=models.SET_NULL, null=True, blank=True, related_name="appels_offre")
    type_procedure = models.ForeignKey(TypeProcedure, on_delete=models.SET_NULL, null=True, blank=True, related_name="appels_offre")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name="appels_offre")

    date_publication = models.DateField()
    date_limite = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="publie")

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default="DEMO")
    region = models.CharField(max_length=150, blank=True, null=True)
    reference_armp = models.CharField(max_length=255, blank=True, null=True)
    numero_armp = models.CharField(max_length=100, blank=True, null=True)
    mode_passation = models.CharField(max_length=20, blank=True, null=True)
    url_source = models.URLField(max_length=500, blank=True, null=True)
    date_import = models.DateTimeField(auto_now_add=True)

    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="appels_offre_crees")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

    class Meta:
        ordering = ["-date_publication"]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["region"]),
            models.Index(fields=["date_limite"]),
        ]


class ClassificationLog(models.Model):
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE, related_name="classifications")
    texte_source = models.TextField()
    secteur_predit = models.ForeignKey(Secteur, on_delete=models.SET_NULL, null=True)
    secteur_reel = models.ForeignKey(
        Secteur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verifications",
    )
    confiance = models.FloatField(help_text="Score de confiance du modèle (0 à 1)")
    date_prediction = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prédiction #{self.id} - {self.appel_offre.titre[:50]}"