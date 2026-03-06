"""
Testes unitários para src/models_trainers/svm_8features_trainer.py.

Cobre:
    - _crop_to_roi_center (ROI alinhado com image.py)
    - extract_features (8 cor + 324 HOG = 332 features)
    - generate_synthetic_negative_features
    - load_positive_features / load_negative_features
    - train_and_save (pipeline completo)
    - Paridade ROI entre trainer e image.py
"""
from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.unit
from pathlib import Path
from unittest.mock import patch

import cv2
import joblib
import numpy as np
import pytest

from src.models_trainers import svm_8features_trainer as trainer


# =============================================================================
# HELPERS
# =============================================================================

def _create_bgr_image(h: int, w: int, saturation: int = 100) -> np.ndarray:
    """Cria imagem BGR válida para extração de features."""
    hsv = np.zeros((h, w, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = saturation
    hsv[:, :, 2] = 200
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


# =============================================================================
# Test_crop_to_roi_center
# =============================================================================

class TestCropToRoiCenter:
    """Testes para _crop_to_roi_center — paridade com image.py."""

    def test_roi_retorna_centro_75_porcento(self):
        """Com USE_ROI=true, deve extrair região central 75% do menor lado."""
        with patch.dict(os.environ, {"USE_ROI": "true"}):
            trainer.USE_ROI = True
            img = _create_bgr_image(100, 100)
            result = trainer._crop_to_roi_center(img)
            expected_size = int(100 * 0.75)  # 75
            assert result.shape[0] == expected_size
            assert result.shape[1] == expected_size
            assert result.shape[2] == 3

    def test_roi_imagem_retangular_usa_menor_lado(self):
        """Imagem 80x120: ROI deve ser 60x60 (75% de 80)."""
        with patch.dict(os.environ, {"USE_ROI": "true"}):
            trainer.USE_ROI = True
            img = _create_bgr_image(80, 120)
            result = trainer._crop_to_roi_center(img)
            expected = int(80 * 0.75)  # 60
            assert result.shape[0] == expected
            assert result.shape[1] == expected

    def test_roi_use_false_retorna_imagem_original(self):
        """Com USE_ROI=false, deve retornar imagem sem crop."""
        with patch.dict(os.environ, {"USE_ROI": "false"}):
            trainer.USE_ROI = False
            img = _create_bgr_image(100, 100)
            result = trainer._crop_to_roi_center(img)
            np.testing.assert_array_equal(result, img)

    def test_roi_imagem_pequena_nao_corta(self):
        """Imagem com min(h,w)*0.75 < 32 deve retornar original."""
        with patch.dict(os.environ, {"USE_ROI": "true"}):
            trainer.USE_ROI = True
            img = _create_bgr_image(40, 40)  # 40*0.75=30 < 32
            result = trainer._crop_to_roi_center(img)
            assert result.shape == img.shape


# =============================================================================
# Test_extract_features
# =============================================================================

class TestExtractFeatures:
    """Testes para extract_features (8 cor + HOG = 332)."""

    def test_retorna_332_features(self):
        """extract_features deve retornar vetor de 332 dimensões."""
        img = _create_bgr_image(128, 128)
        features = trainer.extract_features(img)
        assert features is not None
        assert features.shape == (332,)
        assert features.dtype == np.float64

    def test_imagem_none_retorna_none(self):
        """Entrada None deve retornar None."""
        assert trainer.extract_features(None) is None

    def test_nao_ndarray_retorna_none(self):
        """Entrada que não é ndarray deve retornar None."""
        assert trainer.extract_features("string") is None  # type: ignore
        assert trainer.extract_features([1, 2, 3]) is None  # type: ignore

    def test_imagem_grayscale_retorna_none(self):
        """Imagem 2D (grayscale) deve retornar None."""
        gray = np.zeros((64, 64), dtype=np.uint8)
        assert trainer.extract_features(gray) is None

    def test_imagem_rgba_retorna_none(self):
        """Imagem com 4 canais deve retornar None."""
        rgba = np.zeros((64, 64, 4), dtype=np.uint8)
        assert trainer.extract_features(rgba) is None

    def test_sem_nan(self):
        """Features não devem conter NaN."""
        img = _create_bgr_image(128, 128)
        features = trainer.extract_features(img)
        assert features is not None
        assert not np.isnan(features).any()

    def test_primeiras_8_sao_cor(self):
        """Índices 0-7 devem ser features de cor (BGR, HSV-sat, contraste)."""
        img = _create_bgr_image(128, 128, saturation=150)
        features = trainer.extract_features(img)
        assert features is not None
        # B, G em 0-255; sat 0-255; std grayscale finito
        assert 0 <= features[6] <= 255  # saturação
        assert np.isfinite(features[7])  # contraste

    def test_features_deterministicas(self):
        """Mesma imagem deve produzir mesmo vetor."""
        img = _create_bgr_image(128, 128)
        f1 = trainer.extract_features(img)
        f2 = trainer.extract_features(img)
        assert f1 is not None and f2 is not None
        np.testing.assert_array_almost_equal(f1, f2)

    def test_converte_dtype_para_uint8(self):
        """Imagem float32 deve ser convertida e processada."""
        img = _create_bgr_image(128, 128).astype(np.float32)
        features = trainer.extract_features(img)
        assert features is not None
        assert features.shape == (332,)


# =============================================================================
# Test_generate_synthetic_negative_features
# =============================================================================

class TestGenerateSyntheticNegativeFeatures:
    """Testes para generate_synthetic_negative_features."""

    def test_retorna_lista_com_shape_correto(self):
        """Deve retornar lista de vetores 332 features."""
        negatives = trainer.generate_synthetic_negative_features(10)
        assert len(negatives) == 10
        for feat in negatives:
            assert feat.shape == (332,)
            assert feat.dtype == np.float64
            assert not np.isnan(feat).any()

    def test_reproducibilidade_com_seed(self):
        """Com seed fixo, deve ser reproduzível."""
        n1 = trainer.generate_synthetic_negative_features(5)
        n2 = trainer.generate_synthetic_negative_features(5)
        for a, b in zip(n1, n2):
            np.testing.assert_array_almost_equal(a, b)


# =============================================================================
# Test_load_positive_features / load_negative_features
# =============================================================================

class TestLoadFeatures:
    """Testes para load_positive_features e load_negative_features."""

    def test_load_positive_pasta_inexistente_ignora(self):
        """Pasta inexistente deve ser ignorada (não quebrar)."""
        with patch.object(trainer, "POSITIVE_DIRS", [Path("/caminho/inexistente/xyz")]):
            result = trainer.load_positive_features()
        assert result == []

    def test_load_positive_pasta_vazia_retorna_lista_vazia(self, tmp_path):
        """Pasta sem imagens válidas retorna lista vazia."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with patch.object(trainer, "POSITIVE_DIRS", [empty_dir]):
            result = trainer.load_positive_features()
        assert result == []

    def test_load_positive_com_imagens_reais(self, tmp_path):
        """Pasta com imagens válidas retorna features."""
        pos_dir = tmp_path / "positive"
        pos_dir.mkdir()
        for i in range(3):
            img = _create_bgr_image(128, 128)
            cv2.imwrite(str(pos_dir / f"img_{i}.jpg"), img)
        with patch.object(trainer, "POSITIVE_DIRS", [pos_dir]):
            result = trainer.load_positive_features()
        assert len(result) == 3
        assert all(f.shape == (332,) for f in result)

    def test_load_negative_pasta_inexistente_ignora(self):
        """Pasta negativa inexistente deve ser ignorada."""
        with patch.object(trainer, "NEGATIVE_DIRS", [Path("/caminho/inexistente/neg")]):
            result = trainer.load_negative_features()
        assert result == []

    def test_load_negative_com_imagens_reais(self, tmp_path):
        """Pasta com imagens negativas retorna features."""
        neg_dir = tmp_path / "negative"
        neg_dir.mkdir()
        for i in range(2):
            img = _create_bgr_image(128, 128, saturation=20)
            cv2.imwrite(str(neg_dir / f"neg_{i}.jpg"), img)
        with patch.object(trainer, "NEGATIVE_DIRS", [neg_dir]):
            result = trainer.load_negative_features()
        assert len(result) == 2
        assert all(f.shape == (332,) for f in result)


# =============================================================================
# Test_train_and_save
# =============================================================================

class TestTrainAndSave:
    """Testes para train_and_save."""

    def test_train_and_save_cria_artefatos(self, tmp_path):
        """train_and_save deve criar modelo e scaler .pkl."""
        with patch.object(trainer, "MODEL_PATH", tmp_path / "svm_model.pkl"):
            with patch.object(trainer, "SCALER_PATH", tmp_path / "scaler.pkl"):
                with patch.object(trainer, "load_positive_features") as mock_pos:
                    with patch.object(trainer, "load_negative_features") as mock_neg:
                        mock_pos.return_value = [trainer.extract_features(_create_bgr_image(128, 128)) for _ in range(20)]
                        mock_neg.return_value = [trainer.extract_features(_create_bgr_image(128, 128, saturation=30)) for _ in range(20)]
                        mock_pos.return_value = [f for f in mock_pos.return_value if f is not None]
                        mock_neg.return_value = [f for f in mock_neg.return_value if f is not None]
                        trainer.train_and_save()
        assert (tmp_path / "svm_model.pkl").exists()
        assert (tmp_path / "scaler.pkl").exists()

    def test_modelo_salvo_tem_332_features(self, tmp_path):
        """Modelo salvo deve esperar 332 features."""
        with patch.object(trainer, "MODEL_PATH", tmp_path / "svm_model.pkl"):
            with patch.object(trainer, "SCALER_PATH", tmp_path / "scaler.pkl"):
                with patch.object(trainer, "load_positive_features") as mock_pos:
                    with patch.object(trainer, "load_negative_features") as mock_neg:
                        feats = [trainer.extract_features(_create_bgr_image(128, 128)) for _ in range(15)]
                        mock_pos.return_value = [f for f in feats if f is not None]
                        mock_neg.return_value = [trainer.extract_features(_create_bgr_image(128, 128, saturation=25)) for _ in range(15)]
                        mock_neg.return_value = [f for f in mock_neg.return_value if f is not None]
                        trainer.train_and_save()
        model = joblib.load(tmp_path / "svm_model.pkl")
        scaler = joblib.load(tmp_path / "scaler.pkl")
        assert getattr(model, "n_features_in_", None) == 332
        assert getattr(scaler, "n_features_in_", None) == 332

    def test_sem_positivos_levanta_runtime_error(self):
        """Sem dados positivos deve levantar RuntimeError."""
        with patch.object(trainer, "load_positive_features", return_value=[]):
            with patch.object(trainer, "load_negative_features", return_value=[np.zeros(332)]):
                with pytest.raises(RuntimeError, match="Nenhum dado positivo"):
                    trainer.train_and_save()

    def test_sem_negativos_levanta_runtime_error(self):
        """Sem dados negativos reais e sem USE_SYNTHETIC deve levantar RuntimeError."""
        with patch.object(trainer, "load_positive_features") as mock_pos:
            with patch.object(trainer, "load_negative_features", return_value=[]):
                mock_pos.return_value = [np.zeros(332) for _ in range(5)]
                with patch.dict(os.environ, {"USE_SYNTHETIC_NEGATIVES": "0"}):
                    with pytest.raises(RuntimeError, match="Nenhum dado negativo"):
                        trainer.train_and_save()


# =============================================================================
# Test_paridade_ROI_trainer_image
# =============================================================================

class TestParidadeRoiTrainerImage:
    """Paridade de ROI entre trainer e image.py."""

    def test_roi_ratio_igual_em_trainer_e_image(self):
        """ROI_CENTER_RATIO deve ser 0.75 em ambos."""
        from src.modules import image as img_module
        assert trainer.ROI_CENTER_RATIO == img_module.ROI_CENTER_RATIO == 0.75

    def test_crop_produz_mesmo_resultado(self):
        """Trainer e ImageClassifier devem produzir mesmo crop para mesma imagem."""
        from src.modules.image import ImageClassifier
        img = _create_bgr_image(100, 100)
        with patch.dict(os.environ, {"USE_ROI": "true"}):
            trainer.USE_ROI = True
            trainer_crop = trainer._crop_to_roi_center(img)
        clf = ImageClassifier()
        clf_crop = clf._crop_to_roi_center(img)
        np.testing.assert_array_equal(trainer_crop, clf_crop)


# =============================================================================
# Test_HOG_constants
# =============================================================================

class TestHogConstants:
    """Constantes HOG alinhadas entre trainer e image.py."""

    def test_hog_params_paridade(self):
        """HOG orientations, pixels_per_cell, cells_per_block devem ser iguais."""
        from src.modules import image as img_module
        assert trainer.HOG_ORIENTATIONS == 9
        assert trainer.HOG_PIXELS_PER_CELL == (16, 16)
        assert trainer.HOG_CELLS_PER_BLOCK == (2, 2)
        assert trainer.HOG_SIZE == (64, 64)
        assert img_module.HOG_ORIENTATIONS == trainer.HOG_ORIENTATIONS
        assert img_module.HOG_PIXELS_PER_CELL == trainer.HOG_PIXELS_PER_CELL
        assert img_module.HOG_CELLS_PER_BLOCK == trainer.HOG_CELLS_PER_BLOCK
        assert img_module.HOG_SIZE == trainer.HOG_SIZE
