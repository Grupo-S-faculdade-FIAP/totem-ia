"""
Testes do ImageClassifier — todos os caminhos de classificação.

Cobre:
    SAT_HIGH, SAT_VERY_LOW, MID_HIGH_SAT, ACCEPT_MID_SAT,
    LOW_SAT_FORCE_TAMPINHA, NORMAL_SAT_TAMPINHA, DEBUG_MODE, ERRO
"""
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock

from src.modules.image import ImageClassifier


# =============================================================================
# HELPERS
# =============================================================================

def create_image_with_saturation(saturation: int, size: int = 128) -> np.ndarray:
    """Cria imagem BGR 128x128 com saturação HSV exata (0-255)."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90          # Hue (verde)
    hsv[:, :, 1] = saturation  # Saturação
    hsv[:, :, 2] = 200         # Value (brilho)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def classifier() -> ImageClassifier:
    """Classificador com modelo SVM mockado."""
    clf = ImageClassifier()
    clf.model = MagicMock()
    clf.scaler = MagicMock()
    clf.model.predict.return_value = [1]
    clf.model.decision_function.return_value = [2.5]
    clf.scaler.transform.return_value = np.array([[0.5] * 8])
    return clf


# =============================================================================
# TestExtractColorFeatures
# =============================================================================

class TestExtractColorFeatures:
    def test_retorna_8_features(self):
        """extract_color_features deve retornar vetor com exatamente 8 valores."""
        clf = ImageClassifier()
        image = create_image_with_saturation(100)
        features = clf.extract_color_features(image)
        assert features is not None
        assert features.shape == (8,)

    def test_imagem_invalida_retorna_none(self):
        """Entrada que não é ndarray deve retornar None."""
        clf = ImageClassifier()
        result = clf.extract_color_features("nao_eh_array")  # type: ignore
        assert result is None

    def test_features_deterministicas(self):
        """Mesma imagem deve sempre produzir o mesmo vetor de features."""
        clf = ImageClassifier()
        image = create_image_with_saturation(120)
        f1 = clf.extract_color_features(image)
        f2 = clf.extract_color_features(image)
        assert f1 is not None and f2 is not None
        assert np.allclose(f1, f2)

    def test_feature_6_e_saturacao(self):
        """features[6] deve refletir a saturação média da imagem (HSV)."""
        clf = ImageClassifier()
        image_alta = create_image_with_saturation(200)
        image_baixa = create_image_with_saturation(10)
        f_alta = clf.extract_color_features(image_alta)
        f_baixa = clf.extract_color_features(image_baixa)
        assert f_alta is not None and f_baixa is not None
        assert f_alta[6] > f_baixa[6]


# =============================================================================
# TestClassifyImage — caminhos de decisão
# =============================================================================

class TestClassifyImage:

    # ── Erros / prerequisites ─────────────────────────────────────────────

    def test_imagem_none_retorna_erro(self, classifier: ImageClassifier):
        """classify_image(None) deve retornar tuple de erro sem travar."""
        pred, conf, sat, method = classifier.classify_image(None)
        assert pred is None
        assert method == "ERRO"

    def test_modelo_none_retorna_erro(self):
        """Sem modelo carregado, classify_image deve retornar ERRO."""
        clf = ImageClassifier()
        clf.scaler = MagicMock()
        image = create_image_with_saturation(150)
        pred, conf, sat, method = clf.classify_image(image)
        assert pred is None
        assert method == "ERRO"

    def test_scaler_none_retorna_erro(self):
        """Sem scaler carregado, classify_image deve retornar ERRO."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        image = create_image_with_saturation(150)
        pred, conf, sat, method = clf.classify_image(image)
        assert pred is None
        assert method == "ERRO"

    # ── SAT_HIGH ──────────────────────────────────────────────────────────

    def test_sat_high_retorna_tampinha(self, classifier: ImageClassifier):
        """Saturação > 120 → TAMPINHA via SAT_HIGH, confiança ≥ 0.90."""
        image = create_image_with_saturation(180)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert conf is not None and conf >= 0.90
        assert method == "SAT_HIGH"

    def test_sat_high_retorna_saturation_float(self, classifier: ImageClassifier):
        """Saturação retornada deve ser float."""
        image = create_image_with_saturation(180)
        _, _, sat, _ = classifier.classify_image(image)
        assert isinstance(sat, float)

    # ── SAT_VERY_LOW ──────────────────────────────────────────────────────

    def test_sat_very_low_retorna_nao_tampinha(self, classifier: ImageClassifier):
        """Saturação < 30 → NÃO-TAMPINHA via SAT_VERY_LOW, confiança = 0.95."""
        image = create_image_with_saturation(5)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 0
        assert conf == 0.95
        assert method == "SAT_VERY_LOW"

    # ── MID_HIGH_SAT / ACCEPT_MID_SAT ────────────────────────────────────

    def test_mid_high_sat_svm_aceita(self, classifier: ImageClassifier):
        """100 < sat ≤ 120, SVM pred=1 → MID_HIGH_SAT."""
        classifier.model.predict.return_value = [1]
        image = create_image_with_saturation(110)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert method == "MID_HIGH_SAT"

    def test_mid_high_sat_svm_rejeita_aceita_mesmo_assim(self, classifier: ImageClassifier):
        """100 < sat ≤ 120, SVM pred=0 → ACCEPT_MID_SAT (aceita tampinha mesmo assim)."""
        classifier.model.predict.return_value = [0]
        image = create_image_with_saturation(110)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert method == "ACCEPT_MID_SAT"

    # ── NORMAL_SAT_TAMPINHA ───────────────────────────────────────────────

    def test_normal_sat_tampinha(self, classifier: ImageClassifier):
        """50 ≤ sat ≤ 100 → NORMAL_SAT_TAMPINHA, confiança = 0.80."""
        image = create_image_with_saturation(75)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert conf == 0.80
        assert method == "NORMAL_SAT_TAMPINHA"

    # ── LOW_SAT_FORCE_TAMPINHA ────────────────────────────────────────────

    def test_low_sat_force_tampinha(self, classifier: ImageClassifier):
        """30 ≤ sat < 50 → LOW_SAT_FORCE_TAMPINHA, confiança = 0.75."""
        image = create_image_with_saturation(40)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert conf == 0.75
        assert method == "LOW_SAT_FORCE_TAMPINHA"

    # ── DEBUG_MODE ────────────────────────────────────────────────────────

    def test_debug_mode_ativa_para_sat_media(self, classifier: ImageClassifier):
        """Modo debug + sat > 50 → DEBUG_MODE, confiança = 0.95."""
        image = create_image_with_saturation(75)
        pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=True)
        assert pred == 1
        assert conf == 0.95
        assert method == "DEBUG_MODE"

    def test_debug_mode_nao_ativa_para_sat_muito_baixa(self, classifier: ImageClassifier):
        """Modo debug com sat < 30 → SAT_VERY_LOW (debug não se aplica antes do check de sat)."""
        image = create_image_with_saturation(5)
        pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=True)
        assert pred == 0
        assert method == "SAT_VERY_LOW"

    def test_debug_mode_falso_nao_interfere(self, classifier: ImageClassifier):
        """is_debug_mode=False deve seguir o fluxo normal."""
        image = create_image_with_saturation(75)
        pred, conf, sat, method = classifier.classify_image(image, is_debug_mode=False)
        assert method == "NORMAL_SAT_TAMPINHA"
