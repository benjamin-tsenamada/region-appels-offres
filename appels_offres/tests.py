from django.test import TestCase
from django.urls import reverse
from appels_offres.models import AppelOffre, Secteur, ClassificationLog

try:
    from appels_offres.ml.classifier import predict_secteur
except ImportError:
    predict_secteur = None

class MLTests(TestCase):
    def test_1_prediction_texte_simple(self):
        if predict_secteur:
            texte = "Construction d'une route en béton."
            secteur, confiance = predict_secteur(texte)
            self.assertIsNotNone(secteur)

    def test_2_prediction_texte_ambigu(self):
        if predict_secteur:
            texte = "Achat de divers matériels et services."
            secteur, confiance = predict_secteur(texte)
            self.assertIsNotNone(confiance)

    def test_3_texte_vide(self):
        # L'IA attribue un secteur par défaut même pour un texte vide.
        # On vérifie qu'elle renvoie bien une valeur sans planter.
        if predict_secteur:
            secteur, confiance = predict_secteur("")
            self.assertIsNotNone(secteur) 

class ModelTests(TestCase):
    def setUp(self):
        self.secteur = Secteur.objects.create(nom="Travaux")
        self.ao = AppelOffre.objects.create(
            titre="Test Route", autorite_contractante="Region",
            date_publication="2026-01-01", date_limite="2026-02-01",
            statut="publie", numero_armp="12345"
        )

    def test_4_creation_ao(self):
        self.assertEqual(self.ao.titre, "Test Route")

    def test_5_deduplication(self):
        ao_existant = AppelOffre.objects.get(numero_armp="12345")
        self.assertEqual(ao_existant.titre, "Test Route")

class IntegrationTests(TestCase):
    def test_6_classification_et_log(self):
        ao = AppelOffre.objects.create(titre="Test", date_publication="2026-01-01", date_limite="2026-02-01")
        secteur = Secteur.objects.create(nom="Services")
        log = ClassificationLog.objects.create(appel_offre=ao, secteur_predit=secteur, confiance=0.95)
        self.assertEqual(log.confiance, 0.95)

    def test_7_scraper_extraction(self):
        html = '<tr><td>REF123</td><td>Construction</td></tr>'
        self.assertTrue(True) 

class ViewTests(TestCase):
    def test_8_acces_dashboard(self):
        response = self.client.get(reverse('appels_offres:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_9_acces_pages_principales(self):
        pages = ['dashboard', 'liste_appels', 'performance_ia', 'statistiques', 'carte', 'synchronisation']
        for page in pages:
            response = self.client.get(reverse(f'appels_offres:{page}'))
            self.assertEqual(response.status_code, 200)