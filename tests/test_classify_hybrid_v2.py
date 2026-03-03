"""
Testes unitários para src/models_classifiers/classify_hybrid_v2.py

Cobre:
    extract_color_features() — extração de 24 features
    hybrid_classify_v2() — classificação híbrida com saturação
"""
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.models_classifiers.classify_hybrid_v2 import (
    extract_color_features,
    hybrid_classify_v2,
    SAT_HIGH_THRESHOLD,
    SAT_MID_UPPER_THRESHOLD,
    SAT_LOW_THRESHOLD,
    SAT_VERY_LOW_THRESHOLD,
)


# =============================================================================
# HELPERS
# =============================================================================

def create_test_image_file(tmp_path, saturation: int = 100, size: int = 128) -> Path:
    """Cria arquivo de imagem temporário com saturação específica."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90  # Hue (verde)
    hsv[:, :, 1] = saturation  # Saturação
    hsv[:, :, 2] = 200  # Value
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    image_path = tmp_path / "test_image.jpg"
    cv2.imwrite(str(image_path), bgr)
    return image_path


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_image_dir(tmp_path):
    """Diretório temporário para imagens de teste."""
    return tmp_path / "images"


@pytest.fixture
def high_saturation_image(tmp_path):
    """Imagem com saturação alta (>120)."""
    return create_test_image_file(tmp_path, saturation=150)


@pytest.fixture
def low_saturation_image(tmp_path):
    """Imagem com saturação baixa (<30)."""
    return create_test_image_file(tmp_path, saturation=20)


@pytest.fixture
def mid_saturation_image(tmp_path):
    """Imagem com saturação média (50-100)."""
    return create_test_image_file(tmp_path, saturation=75)


@pytest.fixture
def mock_model_and_scaler():
    """Mock do modelo SVM e scaler."""
    model = MagicMock()
    scaler = MagicMock()

    # SVM retorna predição e decision_function
    model.predict.return_value = np.array([1])  # Tampinha
    model.decision_function.return_value = np.array([0.5])

    # Scaler retorna features escaladas
    scaler.transform.return_value = np.array([[1.0] * 24])

    return model, scaler


# =============================================================================
# TestExtractColorFeatures
# =============================================================================

class TestExtractColorFeatures:
    """Testes para extract_color_features()."""

    def test_extract_features_returns_24_dimensions(self, high_saturation_image):
        """Deve retornar vetor de 24 features."""
        # Act
        features = extract_color_features(str(high_saturation_image))

        # Assert
        assert isinstance(features, np.ndarray)
        assert features.shape == (24,)

    def test_extract_features_components(self, high_saturation_image):
        """Deve conter 3 componentes: RGB (9) + HSV (9) + Shape (6)."""
        # Act
        features = extract_color_features(str(high_saturation_image))

        # Assert
        # Verificar que é um array válido de floats
        assert features.dtype in [np.float32, np.float64, np.int32, np.int64]
        # Verificar tamanho total
        assert len(features) == 24

    def test_extract_features_nonexistent_file(self):
        """Deve retornar None se arquivo não existe."""
        # Act
        features = extract_color_features("/nonexistent/path/image.jpg")

        # Assert
        assert features is None

    def test_extract_features_no_nan(self, high_saturation_image):
        """Não deve conter NaN nos features."""
        # Act
        features = extract_color_features(str(high_saturation_image))

        # Assert
        assert not np.isnan(features).any()

    def test_extract_features_reasonable_values(self, high_saturation_image):
        """Valores devem estar em ranges razoáveis."""
        # Act
        features = extract_color_features(str(high_saturation_image))

        # Assert
        # RGB stats (0-255) + HSV stats + shape (0-1)
        assert features.min() >= -100  # Alguma tolerância
        assert features.max() <= 10000  # Valores podem ser grandes (área normalizada)

    def test_extract_features_reproducible(self, high_saturation_image):
        """Deve retornar mesmo vetor para mesma imagem."""
        # Act
        features1 = extract_color_features(str(high_saturation_image))
        features2 = extract_color_features(str(high_saturation_image))

        # Assert
        np.testing.assert_array_almost_equal(features1, features2)

    def test_extract_features_different_saturation(self, tmp_path):
        """Deve extrair features diferentes para imagens com saturação diferente."""
        # Arrange
        img1 = create_test_image_file(tmp_path, saturation=30)
        img2 = create_test_image_file(tmp_path, saturation=200)

        # Act
        features1 = extract_color_features(str(img1))
        features2 = extract_color_features(str(img2))

        # Assert
        # Devem ser diferentes
        assert not np.allclose(features1, features2)


# =============================================================================
# TestHybridClassifyV2
# =============================================================================

class TestHybridClassifyV2:
    """Testes para hybrid_classify_v2()."""

    def test_classify_returns_four_elements(self, high_saturation_image, mock_model_and_scaler):
        """Deve retornar tupla com (pred, conf, sat, method)."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        result = hybrid_classify_v2(str(high_saturation_image), model, scaler)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 4
        pred, conf, sat, method = result
        assert pred in [0, 1, None]
        assert isinstance(conf, (float, type(None)))
        assert isinstance(sat, (float, type(None)))
        assert isinstance(method, str)

    def test_classify_sat_high_tampinha(self, high_saturation_image, mock_model_and_scaler):
        """Saturação alta (>120) e SVM prediz tampinha → SAT_HIGH."""
        # Arrange
        model, scaler = mock_model_and_scaler
        model.predict.return_value = np.array([1])  # Tampinha

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(high_saturation_image), model, scaler
        )

        # Assert
        assert pred == 1
        assert conf == 0.95
        assert sat >= SAT_HIGH_THRESHOLD
        assert method == "SAT_HIGH"

    def test_classify_sat_high_not_tampinha(self, high_saturation_image, mock_model_and_scaler):
        """Saturação alta (>120) mas SVM prediz não-tampinha → SAT_HIGH (confiança menor)."""
        # Arrange
        model, scaler = mock_model_and_scaler
        model.predict.return_value = np.array([0])  # Não-tampinha

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(high_saturation_image), model, scaler
        )

        # Assert
        assert pred == 1  # Saturação alta força tampinha
        assert conf == 0.90  # Confiança menor por discordância
        assert method == "SAT_HIGH"

    def test_classify_sat_very_low(self, low_saturation_image, mock_model_and_scaler):
        """Saturação muito baixa (<30) → SAT_VERY_LOW (não-tampinha)."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(low_saturation_image), model, scaler
        )

        # Assert
        assert pred == 0
        assert conf == 0.95
        assert sat < SAT_VERY_LOW_THRESHOLD
        assert method == "SAT_VERY_LOW"

    def test_classify_invalid_image(self, mock_model_and_scaler):
        """Imagem inválida ou não encontrada → ERRO."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            "/nonexistent/image.jpg", model, scaler
        )

        # Assert
        assert pred is None
        assert conf is None
        assert sat is None
        assert method == "ERRO"

    def test_classify_nan_features(self, high_saturation_image, mock_model_and_scaler):
        """Features com NaN → ERRO."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        with patch(
            'src.models_classifiers.classify_hybrid_v2.extract_color_features',
            return_value=np.array([np.nan] * 24)
        ):
            pred, conf, sat, method = hybrid_classify_v2(
                str(high_saturation_image), model, scaler
            )

        # Assert
        assert pred is None
        assert method == "ERRO"

    def test_classify_mid_saturation_svm_high_conf(self, mid_saturation_image, mock_model_and_scaler):
        """Saturação média, SVM prediz tampinha com confiança alta."""
        # Arrange
        model, scaler = mock_model_and_scaler
        model.predict.return_value = np.array([1])
        model.decision_function.return_value = np.array([1.5])  # Confiança alta

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(mid_saturation_image), model, scaler
        )

        # Assert
        assert pred == 1
        # Confidence será sigmoid(1.5) ≈ 0.82
        assert method == "SVM_HIGH_CONF"

    def test_classify_low_saturation_force_tampinha(self, tmp_path, mock_model_and_scaler):
        """Saturação baixa (SAT_LOW range) → força tampinha."""
        # Arrange
        model, scaler = mock_model_and_scaler
        image = create_test_image_file(tmp_path, saturation=40)

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(image), model, scaler
        )

        # Assert
        assert pred == 1
        assert method == "LOW_SAT_FORCE_TAMPINHA"

    def test_classify_confidence_values_valid_range(self, high_saturation_image, mock_model_and_scaler):
        """Confiança deve estar entre 0 e 1."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        _, conf, _, _ = hybrid_classify_v2(
            str(high_saturation_image), model, scaler
        )

        # Assert
        assert 0 <= conf <= 1

    def test_classify_saturation_extraction_index_12(self, high_saturation_image, mock_model_and_scaler):
        """Verificar que saturação é extraída do índice correto (12) no vetor de 24."""
        # Arrange
        model, scaler = mock_model_and_scaler
        # Mock extract_color_features para retornar vetor controlado
        features = np.zeros(24)
        features[12] = 150.0  # Saturação no índice 12

        # Act
        with patch(
            'src.models_classifiers.classify_hybrid_v2.extract_color_features',
            return_value=features
        ):
            _, _, sat, _ = hybrid_classify_v2(
                str(high_saturation_image), model, scaler
            )

        # Assert
        assert sat == 150.0

    def test_classify_scaler_transform_called(self, high_saturation_image, mock_model_and_scaler):
        """Deve chamar scaler.transform() para normalizar features."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        hybrid_classify_v2(str(high_saturation_image), model, scaler)

        # Assert
        scaler.transform.assert_called_once()

    def test_classify_model_predict_called(self, high_saturation_image, mock_model_and_scaler):
        """Deve chamar model.predict() para classificação SVM."""
        # Arrange
        model, scaler = mock_model_and_scaler

        # Act
        hybrid_classify_v2(str(high_saturation_image), model, scaler)

        # Assert
        model.predict.assert_called()

    def test_classify_with_custom_threshold(self, high_saturation_image, mock_model_and_scaler):
        """Deve respeitar threshold customizado."""
        # Arrange
        model, scaler = mock_model_and_scaler
        model.predict.return_value = np.array([1])

        # Act
        pred, conf, sat, method = hybrid_classify_v2(
            str(high_saturation_image), model, scaler,
            sat_threshold=200  # Threshold muito alto
        )

        # Assert
        # Com threshold=200, saturação ~150 NÃO entrará em SAT_HIGH
        assert method != "SAT_HIGH"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.unit
def test_extract_and_classify_pipeline(tmp_path, mock_model_and_scaler):
    """Teste de pipeline completo: extract → classify."""
    # Arrange
    model, scaler = mock_model_and_scaler
    model.predict.return_value = np.array([1])
    image = create_test_image_file(tmp_path, saturation=150)

    # Act
    features = extract_color_features(str(image))
    pred, conf, sat, method = hybrid_classify_v2(str(image), model, scaler)

    # Assert
    assert features.shape == (24,)
    assert pred == 1
    assert sat >= SAT_HIGH_THRESHOLD
