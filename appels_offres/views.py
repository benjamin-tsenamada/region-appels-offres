import json
from collections import Counter
from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from .models import (
    AppelOffre, TypeProcedure, District, Region, Secteur,
    ClassificationLog, SynchronisationLog,
)

def dashboard(request):
    appels = AppelOffre.objects.all()
    total_ao = appels.count()
    total_actifs = appels.exclude(statut__in=["attribue", "infructueux"]).count()
    montant_total = appels.aggregate(total=Sum("montant"))["total"] or 0

    aujourd_hui = date.today()
    dans_7_jours = aujourd_hui + timedelta(days=7)
    echeances_proches = appels.filter(date_limite__gte=aujourd_hui, date_limite__lte=dans_7_jours).count()
    total_aramp = appels.filter(source="ARMP").count()

    # Optimisation : calcul de la confiance avec Avg (une seule requête)
    moyenne = ClassificationLog.objects.aggregate(m=Avg("confiance"))["m"]
    confiance_moyenne = round(moyenne * 100, 1) if moyenne is not None else 0.0

    repartition_secteur = []
    for s in Secteur.objects.all():
        nb = appels.filter(secteur=s).count()
        if nb > 0:
            repartition_secteur.append({
                "nom": s.nom,
                "nombre": nb,
                "pourcentage": round(nb / total_ao * 100, 1) if total_ao > 0 else 0,
            })

    liste_appels = []
    for ao in appels.order_by("-date_publication")[:10]:
        log = ao.classifications.order_by("-date_prediction").first()
        liste_appels.append({
            "ao": ao,
            "prediction": log.secteur_predit.nom if log and log.secteur_predit else None,
            "confiance": round(log.confiance * 100) if log else None,
        })

    contexte = {
        "total_ao": total_ao,
        "total_actifs": total_actifs,
        "montant_total": montant_total,
        "echeances_proches": echeances_proches,
        "total_aramp": total_aramp,
        "confiance_moyenne": confiance_moyenne,
        "repartition_secteur": repartition_secteur,
        "liste_appels": liste_appels,
    }
    return render(request, "appels_offres/dashboard.html", contexte)

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

    repartition_secteur = []
    for s in Secteur.objects.all():
        nb = appels.filter(secteur=s).count()
        if nb > 0:
            repartition_secteur.append({"nom": s.nom, "nombre": nb, "pourcentage": round(nb/total_ao*100, 1) if total_ao > 0 else 0})

    # Optimisation : calcul de la confiance avec Avg
    moyenne = ClassificationLog.objects.aggregate(m=Avg("confiance"))["m"]
    confiance_moyenne = round(moyenne * 100, 1) if moyenne is not None else 0.0

    contexte = {
        "total_ao": total_ao,
        "total_actifs": appels.exclude(statut__in=["attribue", "infructueux"]).count(),
        "total_aramp": appels.filter(source="ARMP").count(),
        "confiance_moyenne": confiance_moyenne,
        "repartition_secteur": repartition_secteur,
        "all_regions": repartition_regions,
    }
    return render(request, "appels_offres/statistiques.html", contexte)

def liste_appels(request):
    appels = AppelOffre.objects.select_related("secteur", "type_procedure", "district").order_by("-date_publication")
    q = request.GET.get("q", "").strip()
    secteur_id = request.GET.get("secteur", "")
    region_nom = request.GET.get("region", "")
    mode_passation = request.GET.get("mode", "")
    statut = request.GET.get("statut", "")

    if q:
        appels = appels.filter(titre__icontains=q) | appels.filter(description__icontains=q) | appels.filter(autorite_contractante__icontains=q) | appels.filter(reference_armp__icontains=q)
    if secteur_id: appels = appels.filter(secteur_id=secteur_id)
    if region_nom: appels = appels.filter(region=region_nom)
    if statut: appels = appels.filter(statut=statut)
    if mode_passation: appels = appels.filter(mode_passation=mode_passation)

    paginator = Paginator(appels, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    contexte = {
        "page_obj": page_obj,
        "secteurs": Secteur.objects.all().order_by("nom"),
        "regions": Region.objects.all().order_by("nom"),
        "statuts": AppelOffre.STATUT_CHOICES,
        "modes": ["AOO", "AOR", "ACO", "AMI", "APQ"],
        "filtres": {"q": q, "secteur": secteur_id, "region": region_nom, "statut": statut, "mode": mode_passation},
        "total_resultats": appels.count(),
    }
    return render(request, "appels_offres/liste_appels.html", contexte)

def detail_appel(request, pk):
    appel = get_object_or_404(AppelOffre.objects.select_related("secteur", "type_procedure", "district"), pk=pk)
    classifications = appel.classifications.order_by("-date_prediction")
    return render(request, "appels_offres/detail_appel.html", {
        "appel": appel, "classifications": classifications, "tous_les_secteurs": Secteur.objects.all().order_by("nom"),
    })

@require_POST
def corriger_prediction(request, classification_id):
    log = get_object_or_404(ClassificationLog, pk=classification_id)
    secteur_reel_id = request.POST.get("secteur_reel")
    if secteur_reel_id:
        log.secteur_reel = Secteur.objects.filter(pk=secteur_reel_id).first()
        log.save()
        messages.success(request, "Correction enregistree. Merci.")
    return redirect("appels_offres:detail_appel", pk=log.appel_offre.pk)

def performance_ia(request):
    # Confiance moyenne : une seule requête
    moyenne = ClassificationLog.objects.aggregate(m=Avg("confiance"))["m"]
    confiance_moyenne = round(moyenne * 100, 1) if moyenne is not None else None
    total_predictions = ClassificationLog.objects.count()

    # Paires (secteur réel, secteur prédit) des prédictions vérifiées à la main
    secteurs_list = list(Secteur.objects.all().order_by("nom"))
    paires = Counter(
        ClassificationLog.objects
        .filter(secteur_reel__isnull=False, secteur_predit__isnull=False)
        .values_list("secteur_reel_id", "secteur_predit_id")
    )
    total_verifiees = sum(paires.values())
    correctes = sum(nb for (reel, predit), nb in paires.items() if reel == predit)
    precision = round(correctes / total_verifiees * 100, 1) if total_verifiees else None

    # Matrice de confusion (lignes = réel, colonnes = prédit)
    matrice_data = []
    for s_reel in secteurs_list:
        valeurs = [paires.get((s_reel.id, s_pred.id), 0) for s_pred in secteurs_list]
        matrice_data.append({"nom": s_reel.nom, "valeurs": valeurs})

    # Rappel et précision par secteur
    stats_secteurs = []
    for i, secteur in enumerate(secteurs_list):
        vrais_positifs = matrice_data[i]["valeurs"][i]
        support = sum(matrice_data[i]["valeurs"])
        predits = sum(ligne["valeurs"][i] for ligne in matrice_data)
        stats_secteurs.append({
            "nom": secteur.nom,
            "support": support,
            "rappel": round(vrais_positifs / support * 100, 1) if support else None,
            "precision": round(vrais_positifs / predits * 100, 1) if predits else None,
            "fiable": support >= 5,
        })

    # Données du radar, dans le même ordre que les libellés (secteurs_list)
    radar_rappel = json.dumps([st["rappel"] or 0 for st in stats_secteurs])
    radar_precision = json.dumps([st["precision"] or 0 for st in stats_secteurs])

    # Messages calculés, jamais écrits à la main
    insights = []
    if precision is None:
        insights.append({
            "type": "info",
            "titre": "Précision réelle en attente",
            "texte": "Aucune prédiction n'a été vérifiée manuellement. La confiance moyenne "
                     "mesure l'assurance du modèle, pas son exactitude.",
        })
    else:
        if confiance_moyenne is not None and confiance_moyenne - precision > 10:
            insights.append({
                "type": "warning",
                "titre": "Confiance supérieure à la précision réelle",
                "texte": f"Confiance moyenne de {confiance_moyenne} % contre {precision} % de "
                         f"prédictions correctes sur {total_verifiees} vérifiées : le modèle est "
                         f"plus sûr de lui qu'il n'est exact.",
            })
        else:
            insights.append({
                "type": "success",
                "titre": "Confiance cohérente avec la précision",
                "texte": f"{precision} % de prédictions correctes sur {total_verifiees} vérifiées.",
            })

        fiables = [st for st in stats_secteurs if st["fiable"] and st["rappel"] is not None]
        if fiables:
            meilleur = max(fiables, key=lambda st: st["rappel"])
            pire = min(fiables, key=lambda st: st["rappel"])
            insights.append({
                "type": "info",
                "titre": "Rappel par secteur",
                "texte": f"Meilleur rappel : {meilleur['nom']} ({meilleur['rappel']} %). "
                         f"Plus faible : {pire['nom']} ({pire['rappel']} %).",
            })

        rares = [st["nom"] for st in stats_secteurs if not st["fiable"]]
        if rares:
            insights.append({
                "type": "warning",
                "titre": "Échantillon insuffisant",
                "texte": "Moins de 5 exemples vérifiés pour : " + ", ".join(rares)
                         + ". Leurs taux ne sont pas interprétables.",
            })

        if total_verifiees < 100:
            insights.append({
                "type": "info",
                "titre": "Échantillon réduit",
                "texte": f"{total_verifiees} vérifications seulement : résultats indicatifs, "
                         f"marge d'erreur élevée.",
            })

    return render(request, "appels_offres/performance_ia.html", {
        "total_predictions": total_predictions,
        "total_verifiees": total_verifiees,
        "correctes": correctes,
        "precision": precision,
        "confiance_moyenne": confiance_moyenne,
        "secteurs_list": secteurs_list,
        "matrice_data": matrice_data,
        "stats_secteurs": stats_secteurs,
        "radar_rappel": radar_rappel,
        "radar_precision": radar_precision,
        "insights": insights,
    })

def carte(request):
    appels = AppelOffre.objects.all()
    toutes_avec_region = appels.exclude(region__isnull=True).exclude(region="")
    repartition_regions = []
    if toutes_avec_region.count() > 0:
        compteur = Counter(toutes_avec_region.values_list("region", flat=True))
        for region, nb in compteur.most_common():
            repartition_regions.append({"nom": region, "nb": nb})
    return render(request, "appels_offres/carte.html", {"repartition_regions": repartition_regions})

def carte_data(request):
    data = []
    for d in District.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        appels = AppelOffre.objects.filter(district=d)
        liste_appels = [{"titre": a.titre, "autorite": a.autorite_contractante} for a in appels[:20]]
        data.append({"nom": d.nom, "region": d.region.nom if d.region else "", "lat": d.latitude, "lng": d.longitude, "nb_appels": appels.count(), "appels": liste_appels})
    return JsonResponse(data, safe=False)

def regions_data(request):
    toutes_avec_region = AppelOffre.objects.exclude(region__isnull=True).exclude(region="")
    compteur = Counter(toutes_avec_region.values_list("region", flat=True))
    data = [{"nom": region, "nb": nb} for region, nb in compteur.most_common()]
    return JsonResponse(data, safe=False)

def synchronisation(request):
    derniere_sync = SynchronisationLog.objects.filter(statut="succes").first()
    historique = SynchronisationLog.objects.all()[:20]
    return render(request, "appels_offres/synchronisation.html", {"derniere_sync": derniere_sync, "historique": historique})

def lancer_synchronisation(request):
    from datetime import datetime as dt
    from appels_offres.scrapers.armp import extraire_tous_les_ao
    from appels_offres.ml.classifier import predict_secteur

    log_sync = SynchronisationLog.objects.create(statut="en_cours")
    debut = dt.now()

    try:
        tous_les_ao = extraire_tous_les_ao()
        types_proc = {t.code: t for t in TypeProcedure.objects.all()}
        secteurs_db = {s.nom.lower(): s for s in Secteur.objects.all()}
        numeros_existants = set(AppelOffre.objects.filter(source="ARMP").exclude(numero_armp__isnull=True).values_list("numero_armp", flat=True))
        crees, ignores = 0, 0

        for ao in tous_les_ao:
            numero = ao.get("numero") or ""
            if numero and numero in numeros_existants:
                ignores += 1; continue
            try:
                date_pub = dt.strptime(ao["date_debut"], "%Y-%m-%d").date() if ao.get("date_debut") else None
                date_lim = dt.strptime(ao["date_fin"], "%Y-%m-%d").date() if ao.get("date_fin") else None
            except (ValueError, TypeError):
                date_pub, date_lim = None, None
            
            if not date_pub or not date_lim:
                ignores += 1; continue

            try:
                nouveau = AppelOffre.objects.create(
                    titre=ao.get("objet", "")[:500], description=ao.get("objet", ""),
                    autorite_contractante=ao.get("entite", "")[:255], type_procedure=types_proc.get(ao.get("mode", "")),
                    date_publication=date_pub, date_limite=date_lim, statut="publie", source="ARMP",
                    region=ao.get("region_officielle", "")[:150] if ao.get("region_officielle") else None,
                    reference_armp=(ao.get("reference") or "")[:255] or None, numero_armp=numero[:100] if numero else None,
                    mode_passation=(ao.get("mode") or "")[:20] or None, url_source=(ao.get("lien_fiche") or "")[:500] or None,
                )
                crees += 1
                if numero: numeros_existants.add(numero)

                texte = f"{nouveau.titre} {nouveau.description}"
                secteur_nom, confiance = predict_secteur(texte)
                if secteur_nom:
                    secteur_obj = secteurs_db.get(secteur_nom.lower())
                    if secteur_obj:
                        nouveau.secteur = secteur_obj
                        nouveau.save()
                        ClassificationLog.objects.create(appel_offre=nouveau, texte_source=texte[:2000], secteur_predit=secteur_obj, confiance=confiance)
            except Exception:
                ignores += 1

        duree = (dt.now() - debut).total_seconds()
        log_sync.nb_total_extraits = len(tous_les_ao); log_sync.nb_nouveaux = crees
        log_sync.nb_ignores = ignores; log_sync.duree_secondes = duree
        log_sync.statut = "succes"; log_sync.message = f"Synchronisation reussie : {crees} nouveaux AO"
        log_sync.save()
        messages.success(request, f"Synchronisation reussie : {crees} nouveaux AO ajoutes")

    except Exception as e:
        log_sync.statut = "echec"; log_sync.message = f"Erreur : {str(e)[:500]}"; log_sync.save()
        messages.error(request, f"Erreur : {e}")

    return redirect("appels_offres:synchronisation")