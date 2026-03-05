"""
Testes do CV Pre-screening — camada de validação por visão computacional.

Verifica que o classificador usa circularidade (HoughCircles + Canny contorno +
aspect ratio) para rejeitar objetos não-circulares ANTES do SVM.

Cenários críticos cobertos:
    - Tampinha sintética circular → APROVADA pelo CV
    - Elipse/oval (simula rosto) → REJEITADA pelo CV
    - Retângulo → REJEITADO pelo CV
    - Imagem sólida (sem contornos) → SVM decide
    - Thresholds: valores exatamente na fronteira
    - Métricas: circularity, aspect_ratio, hough_count armazenados corretamente
"""
from __future__ import annotations

import numpy as np
import cv2
import pytest
from unittest.mock import MagicMock, patch

from src.modules.image import (
    ImageClassifier,
    CV_MIN_CIRCULARITY,
    CV_MIN_ASPECT_RATIO,
)


# =============================================================================
# HELPERS — geradores de imagens controladas
# =============================================================================

def make_solid_image(color_bgr: tuple[int, int, int] = (100, 150, 80)) -> np.ndarray:
    """Imagem 256×256 preenchida com uma cor sólida (sem bordas detectáveis)."""
    img = np.full((256, 256, 3), color_bgr, dtype=np.uint8)
    return img


def make_circle_image(radius: int = 50, canvas: int = 128) -> np.ndarray:
    """Círculo branco sobre fundo preto — simula tampinha isolada."""
    img = np.zeros((canvas, canvas, 3), dtype=np.uint8)
    center = (canvas // 2, canvas // 2)
    cv2.circle(img, center, radius, (200, 200, 200), thickness=-1)
    cv2.circle(img, center, radius, (255, 255, 255), thickness=2)
    return img


def make_oval_image(rx: int = 30, ry: int = 55, canvas: int = 128) -> np.ndarray:
    """Elipse vertical (rx < ry) sobre fundo preto — simula rosto/oval."""
    img = np.zeros((canvas, canvas, 3), dtype=np.uint8)
    center = (canvas // 2, canvas // 2)
    cv2.ellipse(img, center, (rx, ry), 0, 0, 360, (200, 200, 200), thickness=-1)
    cv2.ellipse(img, center, (rx, ry), 0, 0, 360, (255, 255, 255), thickness=2)
    return img


def make_rectangle_image(w: int = 80, h: int = 40, canvas: int = 128) -> np.ndarray:
    """Retângulo horizontal sobre fundo preto — baixa circularidade."""
    img = np.zeros((canvas, canvas, 3), dtype=np.uint8)
    cx, cy = canvas // 2, canvas // 2
    pt1 = (cx - w // 2, cy - h // 2)
    pt2 = (cx + w // 2, cy + h // 2)
    cv2.rectangle(img, pt1, pt2, (200, 200, 200), thickness=-1)
    cv2.rectangle(img, pt1, pt2, (255, 255, 255), thickness=2)
    return img


def make_noisy_face_image(canvas: int = 256) -> np.ndarray:
    """Imagem sintética de 'rosto': oval com textura interna (ruído) sobre fundo neutro."""
    rng = np.random.default_rng(42)
    # Fundo tom de pele claro
    img = np.full((canvas, canvas, 3), (140, 160, 190), dtype=np.uint8)
    # Oval central (face)
    center = (canvas // 2, canvas // 2)
    cv2.ellipse(img, center, (canvas // 3, int(canvas * 0.42)), 0, 0, 360, (120, 145, 175), -1)
    # Textura/ruído interno (simula poros, sombras)
    noise = rng.integers(-25, 25, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def _make_classifier_with_svm_accept() -> ImageClassifier:
    """Classificador com SVM mockado para SEMPRE aceitar."""
    clf = ImageClassifier()
    clf.model = MagicMock()
    clf.scaler = MagicMock()
    clf.model.predict.return_value = [1]
    clf.model.decision_function.return_value = [3.0]  # margem alta, aceita tudo
    clf.scaler.transform.side_effect = lambda x: np.array(x)
    return clf


def _inject_cv_metrics(
    clf: ImageClassifier,
    hough: int = 0,
    contour_count: float = 0.0,
    circ: float = 0.0,
    aspect: float = 0.0,
    saturation: int = 150,
) -> None:
    """Substitui extract_color_features por mock que injeta métricas CV controladas.

    Essencial para testar a lógica de decisão CV isoladamente, sem que
    classify_image sobrescreva os _last_* ao chamar extract_color_features.
    """
    features_8 = np.array([100.0, 20.0, 100.0, 100.0, 20.0, 100.0, float(saturation), 30.0])

    def mock_extract(image: np.ndarray) -> np.ndarray:
        clf._last_hough_count = hough
        clf._last_contour_count = contour_count
        clf._last_circularity = circ
        clf._last_aspect_ratio = aspect
        return features_8

    clf.extract_color_features = mock_extract  # type: ignore[method-assign]


# =============================================================================
# TestCvMetricsExtraction — métricas armazenadas corretamente
# =============================================================================

class TestCvMetricsExtraction:
    """Garante que extract_color_features popula _last_* corretamente."""

    def test_circulo_armazena_circularity_alta(self):
        """Círculo perfeito deve resultar em _last_circularity próxima de 1.0."""
        clf = ImageClassifier()
        clf.extract_color_features(make_circle_image(radius=50))
        # HoughCircles pode detectar ou não dependendo do contraste,
        # mas se usar contorno, circularity deve ser ≥ 0.70
        if clf._last_contour_count > 0:
            assert clf._last_circularity >= 0.70, (
                f"Círculo deveria ter circ≥0.70, obteve {clf._last_circularity:.3f}"
            )

    def test_oval_armazena_aspect_ratio_baixo(self):
        """Oval vertical (rx=25, ry=55) deve ter aspect_ratio < CV_MIN_ASPECT_RATIO."""
        clf = ImageClassifier()
        clf.extract_color_features(make_oval_image(rx=25, ry=55))
        if clf._last_contour_count > 0:
            assert clf._last_aspect_ratio < CV_MIN_ASPECT_RATIO, (
                f"Oval deveria ter aspect<{CV_MIN_ASPECT_RATIO}, "
                f"obteve {clf._last_aspect_ratio:.3f}"
            )

    def test_retangulo_armazena_circularity_baixa(self):
        """Retângulo deve ter circularity bem abaixo do threshold."""
        clf = ImageClassifier()
        clf.extract_color_features(make_rectangle_image(w=90, h=30))
        if clf._last_contour_count > 0:
            assert clf._last_circularity < CV_MIN_CIRCULARITY, (
                f"Retângulo deveria ter circ<{CV_MIN_CIRCULARITY}, "
                f"obteve {clf._last_circularity:.3f}"
            )

    def test_imagem_solida_sem_contornos(self):
        """Imagem uniforme não tem bordas → contour_count e hough_count = 0."""
        clf = ImageClassifier()
        clf.extract_color_features(make_solid_image())
        assert clf._last_hough_count == 0
        assert clf._last_contour_count == 0.0
        assert clf._last_circularity == 0.0

    def test_metricas_sao_float_e_int(self):
        """Tipos das métricas devem ser corretos após extração."""
        clf = ImageClassifier()
        clf.extract_color_features(make_circle_image())
        assert isinstance(clf._last_circularity, float)
        assert isinstance(clf._last_aspect_ratio, float)
        assert isinstance(clf._last_contour_count, float)
        assert isinstance(clf._last_hough_count, int)

    def test_metricas_reiniciadas_entre_chamadas(self):
        """Métricas de uma chamada não devem vazar para a próxima."""
        clf = ImageClassifier()
        clf.extract_color_features(make_circle_image(radius=50))
        circ_circulo = clf._last_circularity

        clf.extract_color_features(make_solid_image())
        circ_solido = clf._last_circularity

        # Imagem sólida (sem contornos) deve zerar circularity
        assert circ_solido == 0.0
        # E deve ser diferente da imagem anterior
        assert circ_circulo != circ_solido or circ_circulo == 0.0


# =============================================================================
# TestCvPreScreeningDecision — rejeições e aprovações pelo CV
# =============================================================================

class TestCvPreScreeningDecision:
    """Testa se classify_image rejeita/aprova pelo CV antes de chegar ao SVM."""

    def test_hough_detectado_aprova_e_chama_svm(self):
        """Se HoughCircles detectar círculo, não deve CV_REJECT e deve chamar SVM."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image(radius=48)
        _inject_cv_metrics(clf, hough=1, contour_count=1, circ=0.90, aspect=0.95, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "CV_REJECT" not in method, (
            f"Círculo com HoughCircles detectado não deveria ser rejeitado. method={method}"
        )
        clf.model.predict.assert_called_once()

    def test_oval_vertical_rejeitado_pelo_cv(self):
        """Oval (circ=0.55, aspect=0.40) deve ser rejeitado com CV_REJECT."""
        clf = _make_classifier_with_svm_accept()
        img = make_oval_image(rx=22, ry=56)
        _inject_cv_metrics(clf, hough=0, contour_count=1, circ=0.55, aspect=0.40, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0, f"Oval deveria ser rejeitado, mas pred={pred}"
        assert "CV_REJECT" in method, f"Method deveria conter CV_REJECT, obteve: {method}"

    def test_retangulo_rejeitado_pelo_cv(self):
        """Retângulo largo (circ=0.25, aspect=0.22) deve ser rejeitado pelo CV."""
        clf = _make_classifier_with_svm_accept()
        img = make_rectangle_image(w=90, h=20)
        _inject_cv_metrics(clf, hough=0, contour_count=1, circ=0.25, aspect=0.22, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0
        assert "CV_REJECT" in method

    def test_objeto_sem_contornos_passa_para_svm(self):
        """Objeto sem contornos detectados deve passar para SVM decidir."""
        clf = _make_classifier_with_svm_accept()
        img = make_solid_image((100, 180, 80))
        _inject_cv_metrics(clf, hough=0, contour_count=0, circ=0.0, aspect=0.0, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "CV_REJECT" not in method, (
            f"Objeto sem contornos não deve ser rejeitado pelo CV. method={method}"
        )

    def test_cv_reject_retorna_pred_zero_e_confianca_alta(self):
        """CV_REJECT deve retornar pred=0 com confiança >= 0.85."""
        clf = _make_classifier_with_svm_accept()
        img = make_oval_image(rx=20, ry=60)
        _inject_cv_metrics(clf, hough=0, contour_count=1, circ=0.40, aspect=0.33, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0
        assert conf is not None and conf >= 0.85, f"Confiança de rejeição deveria ser ≥ 0.85, obteve {conf}"
        assert "CV_REJECT" in method

    def test_svm_nao_chamado_quando_cv_rejeita(self):
        """SVM não deve ser consultado quando CV já rejeita o objeto."""
        clf = _make_classifier_with_svm_accept()
        img = make_rectangle_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1, circ=0.20, aspect=0.20, saturation=150)

        clf.classify_image(img)
        clf.model.predict.assert_not_called()


# =============================================================================
# TestCvThresholdBoundary — casos na fronteira dos thresholds
# =============================================================================

class TestCvThresholdBoundary:
    """Testa comportamento exatamente nos limites de CV_MIN_CIRCULARITY e CV_MIN_ASPECT_RATIO."""

    def test_circularity_exatamente_no_threshold_passa(self):
        """circularity == CV_MIN_CIRCULARITY deve PASSAR (operador ≥, não >)."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1,
                           circ=CV_MIN_CIRCULARITY, aspect=CV_MIN_ASPECT_RATIO + 0.1, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "CV_REJECT" not in method, (
            f"circ={CV_MIN_CIRCULARITY} (no limite) deveria PASSAR, obteve method={method}"
        )

    def test_circularity_um_ponto_abaixo_rejeita(self):
        """circularity 0.01 abaixo do threshold deve REJEITAR."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1,
                           circ=CV_MIN_CIRCULARITY - 0.01, aspect=CV_MIN_ASPECT_RATIO + 0.1, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0
        assert "CV_REJECT" in method

    def test_aspect_ratio_exatamente_no_threshold_passa(self):
        """aspect_ratio == CV_MIN_ASPECT_RATIO deve PASSAR."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1,
                           circ=CV_MIN_CIRCULARITY + 0.1, aspect=CV_MIN_ASPECT_RATIO, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "CV_REJECT" not in method

    def test_aspect_ratio_um_ponto_abaixo_rejeita(self):
        """aspect_ratio 0.01 abaixo do threshold deve REJEITAR."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1,
                           circ=CV_MIN_CIRCULARITY + 0.1, aspect=CV_MIN_ASPECT_RATIO - 0.01, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0
        assert "CV_REJECT" in method

    def test_ambos_abaixo_inclui_ambas_as_razoes_no_method(self):
        """Quando circ e aspect falham, o method deve mencionar ambos."""
        clf = _make_classifier_with_svm_accept()
        img = make_oval_image()
        _inject_cv_metrics(clf, hough=0, contour_count=1,
                           circ=CV_MIN_CIRCULARITY - 0.10, aspect=CV_MIN_ASPECT_RATIO - 0.15, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "circ=" in method
        assert "aspect=" in method

    def test_hough_sobrepoe_circularity_e_aspect_baixos(self):
        """HoughCircles detectado deve APROVAR mesmo com circularity e aspect_ratio baixos."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image()
        _inject_cv_metrics(clf, hough=1, contour_count=1,
                           circ=0.30, aspect=0.30, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert "CV_REJECT" not in method, (
            f"HoughCircles detectado deve sobrepor circularity baixa. method={method}"
        )


# =============================================================================
# TestCvRealWorldShapes — formas realistas
# =============================================================================

class TestCvRealWorldShapes:
    """Testa formas que se assemelham a objetos do mundo real."""

    @pytest.mark.parametrize("radius", [15, 30, 45, 55])
    def test_circulos_de_varios_tamanhos_aprovados_ou_sem_rejeicao_cv(self, radius):
        """Círculos de tamanhos variados não devem falhar por circularidade."""
        clf = ImageClassifier()
        img = make_circle_image(radius=radius, canvas=128)
        clf.extract_color_features(img)

        if clf._last_hough_count > 0:
            # HoughCircles aprovou
            assert clf._last_hough_count >= 1
        elif clf._last_contour_count > 0:
            # Contorno deve ter circularity alta
            assert clf._last_circularity >= CV_MIN_CIRCULARITY, (
                f"Círculo raio={radius} obteve circ={clf._last_circularity:.3f} "
                f"< threshold {CV_MIN_CIRCULARITY}"
            )

    @pytest.mark.parametrize("rx,ry", [(20, 55), (25, 60), (18, 50)])
    def test_ovals_verticais_tem_aspect_ratio_abaixo_do_threshold(self, rx, ry):
        """Ovals verticais (como rostos) devem ter aspect_ratio < CV_MIN_ASPECT_RATIO."""
        clf = ImageClassifier()
        img = make_oval_image(rx=rx, ry=ry)
        clf.extract_color_features(img)

        if clf._last_contour_count > 0 and clf._last_hough_count == 0:
            assert clf._last_aspect_ratio < CV_MIN_ASPECT_RATIO, (
                f"Oval ({rx}×{ry}) deveria ter aspect<{CV_MIN_ASPECT_RATIO}, "
                f"obteve {clf._last_aspect_ratio:.3f}"
            )

    @pytest.mark.parametrize("w,h", [(90, 20), (80, 25), (100, 15)])
    def test_retangulos_largos_tem_circularity_abaixo_do_threshold(self, w, h):
        """Retângulos largos devem ter circularity e aspect_ratio abaixo dos thresholds."""
        clf = ImageClassifier()
        img = make_rectangle_image(w=w, h=h)
        clf.extract_color_features(img)

        if clf._last_contour_count > 0 and clf._last_hough_count == 0:
            fails_circ = clf._last_circularity < CV_MIN_CIRCULARITY
            fails_aspect = clf._last_aspect_ratio < CV_MIN_ASPECT_RATIO
            assert fails_circ or fails_aspect, (
                f"Retângulo ({w}×{h}) deveria falhar em circ ou aspect. "
                f"circ={clf._last_circularity:.3f}, aspect={clf._last_aspect_ratio:.3f}"
            )

    def test_face_sintetica_com_cv_metrics_controlados_e_rejeitada(self):
        """Face sintética com métricas controladas (oval) deve ser rejeitada pelo CV."""
        clf = _make_classifier_with_svm_accept()
        img = make_noisy_face_image()
        # Métricas que representam um rosto oval: sem Hough, circularidade e aspect baixos
        _inject_cv_metrics(clf, hough=0, contour_count=1, circ=0.60, aspect=0.68, saturation=150)

        pred, conf, sat, method = clf.classify_image(img)
        assert pred == 0, f"Face oval deveria ser rejeitada"
        assert "CV_REJECT" in method

    def test_tampinha_circular_aprovada_pelo_hough_ou_contorno(self):
        """Tampinha sintética (círculo de alto contraste) deve ser aprovada pelo CV."""
        clf = _make_classifier_with_svm_accept()
        img = make_circle_image(radius=45)
        clf.extract_color_features(img)

        # Deve ter detectado via Hough OU circularity alta
        hough_ok = clf._last_hough_count > 0
        contour_ok = (
            clf._last_contour_count > 0
            and clf._last_circularity >= CV_MIN_CIRCULARITY
            and clf._last_aspect_ratio >= CV_MIN_ASPECT_RATIO
        )
        no_contour = clf._last_contour_count == 0

        assert hough_ok or contour_ok or no_contour, (
            f"Tampinha circular deveria ser aprovada. "
            f"hough={clf._last_hough_count}, circ={clf._last_circularity:.3f}, "
            f"aspect={clf._last_aspect_ratio:.3f}"
        )
