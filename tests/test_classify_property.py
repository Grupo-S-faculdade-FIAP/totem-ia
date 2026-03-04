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
    clf.scaler.transform.return_value = np.array([[0.1] * 8], dtype=np.float64)
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
    """Para qualquer imagem uint8 HxWx3 válida, features devem ser vetor 8 sem NaN."""
    clf = ImageClassifier()
    features = clf.extract_color_features(image)

    assert features is not None
    assert features.shape == (8,)
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
    Método retornado deve respeitar os buckets de saturação do classificador.
    Usa imagem sintética para manter saturação estável no pipeline.
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [1.2]
    classifier.scaler.transform.return_value = np.array([[0.1] * 8], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    assert pred in (0, 1)
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)

    if sat > 120:
        assert method == "SAT_HIGH"
    elif sat < 30:
        assert method == "SAT_VERY_LOW"
    elif sat > 100:
        assert method in {"MID_HIGH_SAT", "ACCEPT_MID_SAT"}
    elif sat < 50:
        assert method == "LOW_SAT_FORCE_TAMPINHA"
    else:
        assert method == "NORMAL_SAT_TAMPINHA"


@settings(max_examples=50, deadline=None)
@given(saturation=st.integers(min_value=30, max_value=255))
def test_classify_rejects_when_margin_is_low_even_with_positive_pred(
    saturation: int
) -> None:
    """
    Em faixas >= 30, predição positiva com margem baixa deve rejeitar.
    Isso evita falsos positivos por confiança fraca do SVM.
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [0.10]  # margem baixa
    classifier.scaler.transform.return_value = np.array([[0.1] * 8], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    assert pred == 0
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)
    assert method in {
        "SAT_HIGH",
        "SAT_VERY_LOW",
        "ACCEPT_MID_SAT",
        "LOW_SAT_FORCE_TAMPINHA",
        "NORMAL_SAT_TAMPINHA",
    }


@settings(max_examples=50, deadline=None)
@given(saturation=st.integers(min_value=30, max_value=255))
def test_classify_accepts_when_margin_is_high_and_pred_positive(
    saturation: int
) -> None:
    """
    Para sat >= 30, predição positiva com margem alta deve aceitar.
    Garante consistência das regras de aceitação por confiança.
    """
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    classifier.model.predict.return_value = [1]
    classifier.model.decision_function.return_value = [2.50]  # margem alta
    classifier.scaler.transform.return_value = np.array([[0.1] * 8], dtype=np.float64)

    image = _solid_bgr_from_saturation(saturation)
    pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)

    assert pred == 1
    assert conf is not None and 0.0 <= conf <= 1.0
    assert sat is not None and isinstance(sat, float)
    assert method in {
        "SAT_HIGH",
        "MID_HIGH_SAT",
        "LOW_SAT_FORCE_TAMPINHA",
        "NORMAL_SAT_TAMPINHA",
    }
