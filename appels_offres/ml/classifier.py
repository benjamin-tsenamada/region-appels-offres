"""
Module de classification automatique du secteur d'un appel d'offres
à partir de son texte (titre + description), via TF-IDF + Naive Bayes.
"""
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), "secteur_model.pkl")


def build_pipeline():
    """Crée le pipeline TF-IDF + Naive Bayes (non entraîné)."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
        )),
        ("clf", MultinomialNB()),
    ])


def train_and_save(textes, labels):
    """
    Entraîne le modèle sur les textes/labels fournis et le sauvegarde sur disque.
    """
    pipeline = build_pipeline()
    pipeline.fit(textes, labels)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    return pipeline


def load_model():
    """Charge le modèle entraîné depuis le disque. Retourne None si inexistant."""
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_secteur(texte):
    """
    Prédit le secteur pour un texte donné.
    Retourne un tuple (secteur_predit, confiance) ou (None, 0.0) si pas de modèle.
    """
    model = load_model()
    if model is None:
        return None, 0.0

    prediction = model.predict([texte])[0]
    probabilites = model.predict_proba([texte])[0]
    confiance = max(probabilites)
    return prediction, float(confiance)