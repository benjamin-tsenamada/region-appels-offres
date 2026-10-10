"""
Module de classification automatique du secteur d'un appel d'offres
via TF-IDF + SVM linéaire (plus performant que Naive Bayes sur les textes courts).
"""
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), "secteur_model.pkl")


def build_pipeline():
    """Crée le pipeline TF-IDF + SVM linéaire calibré (pour avoir predict_proba)."""
    base_svm = LinearSVC(C=1.0, max_iter=2000)
    calibrated = CalibratedClassifierCV(base_svm, cv=3)

    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 3),   # trigrammes pour capturer plus de contexte
            min_df=2,             # ignorer les mots trop rares
            max_df=0.9,           # ignorer les mots trop fréquents
        )),
        ("clf", calibrated),
    ])


def train_and_save(textes, labels):
    """Entraîne le modèle et le sauvegarde sur disque."""
    pipeline = build_pipeline()
    pipeline.fit(textes, labels)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    return pipeline


def load_model():
    """Charge le modèle entraîné depuis le disque."""
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_secteur(texte):
    """
    Prédit le secteur pour un texte donné.
    Retourne (secteur_predit, confiance) ou (None, 0.0).
    """
    model = load_model()
    if model is None:
        return None, 0.0

    try:
        prediction = model.predict([texte])[0]
        probabilites = model.predict_proba([texte])[0]
        confiance = max(probabilites)
        return prediction, float(confiance)
    except Exception:
        return None, 0.0