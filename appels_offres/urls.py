from django.urls import path
from . import views

app_name = "appels_offres"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("appels/", views.liste_appels, name="liste_appels"),
    path("appels/<int:pk>/", views.detail_appel, name="detail_appel"),
    path("classification/<int:classification_id>/corriger/", views.corriger_prediction, name="corriger_prediction"),
    path("performance-ia/", views.performance_ia, name="performance_ia"),
    path("carte/", views.carte, name="carte"),
    path("api/carte-data/", views.carte_data, name="carte_data"),
]