"""
Fixtures específicas para testes na pasta tests/.
"""
import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock
from pathlib import Path

from app import app
from src.modules.image import ImageClassifier
from src.database.db import DatabaseConnection


@pytest.fixture
def flask_client():
    """Cliente Flask para testes de integração."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_classifier() -> ImageClassifier:
    """ClassificadorImageClassifier com mocks de dependências."""
    classifier = ImageClassifier()
    classifier.model = MagicMock()
    classifier.scaler = MagicMock()
    return classifier


@pytest.fixture
def test_db(tmp_path) -> DatabaseConnection:
    """Banco de dados SQLite em memória/temp para testes."""
    db_path = str(tmp_path / "test_totem.db")
    db = DatabaseConnection(db_path)
    db.init_db()
    return db


def create_image_with_saturation(saturation: int, size: int = 128) -> np.ndarray:
    """Helper: Cria imagem BGR com saturação HSV específica."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = saturation
    hsv[:, :, 2] = 200
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


@pytest.fixture
def high_saturation_image() -> np.ndarray:
    """Imagem com saturação alta (>120) → deve classificar como tampinha."""
    return create_image_with_saturation(150)


@pytest.fixture
def low_saturation_image() -> np.ndarray:
    """Imagem com saturação baixa (<30) → não tampinha."""
    return create_image_with_saturation(20)


@pytest.fixture
def mid_saturation_image() -> np.ndarray:
    """Imagem com saturação média (50-100) → depende de SVM."""
    return create_image_with_saturation(75)
