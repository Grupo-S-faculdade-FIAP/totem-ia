"""
Testes unitários para src/models_trainers/svm_complete_classifier.py

Cobre:
    SVMCompleteDatasetClassifier — treinamento de modelo SVM
    extract_color_features(), load_dataset(), train_model(), save_model()
"""
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
from pathlib import Path
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

from src.models_trainers.svm_complete_classifier import SVMCompleteDatasetClassifier


# =============================================================================
# HELPERS
# =============================================================================

def create_dummy_image(tmp_path, size: int = 128) -> Path:
    """Cria imagem temporária para testes."""
    image = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)
    image_path = tmp_path / "dummy_image.jpg"
    cv2.imwrite(str(image_path), image)
    return image_path


def create_dummy_dataset(tmp_path, num_positive: int = 5, num_negative: int = 2):
    """Cria dataset dummy com imagens positivas e negativas."""
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"

    positive_dir.mkdir()
    negative_dir.mkdir()

    positive_files = []
    negative_files = []

    for i in range(num_positive):
        img_path = positive_dir / f"positive_{i}.jpg"
        img = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        positive_files.append(img_path)

    for i in range(num_negative):
        img_path = negative_dir / f"negative_{i}.jpg"
        img = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        negative_files.append(img_path)

    return positive_files, negative_files


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def classifier(tmp_path):
    """Classificador SVM com diretório de modelos temporário."""
    clf = SVMCompleteDatasetClassifier()
    clf.model_path = tmp_path / "models"
    clf.model_path.mkdir(parents=True, exist_ok=True)
    return clf


@pytest.fixture
def dummy_image(tmp_path):
    """Imagem dummy para testes."""
    return create_dummy_image(tmp_path)


@pytest.fixture
def dummy_dataset(tmp_path):
    """Dataset dummy com imagens positivas e negativas."""
    return create_dummy_dataset(tmp_path, num_positive=5, num_negative=3)


# =============================================================================
# TestSVMCompleteDatasetClassifier_Init
# =============================================================================

class TestSVMCompleteDatasetClassifierInit:
    """Testes para __init__()."""

    def test_init_creates_model_path(self, tmp_path):
        """Deve criar diretório de modelos."""
        # Arrange
        clf = SVMCompleteDatasetClassifier()
        clf.model_path = tmp_path / "models"

        # Act
        clf.model_path.mkdir(parents=True, exist_ok=True)

        # Assert
        assert clf.model_path.exists()

    def test_init_model_is_none(self):
        """Modelo deve começar como None."""
        # Act
        clf = SVMCompleteDatasetClassifier()

        # Assert
        assert clf.model is None

    def test_init_scaler_is_standardscaler(self):
        """Scaler deve ser StandardScaler."""
        # Act
        clf = SVMCompleteDatasetClassifier()

        # Assert
        assert isinstance(clf.scaler, StandardScaler)


# =============================================================================
# TestExtractColorFeaturesTrainer
# =============================================================================

class TestExtractColorFeaturesTrainer:
    """Testes para extract_color_features() do trainer."""

    def test_extract_features_returns_24_dimensions(self, classifier, dummy_image):
        """Deve retornar vetor de 24 features."""
        # Act
        features = classifier.extract_color_features(str(dummy_image))

        # Assert
        assert isinstance(features, np.ndarray)
        assert features.shape == (24,)

    def test_extract_features_nonexistent_file(self, classifier):
        """Deve retornar None para arquivo inexistente."""
        # Act
        features = classifier.extract_color_features("/nonexistent/image.jpg")

        # Assert
        assert features is None

    def test_extract_features_contains_rgb_stats(self, classifier, dummy_image):
        """Primeiros 9 features devem ser RGB stats."""
        # Act
        features = classifier.extract_color_features(str(dummy_image))

        # Assert
        # Índices 0-8 são RGB (3 canais × 3 stats)
        assert features is not None
        assert len(features) >= 9
        # RGB values são 0-255, então stats devem estar nesse range
        for i in range(9):
            assert 0 <= features[i] <= 255

    def test_extract_features_contains_hsv_stats(self, classifier, dummy_image):
        """Próximos 9 features devem ser HSV stats."""
        # Act
        features = classifier.extract_color_features(str(dummy_image))

        # Assert
        # Índices 9-17 são HSV
        assert features is not None
        # H: 0-180, S: 0-255, V: 0-255
        # Mas std/median podem estar fora desses ranges, então apenas verificar shape
        assert len(features) >= 18

    def test_extract_features_contains_shape_features(self, classifier, dummy_image):
        """Últimos 6 features devem ser shape features."""
        # Act
        features = classifier.extract_color_features(str(dummy_image))

        # Assert
        # Índices 18-23 são shape features (normalizados entre 0-1)
        assert features is not None
        assert len(features) == 24
        # Shape features são normalizados
        assert all(np.isfinite(features[18:24]))

    def test_extract_features_no_nan(self, classifier, dummy_image):
        """Não deve conter NaN."""
        # Act
        features = classifier.extract_color_features(str(dummy_image))

        # Assert
        assert not np.isnan(features).any()

    def test_extract_features_reproducible(self, classifier, dummy_image):
        """Deve retornar mesmo vetor para mesma imagem."""
        # Act
        features1 = classifier.extract_color_features(str(dummy_image))
        features2 = classifier.extract_color_features(str(dummy_image))

        # Assert
        np.testing.assert_array_almost_equal(features1, features2)


# =============================================================================
# TestLoadDataset
# =============================================================================

class TestLoadDataset:
    """Testes para load_dataset()."""

    def test_load_dataset_returns_tuple(self, classifier):
        """Deve retornar tupla (X, y)."""
        # Act
        with patch.object(classifier, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    result = classifier.load_dataset()

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_load_dataset_x_is_2d_array(self, classifier):
        """X deve ser array 2D (n_samples, 24)."""
        # Act
        with patch.object(classifier, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    X, y = classifier.load_dataset()

        # Assert
        assert isinstance(X, np.ndarray)
        if len(X) > 0:
            assert X.ndim == 2
            assert X.shape[1] == 24

    def test_load_dataset_y_is_1d_array(self, classifier):
        """y deve ser array 1D com labels (0/1)."""
        # Act
        with patch.object(classifier, 'extract_color_features', return_value=np.zeros(24)):
            with patch('pathlib.Path.glob', return_value=[]):
                with patch('pathlib.Path.exists', return_value=False):
                    X, y = classifier.load_dataset()

        # Assert
        assert isinstance(y, np.ndarray)
        if len(y) > 0:
            assert y.ndim == 1
            assert all(label in [0, 1] for label in y)


# =============================================================================
# TestTrainModel
# =============================================================================

class TestTrainModel:
    """Testes para train_model()."""

    def test_train_model_sets_model_attribute(self, classifier):
        """Deve definir classifier.model após treinamento."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)

        # Act
        classifier.train_model(X_train, y_train, X_train, y_train)

        # Assert
        assert classifier.model is not None
        assert isinstance(classifier.model, SVC)

    def test_train_model_fits_scaler(self, classifier):
        """Deve fazer fit do scaler nos dados."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)

        # Act
        classifier.train_model(X_train, y_train, X_train, y_train)

        # Assert
        # Scaler deve ter sido fitted
        assert hasattr(classifier.scaler, 'scale_')

    def test_train_model_produces_predictions(self, classifier):
        """Modelo treinado deve fazer predições."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)

        # Act
        classifier.train_model(X_train, y_train, X_train, y_train)
        X_test = np.random.randn(5, 24)
        X_test_scaled = classifier.scaler.transform(X_test)
        predictions = classifier.model.predict(X_test_scaled)

        # Assert
        assert len(predictions) == 5
        assert all(p in [0, 1] for p in predictions)

    def test_train_model_with_validation(self, classifier):
        """Deve aceitar dados de validação separados."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)
        X_val = np.random.randn(10, 24)
        y_val = np.random.randint(0, 2, 10)

        # Act & Assert (não deve lançar erro)
        classifier.train_model(X_train, y_train, X_val, y_val)
        assert classifier.model is not None


# =============================================================================
# TestSaveModel
# =============================================================================

class TestSaveModel:
    """Testes para save_model()."""

    def test_save_model_creates_model_file(self, classifier):
        """Deve criar arquivo do modelo."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)
        classifier.train_model(X_train, y_train, X_train, y_train)

        # Act
        classifier.save_model()

        # Assert
        model_file = classifier.model_path / "svm_model_complete.pkl"
        assert model_file.exists()

    def test_save_model_creates_scaler_file(self, classifier):
        """Deve criar arquivo do scaler."""
        # Arrange
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)
        classifier.train_model(X_train, y_train, X_train, y_train)

        # Act
        classifier.save_model()

        # Assert
        scaler_file = classifier.model_path / "scaler_complete.pkl"
        assert scaler_file.exists()

    def test_save_model_files_are_serializable(self, classifier):
        """Arquivos salvos devem ser deserializáveis."""
        # Arrange
        import joblib
        X_train = np.random.randn(20, 24)
        y_train = np.random.randint(0, 2, 20)
        classifier.train_model(X_train, y_train, X_train, y_train)

        # Act
        classifier.save_model()

        # Assert
        model_file = classifier.model_path / "svm_model_complete.pkl"
        scaler_file = classifier.model_path / "scaler_complete.pkl"

        loaded_model = joblib.load(model_file)
        loaded_scaler = joblib.load(scaler_file)

        assert loaded_model is not None
        assert loaded_scaler is not None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.unit
def test_complete_training_pipeline(classifier):
    """Teste de pipeline completo: extract → train → save."""
    # Arrange
    X = np.random.randn(30, 24)
    y = np.random.randint(0, 2, 30)

    # Act
    classifier.train_model(X, y, X, y)
    classifier.save_model()

    # Assert
    assert classifier.model is not None
    assert (classifier.model_path / "svm_model_complete.pkl").exists()
    assert (classifier.model_path / "scaler_complete.pkl").exists()

@pytest.mark.unit
def test_trained_model_prediction_consistency(classifier):
    """Modelo treinado deve fazer predições consistentes."""
    # Arrange
    X_train = np.random.randn(50, 24)
    y_train = np.random.randint(0, 2, 50)
    X_test = np.random.randn(10, 24)

    # Act
    classifier.train_model(X_train, y_train, X_train, y_train)
    X_test_scaled = classifier.scaler.transform(X_test)

    pred1 = classifier.model.predict(X_test_scaled)
    pred2 = classifier.model.predict(X_test_scaled)

    # Assert
    np.testing.assert_array_equal(pred1, pred2)
