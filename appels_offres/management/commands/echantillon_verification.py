import csv
import random
import time

from django.core.management.base import BaseCommand
from django.db import OperationalError, connection

from appels_offres.management.commands.etiqueter_auto import deviner_secteur
from appels_offres.models import AppelOffre, ClassificationLog, Secteur


def avec_reconnexion(fonction, essais=4):
    for numero in range(1, essais + 1):
        try:
            return fonction()
        except OperationalError:
            connection.close()
            if numero == essais:
                raise
            time.sleep(2 * numero)


# Les 4 secteurs valides (en minuscules pour comparaison)
SECTEURS_VALIDES = {"travaux", "fournitures", "services", "prestations intellectuelles"}


class Command(BaseCommand):
    help = "Exporte un échantillon à étiqueter à la main, puis importe les corrections"

    def add_arguments(self, parser):
        parser.add_argument("--export", metavar="FICHIER.csv")
        parser.add_argument("--import", dest="importer", metavar="FICHIER.csv")
        parser.add_argument("--n", type=int, default=150)

    def handle(self, *args, **options):
        if options["export"]:
            self.exporter(options["export"], options["n"])
        elif options["importer"]:
            self.importer(options["importer"])
        else:
            self.stdout.write(self.style.ERROR("Utiliser --export ou --import."))

    def exporter(self, chemin, n):
        self.stdout.write("Génération de l'échantillon (étiquetage à l'aveugle)...")
        ids_predits = avec_reconnexion(
            lambda: set(ClassificationLog.objects.values_list("appel_offre_id", flat=True))
        )
        lignes = avec_reconnexion(
            lambda: list(AppelOffre.objects.filter(id__in=ids_predits).values_list("id", "titre", "description"))
        )

        reconnus, inconnus, vus = [], [], set()
        for ao_id, titre, description in lignes:
            texte = f"{titre} {description or ''}".strip()
            if texte in vus:
                continue
            vus.add(texte)
            (reconnus if deviner_secteur(texte) else inconnus).append((ao_id, titre))

        random.seed(42)
        n_inconnus = min(len(inconnus), n // 3)
        n_reconnus = min(len(reconnus), n - n_inconnus)
        choix = random.sample(reconnus, n_reconnus) + random.sample(inconnus, n_inconnus)
        random.shuffle(choix)

        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["id", "titre", "secteur_reel"])
            for ao_id, titre in choix:
                w.writerow([ao_id, titre[:300], ""])

        self.stdout.write(self.style.SUCCESS(
            f"{len(choix)} AO exportés ({n_reconnus} reconnus, {n_inconnus} non reconnus) -> {chemin}"
        ))

    def importer(self, chemin):
        # Détection automatique de l'encodage
        contenu = None
        for encodage in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                with open(chemin, "r", encoding=encodage) as f:
                    contenu = list(csv.reader(f, delimiter=";"))
                self.stdout.write(f"Fichier lu avec encodage : {encodage}")
                break
            except UnicodeDecodeError:
                continue

        if not contenu:
            self.stdout.write(self.style.ERROR("Fichier vide ou encodage inconnu."))
            return

        # On saute la première ligne (en-tête)
        entete = contenu[0]
        lignes = contenu[1:]

        # On cherche l'index de la colonne 'id'
        try:
            id_idx = [h.strip().lower() for h in entete].index("id")
        except ValueError:
            id_idx = 0  # Par défaut, l'ID est la première colonne

        secteurs_db = {s.nom.lower(): s for s in avec_reconnexion(lambda: list(Secteur.objects.all()))}
        ok = vides = invalides = introuvables = 0

        for ligne in lignes:
            if not ligne or len(ligne) <= id_idx:
                vides += 1
                continue

            ao_id = ligne[id_idx].strip()
            if not ao_id:
                vides += 1
                continue

            # 🎯 LA MAGIE : On cherche un secteur valide dans N'IMPORTE QUELLE colonne de la ligne
            secteur_trouve = None
            for cellule in ligne:
                cellule = (cellule or "").strip().lower()
                if cellule in SECTEURS_VALIDES:
                    secteur_trouve = cellule
                    break

            if not secteur_trouve:
                vides += 1
                continue

            secteur_obj = secteurs_db.get(secteur_trouve)
            if not secteur_obj:
                invalides += 1
                continue

            log = avec_reconnexion(
                lambda: ClassificationLog.objects.filter(appel_offre_id=ao_id).order_by("-date_prediction").first()
            )
            if not log:
                introuvables += 1
                continue

            log.secteur_reel = secteur_obj
            avec_reconnexion(lambda: log.save(update_fields=["secteur_reel"]))
            ok += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ {ok} corrections importées | {vides} vides | "
            f"{invalides} invalides | {introuvables} introuvables"
        ))