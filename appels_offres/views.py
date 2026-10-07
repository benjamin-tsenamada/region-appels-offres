from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import AppelOffre, TypeProcedure, District, Secteur, ClassificationLog


# ============================================================
# TABLEAU DE BORD
# ============================================================

def dashboard(request):
    appels = AppelOffre.objects.select_related("secteur", "type_procedure", "district")

    total_actifs = appels.exclude(statut__in=["attribue", "infructueux"]).count()
    montant_total = appels.aggregate(total=Sum("montant"))["total"] or 0

    aujourd_hui = date.today()
    dans_7_jours = aujourd_hui + timedelta(days=7)
    echeances_proches = appels.filter(
        date_limite__gte=aujourd_hui,
        date_limite__lte=dans_7_jours,
    ).count()

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


# ============================================================
# LISTE DES APPELS D'OFFRES + FILTRES
# ============================================================

def liste_appels(request):
    appels = AppelOffre.objects.select_related(
        "secteur", "type_procedure", "district"
    ).order_by("-date_publication")

    q = request.GET.get("q", "").strip()
    secteur_id = request.GET.get("secteur", "")
    district_id = request.GET.get("district", "")
    statut = request.GET.get("statut", "")
    date_limite_avant = request.GET.get("date_limite_avant", "")

    if q:
        appels = appels.filter(titre__icontains=q) | appels.filter(description__icontains=q) | appels.filter(autorite_contractante__icontains=q)

    if secteur_id:
        appels = appels.filter(secteur_id=secteur_id)

    if district_id:
        appels = appels.filter(district_id=district_id)

    if statut:
        appels = appels.filter(statut=statut)

    if date_limite_avant:
        appels = appels.filter(date_limite__lte=date_limite_avant)

    paginator = Paginator(appels, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    contexte = {
        "page_obj": page_obj,
        "secteurs": Secteur.objects.all().order_by("nom"),
        "districts": District.objects.all().order_by("nom"),
        "statuts": AppelOffre.STATUT_CHOICES,
        "filtres": {
            "q": q,
            "secteur": secteur_id,
            "district": district_id,
            "statut": statut,
            "date_limite_avant": date_limite_avant,
        },
        "total_resultats": appels.count(),
    }
    return render(request, "appels_offres/liste_appels.html", contexte)


# ============================================================
# DÉTAIL D'UN APPEL D'OFFRES
# ============================================================

def detail_appel(request, pk):
    appel = get_object_or_404(
        AppelOffre.objects.select_related("secteur", "type_procedure", "district"),
        pk=pk
    )
    classifications = appel.classifications.order_by("-date_prediction")

    contexte = {
        "appel": appel,
        "classifications": classifications,
        "tous_les_secteurs": Secteur.objects.all().order_by("nom"),
    }
    return render(request, "appels_offres/detail_appel.html", contexte)


# ============================================================
# CORRECTION DE LA PRÉDICTION NLP
# ============================================================

@require_POST
def corriger_prediction(request, classification_id):
    log = get_object_or_404(ClassificationLog, pk=classification_id)

    secteur_reel_id = request.POST.get("secteur_reel")
    if secteur_reel_id:
        log.secteur_reel = Secteur.objects.filter(pk=secteur_reel_id).first()
        log.save()
        messages.success(request, "Correction enregistrée. Merci.")
    return redirect("appels_offres:detail_appel", pk=log.appel_offre.pk)


# ============================================================
# PERFORMANCE DU MODÈLE IA
# ============================================================

def performance_ia(request):
    toutes = ClassificationLog.objects.select_related(
        "secteur_predit", "secteur_reel", "appel_offre"
    )
    total_predictions = toutes.count()
    verifiees = toutes.filter(secteur_reel__isnull=False)
    total_verifiees = verifiees.count()

    correctes = 0
    for log in verifiees:
        if log.secteur_predit_id == log.secteur_reel_id:
            correctes += 1

    precision = round((correctes / total_verifiees) * 100, 1) if total_verifiees > 0 else None

    matrice = {}
    for log in verifiees:
        reel = log.secteur_reel.nom if log.secteur_reel else "—"
        predit = log.secteur_predit.nom if log.secteur_predit else "—"
        cle = (reel, predit)
        matrice[cle] = matrice.get(cle, 0) + 1

    confiance_moyenne = None
    if total_predictions > 0:
        somme = sum(log.confiance for log in toutes)
        confiance_moyenne = round((somme / total_predictions) * 100, 1)

    contexte = {
        "total_predictions": total_predictions,
        "total_verifiees": total_verifiees,
        "correctes": correctes,
        "precision": precision,
        "confiance_moyenne": confiance_moyenne,
        "matrice": sorted(matrice.items()),
        "secteurs": Secteur.objects.all().order_by("nom"),
    }
    return render(request, "appels_offres/performance_ia.html", contexte)


# ============================================================
# CARTE DES DISTRICTS
# ============================================================

def carte(request):
    return render(request, "appels_offres/carte.html")


def carte_data(request):
    data = []
    for d in District.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        appels = AppelOffre.objects.filter(district=d)
        liste_appels = [
            {"titre": a.titre, "autorite": a.autorite_contractante, "statut": a.statut}
            for a in appels
        ]
        data.append({
            "nom": d.nom,
            "lat": d.latitude,
            "lng": d.longitude,
            "nb_appels": appels.count(),
            "appels": liste_appels,
        })
    return JsonResponse(data, safe=False)