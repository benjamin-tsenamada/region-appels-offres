"""
Scraper du site officiel de l'ARMP (Autorité de Régulation des Marchés Publics).
Source : http://marches.armp.mg/marches_publics/
"""

import re
import requests
from bs4 import BeautifulSoup


URL_ARMP = "http://marches.armp.mg/marches_publics/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RegionAtsimoAndrefana/1.0; +https://region-appels-offres.onrender.com)"
}


# Mapping des libellés ARMP vers les noms officiels des régions de Madagascar
MAPPING_REGIONS_ARMP = {
    "CENTRALE": "Analamanga",
    "ANALAMANGA": "Analamanga",
    "VAKINANKARATRA": "Vakinankaratra",
    "ITASY": "Itasy",
    "BONGOLAVA": "Bongolava",
    "VATOVAVY": "Vatovavy",
    "FITOVINANY": "Fitovinany",
    "AMORON'I MANIA": "Amoron'i Mania",
    "AMORONIMANIA": "Amoron'i Mania",
    "HAUTE MATSIATRA": "Haute Matsiatra",
    "ATSIMO-ATSINANANA": "Atsimo-Atsinanana",
    "IHOROMBE": "Ihorombe",
    "MENABE": "Menabe",
    "ATSIMO-ANDREFANA": "Atsimo-Andrefana",
    "ANDROY": "Androy",
    "ANOSY": "Anosy",
    "SAVA": "Sava",
    "DIANA": "Diana",
    "SOFIA": "Sofia",
    "BOENY": "Boeny",
    "BETSIBOKA": "Betsiboka",
    "MELAKY": "Melaky",
    "ALAOTRA-MANGORO": "Alaotra-Mangoro",
    "ATSINANANA": "Atsinanana",
    "ANALANJIROFO": "Analanjirofo",
    "AMBATOSOA": "Ambatosoa",
    "AMORONIMANIA": "Amoron'i Mania",
}


def normaliser_region(libelle_armp):
    """Transforme 'REGION : CENTRALE (370 avis)' en 'Analamanga'."""
    if not libelle_armp:
        return None
    # Nettoyer : enlever "REGION :" et "(XXX avis)"
    texte = re.sub(r"REGION\s*:\s*", "", libelle_armp, flags=re.IGNORECASE)
    texte = re.sub(r"\(\d+\s*avis\)", "", texte).strip()
    # Chercher dans le mapping
    for mot_cle, nom_officiel in MAPPING_REGIONS_ARMP.items():
        if mot_cle.upper() in texte.upper():
            return nom_officiel
    return texte if texte else None


def telecharger_page():
    r = requests.get(URL_ARMP, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text


def extraire_entite(cellule):
    texte = cellule.get_text("\n", strip=True)
    lignes = [l.strip() for l in texte.split("\n") if l.strip()]
    for ligne in lignes:
        if not ligne.startswith("-") and not ligne.startswith("Ref:") and not ligne.startswith("Mode:") and not ligne.startswith("N°"):
            return ligne
    return lignes[0] if lignes else ""


def extraire_reference(cellule):
    texte = cellule.get_text("\n", strip=True)
    match = re.search(r"Ref\s*:\s*(.+)", texte)
    return match.group(1).strip() if match else ""


def extraire_mode(cellule):
    texte = cellule.get_text("\n", strip=True)
    match = re.search(r"Mode\s*:\s*(\w+)", texte)
    return match.group(1).strip() if match else ""


def extraire_numero(cellule):
    texte = cellule.get_text("\n", strip=True)
    match = re.search(r"N°\s*([A-Za-z0-9\-_]+)", texte)
    return match.group(1).strip() if match else ""


def extraire_dates(cellule):
    texte = cellule.get_text(" ", strip=True)
    du_match = re.search(r"Du\s*:\s*(\d{4}-\d{2}-\d{2})", texte)
    au_match = re.search(r"Au\s*:\s*(\d{4}-\d{2}-\d{2})", texte)
    return (du_match.group(1) if du_match else None,
            au_match.group(1) if au_match else None)


def extraire_ao_depuis_ligne(tr, region_armp):
    cellules = tr.find_all("td")
    if len(cellules) < 3:
        return None

    cellule_entite = cellules[0]
    cellule_objet = cellules[1]
    cellule_date = cellules[2] if len(cellules) > 2 else None

    entite = extraire_entite(cellule_entite)
    reference = extraire_reference(cellule_entite)
    mode = extraire_mode(cellule_entite)
    numero = extraire_numero(cellule_entite)
    objet = cellule_objet.get_text(" ", strip=True)
    date_debut, date_fin = extraire_dates(cellule_date) if cellule_date else (None, None)

    if not objet or len(objet) < 10:
        return None

    lien_fiche = ""
    if len(cellules) > 3:
        a = cellules[3].find("a")
        if a and a.get("href"):
            lien_fiche = a["href"]
            if lien_fiche.startswith("/"):
                lien_fiche = "http://marches.armp.mg" + lien_fiche
            elif not lien_fiche.startswith("http"):
                lien_fiche = "http://marches.armp.mg/marches_publics/" + lien_fiche

    return {
        "region_armp": region_armp,
        "region_officielle": normaliser_region(region_armp),
        "entite": entite,
        "reference": reference,
        "mode": mode,
        "numero": numero,
        "objet": objet,
        "date_debut": date_debut,
        "date_fin": date_fin,
        "lien_fiche": lien_fiche,
        "source": "ARMP",
    }


def extraire_tous_les_ao(html=None):
    if html is None:
        html = telecharger_page()

    soup = BeautifulSoup(html, "lxml")
    resultats = []
    region_courante = ""

    for table in soup.find_all("table"):
        precedent = table.find_previous(string=re.compile(r"REGION\s*:", re.IGNORECASE))
        if precedent:
            region_courante = precedent.strip()

        for tr in table.find_all("tr"):
            ao = extraire_ao_depuis_ligne(tr, region_courante)
            if ao:
                resultats.append(ao)

    return resultats


if __name__ == "__main__":
    print("Téléchargement...")
    tous = extraire_tous_les_ao()
    print(f"\nTotal : {len(tous)} AO\n")
    for ao in tous[:5]:
        print(f"[{ao['region_officielle']}] {ao['entite']}")
        print(f"  {ao['objet'][:80]}...")
        print()