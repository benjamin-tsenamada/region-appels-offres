from django.contrib import admin
from .models import (
    AppelOffre, TypeProcedure, District, Region, Secteur,
    ClassificationLog, SynchronisationLog
)

# Personnalisation des titres de l'admin
admin.site.site_header = "Région Atsimo-Andrefana"
admin.site.site_title = "Région Atsimo-Andrefana"
admin.site.index_title = "Gestion des appels d'offres publics"

# ==========================================
# ENREGISTREMENT DES MODÈLES DANS L'ADMIN
# ==========================================

@admin.register(AppelOffre)
class AppelOffreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'autorite_contractante', 'region', 'date_limite', 'statut')
    list_filter = ('statut', 'region', 'secteur')
    search_fields = ('titre', 'autorite_contractante', 'reference_armp')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region')
    list_filter = ('region',)
    search_fields = ('nom',)

@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(TypeProcedure)
class TypeProcedureAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom')

@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    list_display = ('appel_offre', 'secteur_predit', 'confiance', 'date_prediction')
    list_filter = ('secteur_predit',)

@admin.register(SynchronisationLog)
class SynchronisationLogAdmin(admin.ModelAdmin):
    list_display = ('date_sync', 'statut', 'nb_nouveaux', 'message')
    list_filter = ('statut',)