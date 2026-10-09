\# Plateforme de gestion et classification intelligente des appels d'offres



Application web développée dans le cadre d'un stage de fin d'études au sein de la \*\*Région Atsimo-Andrefana\*\*. Elle permet d'agréger, classifier automatiquement et suivre en temps réel les appels d'offres publics.



🌐 \*\*Démo en ligne\*\* : \[https://region-appels-offres.onrender.com](https://region-appels-offres.onrender.com)



\---



\## 📸 Aperçu



!\[Tableau de bord](docs/dashboard.png)



\---



\## 🎯 Objectif du projet



Concevoir et développer une application web intelligente permettant d'\*\*agréger\*\*, de \*\*classifier automatiquement\*\* et de \*\*suivre en temps réel\*\* les appels d'offres publics de la Région Atsimo-Andrefana.



L'objectif est de faciliter la recherche pour les entreprises soumissionnaires en centralisant les informations et en utilisant des techniques de \*\*traitement automatique du langage (NLP)\*\* pour catégoriser les appels selon :

\- leur \*\*secteur d'activité\*\* (Travaux, Fournitures, Services, Prestations intellectuelles)

\- leur \*\*région / district\*\*

\- leur \*\*date limite\*\*



\---



\## ✨ Fonctionnalités



\- 📊 \*\*Tableau de bord\*\* : indicateurs clés (AO actifs, montant total, échéances proches), répartition par type de procédure (graphique circulaire interactif)

\- 📋 \*\*Recherche et filtres\*\* : par mot-clé, secteur, district, statut, date limite

\- 🗺️ \*\*Carte interactive\*\* : visualisation géographique des appels d'offres par district (Leaflet + OpenStreetMap)

\- 🤖 \*\*Classification NLP\*\* : catégorisation automatique des appels d'offres par secteur

\- ✅ \*\*Correction manuelle des prédictions\*\* : traçabilité pour mesurer la précision du modèle

\- 📈 \*\*Page Performance IA\*\* : taux de précision, matrice de confusion, confiance moyenne du modèle

\- 🔐 \*\*Administration Django\*\* : gestion complète des données



\---



\## 🛠️ Stack technique



\*\*Backend\*\*

\- Python 3.14

\- Django 6.1

\- Django REST Framework

\- Gunicorn

\- WhiteNoise

\- python-dotenv

\- dj-database-url



\*\*Base de données\*\*

\- PostgreSQL (production — Neon.tech)

\- SQLite (développement local)



\*\*Intelligence artificielle / NLP\*\*

\- Scikit-learn

\- pandas

\- NumPy

\- SciPy

\- Joblib



\*\*Frontend\*\*

\- Bootstrap 5

\- Leaflet.js

\- Chart.js

\- JavaScript



\*\*Déploiement\*\*

\- Git / GitHub

\- Render (hébergement)

\- Neon.tech (base PostgreSQL)



\---



\## 🚀 Installation locale



\### Prérequis

\- Python 3.12+

\- Git



\### Étapes



```bash

\# 1. Cloner le dépôt

git clone https://github.com/benjamin-tsenamada/region-appels-offres.git

cd region-appels-offres



\# 2. Créer un environnement virtuel

python -m venv venv

venv\\Scripts\\activate          # Windows

\# source venv/bin/activate     # Linux/Mac



\# 3. Installer les dépendances

pip install -r requirements.txt



\# 4. Créer un fichier .env

\#    (copier le contenu ci-dessous et adapter)



\# 5. Appliquer les migrations

python manage.py migrate



\# 6. Créer un super-utilisateur

python manage.py createsuperuser



\# 7. Lancer le serveur

python manage.py runserver

