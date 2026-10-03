from django.contrib import admin
from .models import Secteur, TypeProcedure, District, AppelOffre, ClassificationLog
from .ml.classifier import predict_secteur


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(TypeProcedure)
class TypeProcedureAdmin(admin.ModelAdmin):
    list_display = ("code", "nom")
    search_fields = ("code", "nom")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("nom", "latitude", "longitude")
    search_fields = ("nom",)


@admin.register(AppelOffre)
class AppelOffreAdmin(admin.ModelAdmin):
    list_display = (
        "titre", "secteur", "prediction_ia", "type_procedure", "district",
        "montant", "date_publication", "date_limite", "statut",
    )
    list_filter = ("statut", "secteur", "type_procedure", "district")
    search_fields = ("titre", "description", "autorite_contractante")
    date_hierarchy = "date_publication"
    autocomplete_fields = ("secteur", "type_procedure", "district")

    fieldsets = (
        ("Informations générales", {
            "fields": ("titre", "description", "autorite_contractante")
        }),
        ("Classification", {
            "fields": ("secteur", "type_procedure", "district")
        }),
        ("Suivi", {
            "fields": ("montant", "date_publication", "date_limite", "statut")
        }),
    )

    def prediction_ia(self, obj):
        """Affiche la dernière prédiction IA enregistrée pour cet appel d'offres."""
        log = obj.classifications.order_by("-date_prediction").first()
        if log and log.secteur_predit:
            return f"{log.secteur_predit.nom} ({log.confiance:.0%})"
        return "—"
    prediction_ia.short_description = "Prédiction IA"

    def save_model(self, request, obj, form, change):
        if not obj.cree_par_id:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)

        # Classification automatique après sauvegarde
        texte = f"{obj.titre} {obj.description}"
        secteur_nom, confiance = predict_secteur(texte)

        if secteur_nom:
            secteur_predit = Secteur.objects.filter(nom=secteur_nom).first()
            ClassificationLog.objects.create(
                appel_offre=obj,
                texte_source=texte,
                secteur_predit=secteur_predit,
                secteur_reel=obj.secteur,  # le choix humain sert de vérité terrain
                confiance=confiance,
            )


@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    list_display = ("appel_offre", "secteur_predit", "secteur_reel", "confiance", "date_prediction")
    list_filter = ("secteur_predit", "secteur_reel")
    readonly_fields = ("date_prediction",)