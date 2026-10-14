from datetime import date, timedelta
import time

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from .models import (
    AppelOffre, TypeProcedure, District, Region, Secteur,
    ClassificationLog, SynchronisationLog
)


def _stats_communes(appels):
    total_ao = appels.count()
    aujourd_hui = date.today()
    dans_7_jours = aujourd_hui + timedelta(days=7)

    logs = ClassificationLog.objects.all()
    confiance_moyenne = 0.0
    if logs.exists():
        confiance_moyenne = round(sum(l.confiance for l in logs) / logs.count() * 100, 1)

    repartition_secteur = []
    for s in Secteur.objects.all():
        nb = appels.filter(secteur=s).count()
        if nb > 0:
            repartition_secteur.append({
                "nom": s.nom,
                "nombre": nb,
                "pourcentage": round(nb / total_ao * 100, 1) if total_ao > 0 else 0,
            })

    modes_repartition = []
    for mode in ["AOO", "AOR", "ACO", "AMI", "APQ"]:
        nb = appels.filter(mode_passation=mode).count()
        if nb > 0:
            modes_repartition.append({
                "mode": mode,
                "nb": nb,
                "pourcentage": round(nb / total_ao * 100, 1) if total_ao > 0 else 0,
            })

    top_regions = (
        appels.exclude(region__isnull=True).exclude(region="")
        .values("region").annotate(nb=Count("id")).order_by("-nb")[:10]
    )

    return {
        "total_ao": total_ao,
        "total_actifs": appels.exclude(statut__in=["attribue", "infructueux"]).count(),
        "total_aramp": appels.filter(source="ARMP").count(),
        "montant_total": appels.aggregate(total=Sum("montant"))["total"] or 0,
        "echeances_proches": appels.filter(date_limite__gte=aujourd_hui, date_limite__lte=dans_7_jours).count(),
        "confiance_moyenne": confiance_moyenne,
        "repartition_secteur": repartition_secteur,
        "modes_repartition": modes_repartition,
        "top_regions": top_regions,
    }


def dashboard(request):
    appels = AppelOffre.objects.all()
    stats = _stats_communes(appels)

    liste_appels = []
    for ao in appels.order_by("-date_publication")[:8]:
        log = ao.classifications.order_by("-date_prediction").first()
        liste_appels.append({
            "ao": ao,
            "prediction": log.secteur_predit.nom if log and log.secteur_predit else None,
            "confiance": round(log.confiance * 100) if log else None,
        })
    stats["liste_appels"] = liste_appels

    # Info synchronisation (dernière sync + temps écoulé)
    derniere_sync = SynchronisationLog.objects.filter(statut="succes").first()
    stats["derniere_sync"] = derniere_sync
    if derniere_sync:
        delta = timezone.now() - derniere_sync.date_sync
        minutes = int(delta.total_seconds() / 60)
        if minutes < 1:
            stats["sync_texte"] = "à l'instant"
            stats["sync_couleur"] = "green"
        elif minutes < 60:
            stats["sync_texte"] = f"il y a {minutes} min"
            stats["sync_couleur"] = "green"
        elif minutes < 1440:
            heures = minutes // 60
            stats["sync_texte"] = f"il y a {heures} h"
            stats["sync_couleur"] = "orange"
        else:
            jours = minutes // 1440
            stats["sync_texte"] = f"il y a {jours} j"
            stats["sync_couleur"] = "red"
    else:
        stats["sync_texte"] = "jamais synchronisé"
        stats["sync_couleur"] = "red"

    return render(request, "appels_offres/dashboard.html", stats)


def statistiques(request):
    appels = AppelOffre.objects.all()
    stats = _stats_communes(appels)
    return render(request, "appels_offres/statistiques.html", stats)


def liste_appels(request):
    appels = AppelOffre.objects.select_related(
        "secteur", "type_procedure", "district"
    ).order_by("-date_publication")

    q = request.GET.get("q", "").strip()
    secteur_id = request.GET.get("secteur", "")
    region_nom = request.GET.get("region", "")
    district_id = request.GET.get("district", "")
    statut = request.GET.get("statut", "")
    source = request.GET.get("source", "")
    mode_passation = request.GET.get("mode", "")
    date_limite_avant = request.GET.get("date_limite_avant", "")

    if q:
        appels = appels.filter(titre__icontains=q) | \
                 appels.filter(description__icontains=q) | \
                 appels.filter(autorite_contractante__icontains=q) | \
                 appels.filter(reference_armp__icontains=q)
    if secteur_id:
        appels = appels.filter(secteur_id=secteur_id)
    if region_nom:
        appels = appels.filter(region=region_nom)
    if district_id:
        appels = appels.filter(district_id=district_id)
    if statut:
        appels = appels.filter(statut=statut)
    if source:
        appels = appels.filter(source=source)
    if mode_passation:
        appels = appels.filter(mode_passation=mode_passation)
    if date_limite_avant:
        appels = appels.filter(date_limite__lte=date_limite_avant)

    paginator = Paginator(appels, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    contexte = {
        "page_obj": page_obj,
        "secteurs": Secteur.objects.all().order_by("nom"),
        "regions": Region.objects.all().order_by("nom"),
        "districts": District.objects.all().order_by("nom"),
        "statuts": AppelOffre.STATUT_CHOICES,
        "sources": AppelOffre.SOURCE_CHOICES,
        "modes": ["AOO", "AOR", "ACO", "AMI", "APQ"],
        "filtres": {
            "q": q, "secteur": secteur_id, "region": region_nom,
            "district": district_id, "statut": statut, "source": source,
            "mode": mode_passation, "date_limite_avant": date_limite_avant,
        },
        "total_resultats": appels.count(),
    }
    return render(request, "appels_offres/liste_appels.html", contexte)


def detail_appel(request, pk):
    appel = get_object_or_404(
        AppelOffre.objects.select_related("secteur", "type_procedure", "district"), pk=pk
    )
    classifications = appel.classifications.order_by("-date_prediction")
    return render(request, "appels_offres/detail_appel.html", {
        "appel": appel,
        "classifications": classifications,
        "tous_les_secteurs": Secteur.objects.all().order_by("nom"),
    })


@require_POST
def corriger_prediction(request, classification_id):
    log = get_object_or_404(ClassificationLog, pk=classification_id)
    secteur_reel_id = request.POST.get("secteur_reel")
    if secteur_reel_id:
        log.secteur_reel = Secteur.objects.filter(pk=secteur_reel_id).first()
        log.save()
        messages.success(request, "Correction enregistrée. Merci.")
    return redirect("appels_offres:detail_appel", pk=log.appel_offre.pk)


def performance_ia(request):
    toutes = ClassificationLog.objects.select_related("secteur_predit", "secteur_reel", "appel_offre")
    total_predictions = toutes.count()
    verifiees = toutes.filter(secteur_reel__isnull=False)
    total_verifiees = verifiees.count()
    correctes = sum(1 for log in verifiees if log.secteur_predit_id == log.secteur_reel_id)
    precision = round((correctes / total_verifiees) * 100, 1) if total_verifiees > 0 else None

    matrice = {}
    for log in verifiees:
        reel = log.secteur_reel.nom if log.secteur_reel else "—"
        predit = log.secteur_predit.nom if log.secteur_predit else "—"
        matrice[(reel, predit)] = matrice.get((reel, predit), 0) + 1

    confiance_moyenne = None
    if total_predictions > 0:
        confiance_moyenne = round(sum(log.confiance for log in toutes) / total_predictions * 100, 1)

    return render(request, "appels_offres/performance_ia.html", {
        "total_predictions": total_predictions,
        "total_verifiees": total_verifiees,
        "correctes": correctes,
        "precision": precision,
        "confiance_moyenne": confiance_moyenne,
        "matrice": sorted(matrice.items()),
        "secteurs": Secteur.objects.all().order_by("nom"),
    })


def carte(request):
    return render(request, "appels_offres/carte.html")


def carte_data(request):
    data = []
    for d in District.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        appels = AppelOffre.objects.filter(district=d)
        liste_appels = [
            {"titre": a.titre, "autorite": a.autorite_contractante, "statut": a.statut,
             "region": a.region or "", "reference": a.reference_armp or "", "mode": a.mode_passation or ""}
            for a in appels[:20]
        ]
        data.append({
            "nom": d.nom,
            "region": d.region.nom if d.region else "",
            "lat": d.latitude, "lng": d.longitude,
            "nb_appels": appels.count(),
            "appels": liste_appels,
        })
    return JsonResponse(data, safe=False)


# ============================================================
# SYNCHRONISATION ARMP
# ============================================================

def synchronisation(request):
    """Page de synchronisation avec l'ARMP."""
    historique = SynchronisationLog.objects.all()[:20]
    derniere_sync = SynchronisationLog.objects.filter(statut="succes").first()

    contexte = {
        "historique": historique,
        "derniere_sync": derniere_sync,
        "total_ao": AppelOffre.objects.filter(source="ARMP").count(),
        "total_ao_total": AppelOffre.objects.count(),
    }
    return render(request, "appels_offres/synchronisation.html", contexte)


@require_POST
def lancer_synchronisation(request):
    """Lance le scraper ARMP et enregistre le résultat."""
    from appels_offres.scrapers.armp import extraire_tous_les_ao
    from datetime import datetime

    debut = time.time()

    # Créer un log "en cours"
    log_sync = SynchronisationLog.objects.create(statut="en_cours")

    try:
        # Récupérer les AO depuis l'ARMP
        tous_les_ao = extraire_tous_les_ao()
        nb_total = len(tous_les_ao)

        # Types de procédure en base
        types_proc = {t.code: t for t in TypeProcedure.objects.all()}

        # Numéros déjà en base
        numeros_existants = set(
            AppelOffre.objects.filter(source="ARMP").exclude(numero_armp__isnull=True)
            .values_list("numero_armp", flat=True)
        )

        crees = 0
        ignores = 0

        for ao in tous_les_ao:
            numero = ao.get("numero") or ""
            if numero and numero in numeros_existants:
                ignores += 1
                continue

            date_publication = None
            date_limite = None
            try:
                if ao.get("date_debut"):
                    date_publication = datetime.strptime(ao["date_debut"], "%Y-%m-%d").date()
                if ao.get("date_fin"):
                    date_limite = datetime.strptime(ao["date_fin"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

            if not date_publication or not date_limite:
                ignores += 1
                continue

            type_proc = types_proc.get(ao.get("mode", ""))

            try:
                nouveau = AppelOffre.objects.create(
                    titre=ao.get("objet", "")[:500],
                    description=ao.get("objet", ""),
                    autorite_contractante=ao.get("entite", "")[:255],
                    type_procedure=type_proc,
                    date_publication=date_publication,
                    date_limite=date_limite,
                    statut="publie",
                    source="ARMP",
                    region=ao.get("region_officielle", "")[:150] if ao.get("region_officielle") else None,
                    reference_armp=(ao.get("reference") or "")[:255] or None,
                    numero_armp=numero[:100] if numero else None,
                    mode_passation=(ao.get("mode") or "")[:20] or None,
                    url_source=(ao.get("lien_fiche") or "")[:500] or None,
                )
                crees += 1
                if numero:
                    numeros_existants.add(numero)

                # Classification automatique
                from appels_offres.ml.classifier import predict_secteur
                texte = f"{nouveau.titre} {nouveau.description}"
                secteur_nom, confiance = predict_secteur(texte)
                if secteur_nom:
                    secteur_obj = Secteur.objects.filter(nom__iexact=secteur_nom).first()
                    if secteur_obj:
                        nouveau.secteur = secteur_obj
                        nouveau.save(update_fields=["secteur"])
                        ClassificationLog.objects.create(
                            appel_offre=nouveau,
                            texte_source=texte[:2000],
                            secteur_predit=secteur_obj,
                            confiance=confiance,
                        )

            except Exception:
                ignores += 1

        duree = round(time.time() - debut, 1)

        # Mettre à jour le log
        log_sync.nb_total_extraits = nb_total
        log_sync.nb_nouveaux = crees
        log_sync.nb_ignores = ignores
        log_sync.duree_secondes = duree
        log_sync.statut = "succes"
        log_sync.message = f"Synchronisation réussie : {crees} nouveaux AO ajoutés"
        log_sync.save()

        messages.success(
            request,
            f"✅ Synchronisation terminée : {crees} nouveaux AO ajoutés ({duree}s)"
        )

    except Exception as e:
        duree = round(time.time() - debut, 1)
        log_sync.statut = "echec"
        log_sync.duree_secondes = duree
        log_sync.message = f"Erreur : {str(e)[:500]}"
        log_sync.save()
        messages.error(request, f"❌ Erreur de synchronisation : {e}")

    return redirect("appels_offres:synchronisation")