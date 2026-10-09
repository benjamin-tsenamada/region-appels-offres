"""
Données géographiques de Madagascar :
- 22 régions officielles
- 119 districts avec coordonnées GPS
"""

REGIONS_DISTRICTS = {
    "Analamanga": ("Analamanga", [
        ("Antananarivo Renivohitra", -18.9100, 47.5250),
        ("Antananarivo Atsimondrano", -18.9833, 47.5167),
        ("Antananarivo Avaradrano", -18.8333, 47.5833),
        ("Ambohidratrimo", -18.8167, 47.4333),
        ("Andramasina", -19.1833, 47.5833),
        ("Anjozorobe", -18.4000, 47.8667),
        ("Ankazobe", -18.3167, 47.1167),
        ("Manjakandriana", -18.9167, 47.8000),
    ]),
    "Vakinankaratra": ("Vakinankaratra", [
        ("Antsirabe I", -19.8659, 47.0333),
        ("Antsirabe II", -19.9000, 47.0000),
        ("Ambatolampy", -19.3833, 47.4333),
        ("Antanifotsy", -19.6500, 47.3167),
        ("Betafo", -19.8333, 46.8500),
        ("Faratsiho", -19.4000, 46.9500),
        ("Mandoto", -19.5833, 46.5000),
    ]),
    "Itasy": ("Itasy", [
        ("Miarinarivo", -18.9500, 46.9000),
        ("Arivonimamo", -19.0167, 47.1833),
        ("Soavinandriana", -19.1667, 46.7333),
    ]),
    "Bongolava": ("Bongolava", [
        ("Tsiroanomandidy", -18.7667, 46.0333),
        ("Fenoarivobe", -18.4500, 46.5667),
    ]),
    "Vatovavy": ("Vatovavy", [
        ("Mananjary", -21.2333, 48.3333),
        ("Nosy Varika", -20.5833, 48.5333),
        ("Ifanadiana", -21.3000, 47.6333),
    ]),
    "Fitovinany": ("Fitovinany", [
        ("Manakara", -22.1500, 48.0000),
        ("Vohipeno", -22.3500, 47.8333),
        ("Ikongo", -21.8833, 47.4333),
    ]),
    "Amoron'i Mania": ("Amoron'i Mania", [
        ("Ambositra", -20.5333, 47.2500),
        ("Fandriana", -20.2333, 47.3833),
        ("Ambatofinandrahana", -20.5500, 46.8000),
        ("Manandriana", -20.5833, 47.0833),
    ]),
    "Haute Matsiatra": ("Haute Matsiatra", [
        ("Fianarantsoa I", -21.4333, 47.0833),
        ("Fianarantsoa II", -21.5000, 47.0000),
        ("Ambalavao", -21.8333, 46.9333),
        ("Ambohimahasoa", -21.1167, 47.2167),
        ("Ikalamavony", -21.1500, 46.5833),
        ("Isandra", -21.2833, 46.9167),
        ("Lalangina", -21.5500, 47.1667),
        ("Vohibato", -21.7000, 47.0000),
    ]),
    "Atsimo-Atsinanana": ("Atsimo-Atsinanana", [
        ("Farafangana", -22.8167, 47.8333),
        ("Vangaindrano", -23.3500, 47.6000),
        ("Befotaka", -23.8167, 47.3167),
        ("Midongy-Atsimo", -23.5833, 47.0167),
        ("Vondrozo", -22.8167, 47.3167),
    ]),
    "Ihorombe": ("Ihorombe", [
        ("Ihosy", -22.4000, 46.1167),
        ("Iakora", -23.1000, 46.6333),
        ("Ivohibe", -22.4833, 46.8833),
    ]),
    "Menabe": ("Menabe", [
        ("Morondava", -20.2833, 44.2833),
        ("Mahabo", -20.3667, 44.6667),
        ("Manja", -21.4333, 44.3333),
        ("Belo-sur-Tsiribihina", -19.7000, 44.5500),
        ("Miandrivazo", -19.5167, 45.4667),
    ]),
    "Atsimo-Andrefana": ("Atsimo-Andrefana", [
        ("Toliara I", -23.3560, 43.6667),
        ("Toliara II", -23.4167, 43.5833),
        ("Sakaraha", -22.9167, 44.5333),
        ("Betioky", -23.7167, 44.3833),
        ("Ampanihy", -24.7000, 44.7500),
        ("Ankazoabo", -22.2833, 44.5167),
        ("Benenitra", -23.4500, 45.0833),
        ("Beroroha", -21.6667, 45.1667),
        ("Morombe", -21.7500, 43.3667),
    ]),
    "Androy": ("Androy", [
        ("Ambovombe", -25.1667, 46.0833),
        ("Bekily", -24.2167, 45.3167),
        ("Beloha", -25.0500, 45.0500),
        ("Tsihombe", -25.3167, 45.4833),
    ]),
    "Anosy": ("Anosy", [
        ("Tolagnaro", -25.0333, 46.9833),
        ("Amboasary-Atsimo", -25.0333, 46.3833),
        ("Betroka", -23.2667, 46.1000),
    ]),
    "Sava": ("Sava", [
        ("Sambava", -14.2667, 50.1667),
        ("Antalaha", -14.9000, 50.2833),
        ("Andapa", -14.6500, 49.6500),
        ("Vohemar", -13.3500, 50.0000),
    ]),
    "Diana": ("Diana", [
        ("Antsiranana I", -12.3000, 49.2833),
        ("Antsiranana II", -12.4167, 49.2167),
        ("Ambilobe", -13.2000, 49.0500),
        ("Ambanja", -13.6833, 48.4500),
        ("Nosy Be", -13.3167, 48.2500),
    ]),
    "Sofia": ("Sofia", [
        ("Antsohihy", -14.8667, 47.9833),
        ("Bealanana", -14.5500, 48.7500),
        ("Befandriana-Nord", -15.2500, 48.5333),
        ("Boriziny", -15.5833, 47.6333),
        ("Mampikony", -16.0833, 47.6167),
        ("Mandritsara", -15.8333, 48.8167),
        ("Analalava", -14.6333, 47.7500),
    ]),
    "Boeny": ("Boeny", [
        ("Mahajanga I", -15.7167, 46.3167),
        ("Mahajanga II", -15.6667, 46.3833),
        ("Ambato-Boeny", -16.0333, 46.7500),
        ("Marovoay", -16.1000, 46.6333),
        ("Mitsinjo", -16.0000, 45.8667),
        ("Soalala", -16.1000, 45.3333),
    ]),
    "Betsiboka": ("Betsiboka", [
        ("Maevatanana", -16.9500, 46.8333),
        ("Tsaratanana", -16.8000, 47.6500),
        ("Kandreho", -17.4667, 46.0833),
    ]),
    "Melaky": ("Melaky", [
        ("Maintirano", -18.0667, 44.0333),
        ("Ambatomainty", -17.6833, 45.6667),
        ("Antsalova", -18.6667, 44.6167),
        ("Besalampy", -16.7500, 44.4833),
        ("Morafenobe", -17.8500, 44.9167),
    ]),
    "Alaotra-Mangoro": ("Alaotra-Mangoro", [
        ("Ambatondrazaka", -17.8333, 48.4167),
        ("Amparafaravola", -17.5833, 48.2167),
        ("Andilamena", -17.0167, 48.5833),
        ("Anosibe An'ala", -19.4333, 48.2000),
        ("Moramanga", -18.9500, 48.2333),
    ]),
    "Atsinanana": ("Atsinanana", [
        ("Toamasina I", -18.1500, 49.4167),
        ("Toamasina II", -18.1167, 49.3333),
        ("Antanambao Manampotsy", -19.5000, 48.9667),
        ("Brickaville", -18.8167, 49.0667),
        ("Mahanoro", -19.9000, 48.8000),
        ("Marolambo", -20.0500, 48.1333),
        ("Vatomandry", -19.3333, 48.9833),
    ]),
    "Analanjirofo": ("Analanjirofo", [
        ("Fenoarivo Atsinanana", -17.3833, 49.4000),
        ("Mananara Avaratra", -16.1667, 49.7667),
        ("Maroantsetra", -15.4333, 49.7333),
        ("Sainte-Marie", -17.0833, 49.8167),
        ("Soanierana Ivongo", -16.9167, 49.5833),
        ("Vavatenina", -17.4667, 49.2000),
    ]),
}


def get_tous_les_districts():
    resultat = []
    for code, (region, districts) in REGIONS_DISTRICTS.items():
        for nom, lat, lng in districts:
            resultat.append((region, nom, lat, lng))
    return resultat


def get_toutes_les_regions():
    return list(REGIONS_DISTRICTS.keys())


if __name__ == "__main__":
    districts = get_tous_les_districts()
    print(f"Régions  : {len(REGIONS_DISTRICTS)}")
    print(f"Districts: {len(districts)}")