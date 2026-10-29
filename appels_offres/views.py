from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from collections import Counter
from .models import (
    AppelOffre, TypeProcedure, District, Region, Secteur,
    ClassificationLog, SynchronisationLog,
)


# ============================================================
# TABLEAU DE BORD
# ============================================================

def dashboard(request):
    appels = AppelOffre.objects.all()
    total_ao = appels.count()
    total_actifs = appels.exclude(statut__in=["attribue", "infructueux"]).count()
    montant_total = appels.aggregate(total=Sum("montant"))["total"] or 0

    aujourd_hui = date.today()
    dans_7_jours = aujourd_hui + timedelta(days=7)
    echeances_proches = appels.filter(
        date_limite__gte=aujourd_hui,
        date_limite__lte=dans_7_jours,
    ).count()

    total_aramp = appels.filter(source="ARMP").count()

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

    liste_appels = []
    for ao in appels.order_by("-date_publication")[:10]:
        log = ao.classifications.order_by("-date_prediction").first()
        liste_appels.append({
            "ao": ao,
            "prediction": log.secteur_predit.nom if log and log.secteur_predit else None,
            "confiance": round(log.confiance * 100) if log else None,
        })

    derniere_sync = SynchronisationLog.objects.filter(statut="succes").first()
    sync_texte = "jamais synchronisé"
    sync_couleur = "red"
    if derniere_sync:
        delta = timezone.now() - derniere_sync.date_sync
        minutes = int(delta.total_seconds() / 60)
        if minutes < 1:
            sync_texte = "à l'instant"
            sync_couleur = "green"
        elif minutes < 60:
            sync_texte = f"il y a {minutes} min"
            sync_couleur = "green"
        else:
            heures = int(minutes / 60)
            if heures < 24:
                sync_texte = f"il y a {heures} h"
                sync_couleur = "orange"
            else:
                jours = int(heures / 24)
                sync_texte = f"il y a {jours} j"
                sync_couleur = "red"

    contexte = {
        "total_ao": total_ao,
        "total_actifs": total_actifs,
        "montant_total": montant_total,
        "echeances_proches": echeances_proches,
        "total_aramp": total_aramp,
        "confiance_moyenne": confiance_moyenne,
        "repartition_secteur": repartition_secteur,
        "modes_repartition": modes_repartition,
        "top_regions": top_regions,
        "liste_appels": liste_appels,
        "derniere_sync": derniere_sync,
        "sync_texte": sync_texte,
        "sync_couleur": sync_couleur,
    }
    return render(request, "appels_offres/dashboard.html", contexte)


# ============================================================
# STATISTIQUES
# ============================================================

def statistiques(request):
    appels = AppelOffre.objects.all()
    total_ao = appels.count()

    repartition_regions = []
    toutes_avec_region = appels.exclude(region__isnull=True).exclude(region="")
    total_avec_region = toutes_avec_region.count()
    if total_avec_region > 0:
        compteur = Counter(toutes_avec_region.values_list("region", flat=True))
        for region, nb in compteur.most_common():
            repartition_regions.append({
                "nom": region, "nb": nb,
                "pourcentage": round(nb / total_avec_region * 100, 1),
            })

    top_5 = repartition_regions[:5]
    top_regions = repartition_regions[:10]  # <--- LA CORRECTION EST ICI
    max_nb = repartition_regions[0]["nb"] if repartition_regions else 0
    max_region = repartition_regions[0]["nom"] if repartition_regions else "—"
    moyenne = round(total_avec_region / len(repartition_regions), 1) if repartition_regions else 0

    repartition_secteur = []
    for s in Secteur.objects.all():
        nb = appels.filter(secteur=s).count()
        if nb > 0:
            repartition_secteur.append({"nom": s.nom, "nombre": nb, "pourcentage": round(nb/total_ao*100, 1)})

    modes_repartition = []
    for mode in ["AOO", "AOR", "ACO", "AMI", "APQ"]:
        nb = appels.filter(mode_passation=mode).count()
        if nb > 0:
            modes_repartition.append({"mode": mode, "nb": nb, "pourcentage": round(nb/total_ao*100, 1)})

    logs = ClassificationLog.objects.all()
    confiance_moyenne = 0.0
    if logs.exists():
        confiance_moyenne = round(sum(l.confiance for l in logs) / logs.count() * 100, 1)

    contexte = {
        "total_ao": total_ao,
        "total_actifs": appels.exclude(statut__in=["attribue", "infructueux"]).count(),
        "total_aramp": appels.filter(source="ARMP").count(),
        "echeances_proches": appels.filter(
            date_limite__gte=date.today(),
            date_limite__lte=date.today() + timedelta(days=7)
        ).count(),
        "confiance_moyenne": confiance_moyenne,
        "repartition_regions": repartition_regions,
        "repartition_secteur": repartition_secteur,
        "modes_repartition": modes_repartition,
        "top_regions": top_regions,
        "top_5": top_5,
        "max_nb": max_nb,
        "max_region": max_region,
        "moyenne_par_region": moyenne,
        "nb_regions": len(repartition_regions),
        "total_avec_region": total_avec_region,
    }
    return render(request, "appels_offres/statistiques.html", contexte)


# ============================================================
# LISTE DES APPELS D'OFFRES
# ============================================================

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


# ============================================================
# DÉTAIL
# ============================================================

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


# ============================================================
# PERFORMANCE IA
# ============================================================

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


# ============================================================
# CARTE
# ============================================================

def carte(request):
    appels = AppelOffre.objects.all()
    toutes_avec_region = appels.exclude(region__isnull=True).exclude(region="")
    total_avec_region = toutes_avec_region.count()

    repartition_regions = []
    if total_avec_region > 0:
        compteur = Counter(toutes_avec_region.values_list("region", flat=True))
        for region, nb in compteur.most_common():
            repartition_regions.append({
                "nom": region, "nb": nb,
                "pourcentage": round(nb / total_avec_region * 100, 1),
            })

    max_nb = repartition_regions[0]["nb"] if repartition_regions else 0
    max_region = repartition_regions[0]["nom"] if repartition_regions else "—"
    moyenne = round(total_avec_region / len(repartition_regions), 1) if repartition_regions else 0

    contexte = {
        "repartition_regions": repartition_regions,
        "top_5": repartition_regions[:5],
        "total_avec_region": total_avec_region,
        "max_nb": max_nb,
        "max_region": max_region,
        "moyenne_par_region": moyenne,
        "nb_regions": len(repartition_regions),
    }
    return render(request, "appels_offres/carte.html", contexte)


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


def regions_data(request):
    """API : renvoie la répartition des AO par région (pour le refresh automatique de la carte)."""
    toutes_avec_region = AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
    compteur = Counter(toutes_avec_region.values_list("region", flat=True))
    data = [{"nom": region, "nb": nb} for region, nb in compteur.most_common()]
    return JsonResponse(data, safe=False)


# ============================================================
# SYNCHRONISATION ARMP
# ============================================================

def synchronisation(request):
    derniere_sync = SynchronisationLog.objects.filter(statut="succes").first()
    historique = SynchronisationLog.objects.all()[:20]
    return render(request, "appels_offres/synchronisation.html", {
        "derniere_sync": derniere_sync,
        "historique": historique,
    })


def lancer_synchronisation(request):
    """Lance une synchronisation manuelle avec l'ARMP."""
    from datetime import datetime as dt
    from appels_offres.scrapers.armp import extraire_tous_les_ao
    from appels_offres.ml.classifier import predict_secteur

    log_sync = SynchronisationLog.objects.create(statut="en_cours")
    debut = dt.now()

    try:
        tous_les_ao = extraire_tous_les_ao()
        nb_total = len(tous_les_ao)

        types_proc = {t.code: t for t in TypeProcedure.objects.all()}
        secteurs_db = {s.nom.lower(): s for s in Secteur.objects.all()}
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
                    date_publication = dt.strptime(ao["date_debut"], "%Y-%m-%d").date()
                if ao.get("date_fin"):
                    date_limite = dt.strptime(ao["date_fin"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

            if not date_publication or not date_limite:
                ignores += 1
                continue

            try:
                nouveau = AppelOffre.objects.create(
                    titre=ao.get("objet", "")[:500],
                    description=ao.get("objet", ""),
                    autorite_contractante=ao.get("entite", "")[:255],
                    type_procedure=types_proc.get(ao.get("mode", "")),
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

                texte = f"{nouveau.titre} {nouveau.description}"
                secteur_nom, confiance = predict_secteur(texte)
                if secteur_nom:
                    secteur_obj = secteurs_db.get(secteur_nom.lower())
                    if secteur_obj:
                        nouveau.secteur = secteur_obj
                        nouveau.save()
                        ClassificationLog.objects.create(
                            appel_offre=nouveau,
                            texte_source=texte[:2000],
                            secteur_predit=secteur_obj,
                            confiance=confiance,
                        )
            except Exception:
                ignores += 1

        duree = (dt.now() - debut).total_seconds()
        log_sync.nb_total_extraits = nb_total
        log_sync.nb_nouveaux = crees
        log_sync.nb_ignores = ignores
        log_sync.duree_secondes = duree
        log_sync.statut = "succes"
        log_sync.message = f"Synchronisation réussie : {crees} nouveaux AO ajoutés"
        log_sync.save()

        messages.success(request, f"✅ Synchronisation réussie : {crees} nouveaux AO ajoutés")

    except Exception as e:
        duree = (dt.now() - debut).total_seconds()
        log_sync.statut = "echec"
        log_sync.duree_secondes = duree
        log_sync.message = f"Erreur : {str(e)[:500]}"
        log_sync.save()
        messages.error(request, f"❌ Erreur de synchronisation : {e}")

    return redirect("appels_offres:synchronisation")