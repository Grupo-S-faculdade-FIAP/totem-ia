"""
Testes unitários dos artefatos de modelo (.pkl) usados em produção.

Garante que:
- modelo e scaler existem e carregam corretamente;
- ambos estão alinhados ao vetor de 8 ou 332 features da inferência;
- pipeline scaler -> model funciona em predição e decision_function;
- ImageClassifier consegue carregar e inferir usando os .pkl reais.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import joblib
import numpy as np
import pytest

from src.modules.image import ImageClassifier


MODEL_PATH = Path("models/svm/svm_model_complete.pkl")
SCALER_PATH = Path("models/svm/scaler_complete.pkl")


def _sample_image() -> np.ndarray:
    """Cria imagem BGR simples para smoke test de inferência."""
    hsv = np.zeros((128, 128, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = 120
    hsv[:, :, 2] = 200
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


class TestModelArtifacts:
    def test_model_and_scaler_files_exist(self):
        """Arquivos de artefato devem existir no caminho esperado."""
        assert MODEL_PATH.exists(), f"Modelo não encontrado: {MODEL_PATH}"
        assert SCALER_PATH.exists(), f"Scaler não encontrado: {SCALER_PATH}"

    def test_artifacts_are_trained_for_expected_features(self):
        """Modelo e scaler devem estar treinados com 8 (legacy) ou 332 (8+HOG) features."""
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)

        n_model = getattr(model, "n_features_in_", None)
        n_scaler = getattr(scaler, "n_features_in_", None)
        assert n_model in (8, 332), f"Modelo espera 8 ou 332 features, obteve {n_model}"
        assert n_scaler == n_model, f"Scaler e modelo devem ter mesmo n_features: {n_scaler} vs {n_model}"

    def test_scaler_and_model_pipeline_smoke(self):
        """Pipeline scaler -> model deve processar vetor sem erro."""
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)

        n = getattr(model, "n_features_in_", 8)
        x = np.zeros((1, n), dtype=np.float64)
        x_scaled = scaler.transform(x)
        pred = model.predict(x_scaled)
        decision = model.decision_function(x_scaled)

        assert pred.shape == (1,)
        assert decision.shape == (1,)
        assert pred[0] in (0, 1)

    @pytest.mark.unit
    def test_image_classifier_load_and_infer_with_real_artifacts(self):
        """ImageClassifier deve carregar .pkl reais e inferir sem erro."""
        classifier = ImageClassifier()
        classifier.load_classifier()

        image = _sample_image()
        pred, conf, sat, method = classifier.classify_image(image)

        assert pred in (0, 1)
        assert isinstance(conf, float)
        assert isinstance(sat, float)
        assert method in {
            "SAT_HIGH",
            "SAT_VERY_LOW",
            "MID_HIGH_SAT",
            "ACCEPT_MID_SAT",
            "LOW_SAT_FORCE_TAMPINHA",
            "NORMAL_SAT_TAMPINHA",
            "DEBUG_MODE",
            "ERRO",
            "CV_CIRCLE_CONFIRMED",
            "SVM_ACCEPT",
            "CV_NO_CIRCLE",
            "FACE_DETECTED",
        } or method.startswith("CV_REJECT")
