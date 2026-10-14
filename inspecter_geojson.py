import json

with open("appels_offres/static/data/madagascar_regions.geojson", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 60)
print("INSPECTION DU GEOJSON DES RÉGIONS")
print("=" * 60)
print("Type :", data.get("type"))
print("Nombre de features :", len(data.get("features", [])))

if data.get("features"):
    first = data["features"][0]
    print()
    print("=== STRUCTURE D'UNE FEATURE ===")
    for key, value in first.get("properties", {}).items():
        print(f"  - {key} : {value}")

    print()
    print("=== TOUS LES NOMS DE RÉGIONS ===")
    for i, feature in enumerate(data["features"]):
        props = feature.get("properties", {})
        nom = props.get("NAME_1") or props.get("shapeName") or props.get("name") or "?"
        print(f"  {i+1:3}. {nom}")