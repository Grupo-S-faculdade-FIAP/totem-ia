"""
Testes das rotas Flask — /api/health e /api/classify.

Cobre:
    health check, classify (sucesso, rejeição, sem imagem,
    sem JSON, erro do classificador, timestamp presente)
"""
import pytest
import base64
import numpy as np
import cv2
from unittest.mock import MagicMock, patch

from app import app


# =============================================================================
# HELPERS
# =============================================================================

def create_test_image_b64(saturation: int = 150, size: int = 64) -> str:
    """Cria imagem BGR codificada em base64 com saturação HSV específica."""
    hsv = np.zeros((size, size, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = saturation
    hsv[:, :, 2] = 200
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    _, buffer = cv2.imencode('.jpg', bgr)
    return base64.b64encode(buffer).decode('utf-8')


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Flask test client com TESTING=True."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# =============================================================================
# TestHealthCheck
# =============================================================================

class TestHealthCheck:
    def test_retorna_200(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_retorna_json_com_status(self, client):
        response = client.get('/api/health')
        data = response.get_json()
        assert data is not None
        assert 'status' in data


# =============================================================================
# TestApiClassify — validação de input
# =============================================================================

class TestApiClassifyInput:
    def test_sem_corpo_retorna_400(self, client):
        """Requisição sem campo 'image' deve retornar 400."""
        response = client.post('/api/classify', json={})
        assert response.status_code == 400

    def test_content_type_invalido_retorna_400(self, client):
        """Envio sem JSON e sem file deve retornar 400."""
        response = client.post(
            '/api/classify',
            data='texto_puro',
            content_type='text/plain'
        )
        assert response.status_code == 400

    def test_imagem_base64_corrompida_retorna_400(self, client):
        """Base64 inválido deve retornar 400 ou 500 (nunca travar)."""
        response = client.post('/api/classify', json={'image': 'nao_eh_base64!!!'})
        assert response.status_code in (400, 500)


# =============================================================================
# TestApiClassify — fluxo de classificação
# =============================================================================

class TestApiClassifyFlow:
    def test_tampinha_aceita_retorna_sucesso(self, client):
        """Classificador retornando tampinha → status='sucesso', is_tampinha=True."""
        image_b64 = create_test_image_b64(saturation=180)
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.95, 180.0, "SAT_HIGH")
            response = client.post('/api/classify', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'sucesso'
        assert data['is_tampinha'] is True

    def test_nao_tampinha_retorna_rejeitado(self, client):
        """Classificador retornando não-tampinha → status='rejeitado', is_tampinha=False."""
        image_b64 = create_test_image_b64(saturation=5)
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.95, 5.0, "SAT_VERY_LOW")
            response = client.post('/api/classify', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejeitado'
        assert data['is_tampinha'] is False

    def test_classificador_com_erro_retorna_500(self, client):
        """Classificador retornando pred=None → 500."""
        image_b64 = create_test_image_b64()
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (None, None, None, "ERRO")
            response = client.post('/api/classify', json={'image': image_b64})
        assert response.status_code == 500

    def test_resposta_sempre_contem_timestamp(self, client):
        """Toda resposta de classify deve incluir campo timestamp."""
        image_b64 = create_test_image_b64()
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.90, 130.0, "SAT_HIGH")
            response = client.post('/api/classify', json={'image': image_b64})
        data = response.get_json()
        assert data is not None
        assert 'timestamp' in data

    def test_resposta_tampinha_contem_campos_esperados(self, client):
        """Resposta de tampinha aceita deve incluir classification, confidence, method."""
        image_b64 = create_test_image_b64(saturation=180)
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.95, 180.0, "SAT_HIGH")
            response = client.post('/api/classify', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })
        data = response.get_json()
        for campo in ('status', 'is_tampinha', 'classification', 'confidence', 'method', 'timestamp'):
            assert campo in data, f"Campo '{campo}' ausente na resposta"

    def test_base64_sem_prefixo_data_uri(self, client):
        """Imagem base64 sem prefixo 'data:...' também deve ser aceita."""
        image_b64 = create_test_image_b64(saturation=150)
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.85, 150.0, "NORMAL_SAT_TAMPINHA")
            response = client.post('/api/classify', json={'image': image_b64})
        assert response.status_code == 200
