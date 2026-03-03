"""
Configuração global de fixtures para pytest.

Fixtures reutilizáveis em todos os testes.
"""
import pytest
import numpy as np
import cv2
from pathlib import Path


@pytest.fixture
def sample_image() -> np.ndarray:
    """Imagem BGR padrão (128x128, saturação média)."""
    hsv = np.zeros((128, 128, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90  # Hue
    hsv[:, :, 1] = 100  # Saturação média
    hsv[:, :, 2] = 200  # Value
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


@pytest.fixture
def temp_model_path(tmp_path) -> Path:
    """Caminho temporário para modelos de teste."""
    models_dir = tmp_path / "models" / "svm"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def pytest_configure(config):
    """Registra markers customizados."""
    config.addinivalue_line(
        "markers",
        "unit: Testes unitários (classificador, DB)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Testes de integração (rotas Flask, ESP32)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Testes lentos (requerem hardware)"
    )
