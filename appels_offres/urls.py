from django.urls import path
from . import views

app_name = "appels_offres"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]