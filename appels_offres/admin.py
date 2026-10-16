from django.contrib import admin
from .models import (
    Secteur, TypeProcedure, Region, District,
    AppelOffre, ClassificationLog, SynchronisationLog
)


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(TypeProcedure)
class TypeProcedureAdmin(admin.ModelAdmin):
    list_display = ("code", "nom")
    search_fields = ("code", "nom")


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("nom", "region")
    list_filter = ("region",)
    search_fields = ("nom",)


@admin.register(AppelOffre)
class AppelOffreAdmin(admin.ModelAdmin):
    list_display = ("titre", "autorite_contractante", "region", "date_limite", "statut", "source")
    list_filter = ("statut", "source", "region", "mode_passation")
    search_fields = ("titre", "description", "autorite_contractante", "reference_armp", "numero_armp")
    date_hierarchy = "date_limite"
    ordering = ("-date_publication",)

    fieldsets = (
        ("Informations principales", {
            "fields": ("titre", "description", "autorite_contractante", "montant")
        }),
        ("Classification", {
            "fields": ("secteur", "type_procedure", "district", "mode_passation")
        }),
        ("Dates et statut", {
            "fields": ("date_publication", "date_limite", "statut")
        }),
        ("Source ARMP", {
            "fields": ("source", "region", "reference_armp", "numero_armp", "url_source"),
            "classes": ("collapse",)
        }),
        ("Métadonnées", {
            "fields": ("cree_par", "date_creation", "date_import"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "appel_offre", "secteur_predit", "secteur_reel", "confiance", "date_prediction")
    list_filter = ("secteur_predit", "secteur_reel")
    search_fields = ("appel_offre__titre",)
    readonly_fields = ("date_prediction",)
    date_hierarchy = "date_prediction"


@admin.register(SynchronisationLog)
class SynchronisationLogAdmin(admin.ModelAdmin):
    list_display = ("date_sync", "statut", "nb_total_extraits", "nb_nouveaux", "nb_ignores", "duree_secondes")
    list_filter = ("statut",)
    readonly_fields = ("date_sync",)
    date_hierarchy = "date_sync"
    ordering = ("-date_sync",)


# Personnalisation du titre de l'admin
admin.site.site_header = "Région Atsimo-Andrefana — Administration"
admin.site.site_title = "Admin Région Atsimo-Andrefana"
admin.site.index_title = "Gestion des appels d'offres publics"