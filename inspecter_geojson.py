import json

with open("appels_offres/static/data/madagascar_districts.geojson", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 60)
print("INSPECTION DU GEOJSON")
print("=" * 60)
print("Type :", data.get("type"))
print("Nombre de features :", len(data.get("features", [])))

# Prendre la première feature pour voir sa structure
if data.get("features"):
    first = data["features"][0]
    print()
    print("=== STRUCTURE D'UNE FEATURE ===")
    print("Type :", first.get("type"))
    print("Propriétés :")
    for key, value in first.get("properties", {}).items():
        print(f"  - {key} : {value}")

    print()
    print("=== 5 PREMIERS NOMS DE DISTRICTS ===")
    for i, feature in enumerate(data["features"][:5]):
        props = feature.get("properties", {})
        # Chercher les champs qui ressemblent à un nom
        nom = props.get("shapeName") or props.get("ADM2_FR") or props.get("ADM2_EN") or props.get("name")
        print(f"  {i+1}. {nom}")