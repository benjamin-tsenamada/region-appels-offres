from django.test import TestCase
from appels_offres.models import AppelOffre

class AppelOffreTestCase(TestCase):
    def test_creation_appel_offre(self):
        """Vérifie qu'on peut créer un appel d'offre dans la base."""
        ao = AppelOffre.objects.create(
            titre="Test de construction",
            autorite_contractante="Ma Région",
            date_publication="2026-01-01",
            date_limite="2026-02-01",
            statut="publie"
        )
        self.assertEqual(ao.titre, "Test de construction")

# Create your tests here.
