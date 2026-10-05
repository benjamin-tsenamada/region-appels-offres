from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import AppelOffre, TypeProcedure
 
 
def dashboard(request):
    appels = AppelOffre.objects.select_related("secteur", "type_procedure", "district")
 
    # Indicateurs principaux
    total_actifs = appels.exclude(statut__in=["attribue", "infructueux"]).count()
    montant_total = appels.aggregate(total=Sum("montant"))["total"] or 0
 
    aujourd_hui = date.today()
    dans_7_jours = aujourd_hui + timedelta(days=7)
    echeances_proches = appels.filter(
        date_limite__gte=aujourd_hui,
        date_limite__lte=dans_7_jours,
    ).count()
 
    # Répartition par type de procédure (pour l'indicateur de gouvernance)
    total_count = appels.count()
    repartition_procedure = []
    if total_count > 0:
        for tp in TypeProcedure.objects.all():
            nb = appels.filter(type_procedure=tp).count()
            if nb > 0:
                repartition_procedure.append({
                    "nom": tp.nom,
                    "code": tp.code,
                    "nombre": nb,
                    "pourcentage": round(nb / total_count * 100, 1),
                })
 
    # Dernière prédiction IA pour chaque appel d'offres
    liste_appels = []
    for ao in appels.order_by("-date_publication")[:20]:
        log = ao.classifications.order_by("-date_prediction").first()
        liste_appels.append({
            "ao": ao,
            "prediction": log.secteur_predit.nom if log and log.secteur_predit else None,
            "confiance": round(log.confiance * 100) if log else None,
        })
 
    contexte = {
        "total_actifs": total_actifs,
        "montant_total": montant_total,
        "echeances_proches": echeances_proches,
        "repartition_procedure": repartition_procedure,
        "liste_appels": liste_appels,
    }
    return render(request, "appels_offres/dashboard.html", contexte)