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
from pathlib import Path

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
    clf.scaler.transform.return_value = np.array([[0.5] * 12])
    return clf


# =============================================================================
# TestExtractColorFeatures
# =============================================================================

class TestExtractColorFeatures:
    def test_retorna_12_features(self):
        """extract_color_features deve retornar vetor com exatamente 12 valores."""
        clf = ImageClassifier()
        image = create_image_with_saturation(100)
        features = clf.extract_color_features(image)
        assert features is not None
        assert features.shape == (12,)

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

    def test_edge_density_entre_zero_e_um(self):
        """features[8] (edge_density) deve estar em [0, 1]."""
        clf = ImageClassifier()
        image = create_image_with_saturation(100)
        features = clf.extract_color_features(image)
        assert features is not None
        assert 0.0 <= features[8] <= 1.0

    def test_contour_count_nao_negativo(self):
        """features[9] (contour_count) deve ser >= 0."""
        clf = ImageClassifier()
        image = create_image_with_saturation(100)
        features = clf.extract_color_features(image)
        assert features is not None
        assert features[9] >= 0.0

    def test_circularity_entre_zero_e_um_para_imagem_solida(self):
        """features[10] (circularity) deve estar em [0, 1.1] para imagem uniforme."""
        clf = ImageClassifier()
        image = create_image_with_saturation(150)
        features = clf.extract_color_features(image)
        assert features is not None
        assert 0.0 <= features[10] <= 1.1

    def test_area_ratio_entre_zero_e_um(self):
        """features[11] (area_ratio) deve estar em [0, 1]."""
        clf = ImageClassifier()
        image = create_image_with_saturation(100)
        features = clf.extract_color_features(image)
        assert features is not None
        assert 0.0 <= features[11] <= 1.0

    def test_features_sem_nan_em_imagem_preta(self):
        """Imagem totalmente preta não deve gerar NaN nas features de borda."""
        clf = ImageClassifier()
        image = np.zeros((128, 128, 3), dtype=np.uint8)
        features = clf.extract_color_features(image)
        assert features is not None
        assert not np.isnan(features).any()
        assert features[8] == 0.0  # sem bordas em imagem preta
        assert features[9] == 0.0  # sem contornos
        assert features[10] == 0.0  # circularity = 0 quando sem contornos
        assert features[11] == 0.0  # area_ratio = 0 quando sem contornos


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

    def test_sat_high_pred_positivo_com_margem_baixa_rejeita(self, classifier: ImageClassifier):
        """Mesmo com sat alta, margem baixa não deve aceitar tampinha."""
        classifier.model.predict.return_value = [1]
        classifier.model.decision_function.return_value = [0.20]
        image = create_image_with_saturation(180)
        pred, conf, _, method = classifier.classify_image(image)
        assert pred == 0
        assert conf == 0.90
        assert method == "SAT_HIGH"

    def test_sat_high_com_svm_rejeitando_nao_forca_tampinha(self, classifier: ImageClassifier):
        """Saturação alta não deve forçar aceitação quando SVM rejeita."""
        classifier.model.predict.return_value = [0]
        image = create_image_with_saturation(180)
        pred, conf, _, method = classifier.classify_image(image)
        assert pred == 0
        assert conf == 0.90
        assert method == "SAT_HIGH"

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

    def test_mid_high_sat_svm_rejeita_nao_aceita(self, classifier: ImageClassifier):
        """100 < sat ≤ 120, SVM pred=0 deve rejeitar para evitar falso positivo."""
        classifier.model.predict.return_value = [0]
        image = create_image_with_saturation(110)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 0
        assert method == "ACCEPT_MID_SAT"
        assert conf == 0.70

    def test_mid_high_sat_pred_positivo_com_margem_baixa_rejeita(self, classifier: ImageClassifier):
        """Predição positiva com margem baixa deve cair na zona de incerteza (rejeitar)."""
        classifier.model.predict.return_value = [1]
        classifier.model.decision_function.return_value = [0.05]
        image = create_image_with_saturation(110)
        pred, _, _, method = classifier.classify_image(image)
        assert pred == 0
        assert method == "ACCEPT_MID_SAT"

    def test_mid_high_sat_pred_positivo_com_margem_calibrada_aceita(self, classifier: ImageClassifier):
        """Predição positiva com margem acima do mínimo calibrado deve aceitar."""
        classifier.model.predict.return_value = [1]
        classifier.model.decision_function.return_value = [0.7]
        image = create_image_with_saturation(110)
        pred, _, _, method = classifier.classify_image(image)
        assert pred == 1
        assert method == "MID_HIGH_SAT"

    # ── NORMAL_SAT_TAMPINHA ───────────────────────────────────────────────

    def test_normal_sat_tampinha(self, classifier: ImageClassifier):
        """50 ≤ sat ≤ 100 → NORMAL_SAT_TAMPINHA, confiança = 0.80."""
        image = create_image_with_saturation(75)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert conf == 0.80
        assert method == "NORMAL_SAT_TAMPINHA"

    def test_normal_sat_svm_rejeita(self, classifier: ImageClassifier):
        """50 ≤ sat ≤ 100 com SVM=0 deve rejeitar."""
        classifier.model.predict.return_value = [0]
        image = create_image_with_saturation(75)
        pred, conf, _, method = classifier.classify_image(image)
        assert pred == 0
        assert conf == 0.80
        assert method == "NORMAL_SAT_TAMPINHA"

    def test_normal_sat_svm_aceita_com_margem_calibrada(self, classifier: ImageClassifier):
        """50 ≤ sat ≤ 100 com margem acima do mínimo calibrado deve aceitar."""
        classifier.model.predict.return_value = [1]
        classifier.model.decision_function.return_value = [0.8]
        image = create_image_with_saturation(75)
        pred, _, _, method = classifier.classify_image(image)
        assert pred == 1
        assert method == "NORMAL_SAT_TAMPINHA"

    # ── LOW_SAT_FORCE_TAMPINHA ────────────────────────────────────────────

    def test_low_sat_force_tampinha(self, classifier: ImageClassifier):
        """30 ≤ sat < 50 → LOW_SAT_FORCE_TAMPINHA, confiança = 0.75."""
        image = create_image_with_saturation(40)
        pred, conf, sat, method = classifier.classify_image(image)
        assert pred == 1
        assert conf == 0.75
        assert method == "LOW_SAT_FORCE_TAMPINHA"

    def test_low_sat_com_svm_rejeita_nao_forca_aceite(self, classifier: ImageClassifier):
        """30 ≤ sat < 50 com SVM=0 deve rejeitar (sem aceitação forçada)."""
        classifier.model.predict.return_value = [0]
        image = create_image_with_saturation(40)
        pred, conf, _, method = classifier.classify_image(image)
        assert pred == 0
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


class TestImageClassifierErrorPaths:
    """Cobertura de caminhos de erro/fallback do classificador."""

    def test_load_classifier_retorna_none_quando_arquivos_nao_existem(self, monkeypatch):
        """Sem arquivos de modelo/scaler, deve manter atributos None."""
        clf = ImageClassifier()
        monkeypatch.setattr('src.modules.image.MODEL_PATH', Path('/tmp/arquivo_inexistente_model.pkl'))
        monkeypatch.setattr('src.modules.image.SCALER_PATH', Path('/tmp/arquivo_inexistente_scaler.pkl'))

        clf.load_classifier()

        assert clf.model is None
        assert clf.scaler is None

    def test_load_classifier_trata_excecao_do_joblib(self, monkeypatch, tmp_path):
        """Exceção no joblib.load deve ser tratada sem crash."""
        model_file = tmp_path / 'model.pkl'
        scaler_file = tmp_path / 'scaler.pkl'
        model_file.write_bytes(b'x')
        scaler_file.write_bytes(b'y')

        clf = ImageClassifier()
        monkeypatch.setattr('src.modules.image.MODEL_PATH', model_file)
        monkeypatch.setattr('src.modules.image.SCALER_PATH', scaler_file)
        monkeypatch.setattr('src.modules.image.joblib.load', lambda _: (_ for _ in ()).throw(RuntimeError('erro')))

        clf.load_classifier()

        assert clf.model is None
        assert clf.scaler is None

    def test_load_classifier_sucesso_define_model_e_scaler(self, monkeypatch, tmp_path):
        """Quando arquivos existem e load funciona, atributos devem ser preenchidos."""
        model_file = tmp_path / 'model_ok.pkl'
        scaler_file = tmp_path / 'scaler_ok.pkl'
        model_file.write_bytes(b'model')
        scaler_file.write_bytes(b'scaler')

        fake_model = MagicMock(name='fake_model')
        fake_scaler = MagicMock(name='fake_scaler')

        def fake_load(path: str):
            if str(model_file) in path:
                return fake_model
            return fake_scaler

        clf = ImageClassifier()
        monkeypatch.setattr('src.modules.image.MODEL_PATH', model_file)
        monkeypatch.setattr('src.modules.image.SCALER_PATH', scaler_file)
        monkeypatch.setattr('src.modules.image.joblib.load', fake_load)

        clf.load_classifier()

        assert clf.model is fake_model
        assert clf.scaler is fake_scaler

    def test_extract_features_converte_dtype_para_uint8(self):
        """Imagem float32 válida deve ser convertida para uint8 e processada."""
        clf = ImageClassifier()
        image = create_image_with_saturation(80).astype(np.float32)

        features = clf.extract_color_features(image)

        assert features is not None
        assert features.shape == (12,)

    def test_extract_features_trata_excecao_interna(self, monkeypatch):
        """Erro interno em cv2.resize deve retornar None."""
        clf = ImageClassifier()
        image = create_image_with_saturation(90)
        monkeypatch.setattr('src.modules.image.cv2.resize', lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError('falha')))

        result = clf.extract_color_features(image)

        assert result is None

    def test_classify_image_trata_features_nan(self):
        """Features com NaN devem gerar retorno de erro padronizado."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        clf.scaler = MagicMock()
        clf.extract_color_features = MagicMock(return_value=np.array([np.nan] * 12))

        pred, conf, sat, method = clf.classify_image(create_image_with_saturation(100))

        assert pred is None
        assert conf is None
        assert sat is None
        assert method == "ERRO"

    def test_classify_image_trata_excecao_no_fluxo(self):
        """Exceção no scaler/model deve retornar erro sem propagar."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        clf.scaler = MagicMock()
        clf.scaler.transform.side_effect = RuntimeError('falha scaler')

        pred, conf, sat, method = clf.classify_image(create_image_with_saturation(110))

        assert pred is None
        assert conf is None
        assert sat is None
        assert method == "ERRO"
