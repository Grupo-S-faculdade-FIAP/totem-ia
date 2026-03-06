"""
Testes property-based para ImageClassifier (ML/IA).

Foco:
    - Robustez da extração de features para imagens válidas aleatórias
    - Tratamento seguro de entradas inválidas
    - Invariantes de decisão por faixa de saturação
"""
from __future__ import annotations

from unittest.mock import MagicMock

import cv2
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra.numpy import arrays

from src.modules.image import ImageClassifier


@pytest.fixture
def classifier() -> ImageClassifier:
    """Classificador com modelo/scaler mockados para testes determinísticos."""
    clf = ImageClassifier()
    clf.model = MagicMock()
    clf.scaler = MagicMock()
    clf.model.predict.return_value = [1]
    clf.model.decision_function.return_value = [1.2]
    clf.scaler.transform.return_value = np.array([[0.1] * 332], dtype=np.float64)
    return clf


def _solid_bgr_from_saturation(saturation: int, size: int = 64) -> np.ndarray:
    """Cria imagem BGR sólida a partir de saturação HSV controlada."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = saturation
    hsv[:, :, 2] = 200
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


@settings(max_examples=60, deadline=None)
@given(
    image=arrays(
        dtype=np.uint8,
        shape=st.tuples(
            st.integers(min_value=32, max_value=128),
            st.integers(min_value=32, max_value=128),
            st.just(3),
        ),
        elements=st.integers(min_value=0, max_value=255),
    )
)
def test_extract_color_features_random_uint8_image_returns_valid_vector(image: np.ndarray) -> None:
    """Para qualquer imagem uint8 HxWx3 válida, features devem ser vetor 12 sem NaN."""
    clf = ImageClassifier()
    features = clf.extract_color_features(image)

    assert features is not None
    assert features.shape == (332,)
    assert not np.isnan(features).any()
    assert np.isfinite(features).all()


@settings(max_examples=20, deadline=None)
@given(
    image=arrays(
        dtype=np.uint8,
        shape=st.tuples(
            st.integers(min_value=16, max_value=64),
            st.integers(min_value=16, max_value=64),
        ),
        elements=st.integers(min_value=0, max_value=255),
    )
)
def test_extract_color_features_rejects_non_3d_inputs(image: np.ndarray) -> None:
    """Entradas sem 3 canais devem ser rejeitadas com retorno None."""
    clf = ImageClassifier()
    assert clf.extract_color_features(image) is None


@settings(max_examples=40, deadline=None)
@given(saturation=st.integers(min_value=0, max_value=255))
def test_classify_image_method_matches_saturation_buckets(
    saturation: int
) -> None:
    """
    Método retornado deve estar dentro dos métodos possíveis da implementação atual:
    CV_NO_CIRCLE, SVM_ACCEPT, CV_CIRCLE_CONFIRMED, CV_REJECT, ERRO.
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [1.2]
    classifier.scaler.transform.return_value = np.array([[0.1] * 332], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    assert pred in (0, 1)
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)
    # Metodos validos na implementacao atual (image.py)
    valid_methods = {"SVM_ACCEPT", "CV_NO_CIRCLE", "CV_CIRCLE_CONFIRMED", "ERRO"}
    assert method in valid_methods or method.startswith("CV_REJECT")
    # Saturacao abaixo de SAT_VERY_LOW_THRESHOLD (30) nunca aceita
    if sat < 30:
        assert pred == 0


@settings(max_examples=50, deadline=None)
@given(saturation=st.integers(min_value=30, max_value=119))
def test_classify_rejects_when_margin_is_low_even_with_positive_pred(
    saturation: int
) -> None:
    """
    Com margem abaixo do SVM_SOFT_THRESHOLD (-0.50), o sistema rejeita.
    Faixa de sat 30-119 para evitar o gate SAT_VERY_LOW (<30).
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [-0.80]  # margem < -0.50 = SOFT_THRESHOLD
    classifier.scaler.transform.return_value = np.array([[0.1] * 332], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    # Com imagem solida sem contornos detec taveis e margem < threshold, rejeita
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)
    # Metodo de rejeicao deve ser CV_NO_CIRCLE ou CV_REJECT
    assert method == "CV_NO_CIRCLE" or method.startswith("CV_REJECT")


@settings(max_examples=50, deadline=None)
@given(saturation=st.integers(min_value=30, max_value=255))
def test_classify_accepts_when_margin_is_high_and_pred_positive(
    saturation: int
) -> None:
    """
    Para sat >= 30, margem acima do SVM_SOFT_THRESHOLD (-0.50) deve aceitar.
    Garante consistência do pipeline SVM quando confiança é alta.
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [2.50]  # margem muito acima de -0.50
    classifier.scaler.transform.return_value = np.array([[0.1] * 332], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    assert pred == 1
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)
    assert method in {"SVM_ACCEPT", "CV_CIRCLE_CONFIRMED"}
