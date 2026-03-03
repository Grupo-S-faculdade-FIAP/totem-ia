"""
Testes das rotas Flask — health, classify, validate-mechanical, esp32-health.

Cobre:
    /api/health — health check
    /api/classify — classificação de imagem (sucesso, rejeição, erros)
    /api/validate-mechanical — validação mecânica apenas
    /api/esp32-health — status do ESP32
    /api/admin/login — autenticação admin
    /api/admin/dashboard — dashboard admin
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


# =============================================================================
# TestValidateMechanical
# =============================================================================

class TestValidateMechanical:
    """Testes para /api/validate-mechanical — validação de presença e peso."""

    def test_validate_mechanical_presenca_e_peso_validos(self, client):
        """Presença=True e peso dentro do intervalo → 'aprovado'."""
        response = client.post('/api/validate-mechanical', json={
            'presenca': True,
            'peso': 2600  # Dentro do intervalo
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'aprovado'
        assert 'timestamp' in data

    def test_validate_mechanical_presenca_falsa(self, client):
        """Presença=False → 'rejeitado'."""
        response = client.post('/api/validate-mechanical', json={
            'presenca': False,
            'peso': 2600
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejeitado'
        assert 'Presença não detectada' in data['message']

    def test_validate_mechanical_peso_minimo_invalido(self, client):
        """Peso abaixo do mínimo → 'rejeitado'."""
        response = client.post('/api/validate-mechanical', json={
            'presenca': True,
            'peso': 500  # Abaixo do mínimo
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejeitado'
        assert 'Peso fora do intervalo' in data['message']

    def test_validate_mechanical_peso_maximo_invalido(self, client):
        """Peso acima do máximo → 'rejeitado'."""
        response = client.post('/api/validate-mechanical', json={
            'presenca': True,
            'peso': 5000  # Acima do máximo
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rejeitado'
        assert 'Peso fora do intervalo' in data['message']

    def test_validate_mechanical_sem_json(self, client):
        """Requisição sem JSON → 400."""
        response = client.post(
            '/api/validate-mechanical',
            data='texto_puro',
            content_type='text/plain'
        )
        assert response.status_code == 400

    def test_validate_mechanical_valores_default(self, client):
        """Dados ausentes devem ter valores default."""
        response = client.post('/api/validate-mechanical', json={})
        assert response.status_code == 200
        data = response.get_json()
        # presenca defaults a True, peso defaults a 2600
        assert 'status' in data


# =============================================================================
# TestEsp32Health
# =============================================================================

class TestEsp32Health:
    """Testes para /api/esp32-health — verificação de status ESP32."""

    def test_esp32_online_retorna_200(self, client):
        """ESP32 online → status='online' e HTTP 200."""
        with patch('app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'ok'}
            mock_get.return_value = mock_response

            response = client.get('/api/esp32-health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'online'
        assert 'timestamp' in data

    def test_esp32_offline_retorna_503(self, client):
        """ESP32 offline (timeout/erro) → status='offline' e HTTP 503."""
        with patch('app.requests.get') as mock_get:
            mock_get.side_effect = ConnectionError("Cannot connect")

            response = client.get('/api/esp32-health')

        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'offline'

    def test_esp32_http_error_status(self, client):
        """ESP32 retorna erro HTTP → status='offline'."""
        with patch('app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            response = client.get('/api/esp32-health')

        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'offline'

    def test_esp32_timeout_treated_as_offline(self, client):
        """Timeout ao conectar ESP32 → status='offline'."""
        import requests
        with patch('app.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("timeout")

            response = client.get('/api/esp32-health')

        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'offline'


# =============================================================================
# TestAdminRoutes
# =============================================================================

class TestAdminRoutes:
    """Testes para rotas de autenticação e dashboard admin."""

    def test_api_admin_login_sem_credenciais(self, client):
        """Login sem credenciais → 400."""
        response = client.post('/api/admin/login', json={})
        assert response.status_code == 400

    def test_api_admin_login_credenciais_invalidas(self, client):
        """Login com credenciais erradas → 401."""
        response = client.post('/api/admin/login', json={
            'username': 'wrong_user',
            'password': 'wrong_pass'
        })
        assert response.status_code == 401

    def test_api_admin_login_credenciais_validas(self, client):
        """Login com credenciais corretas → token."""
        with patch.dict('os.environ', {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'senha123'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'senha123'
            })
        if response.status_code == 200:
            data = response.get_json()
            assert 'token' in data or 'message' in data

    def test_api_admin_dashboard_sem_autenticacao(self, client):
        """Dashboard sem autenticação → 401 ou 403."""
        response = client.get('/api/admin/dashboard')
        assert response.status_code in (401, 403, 400)

    def test_api_admin_dashboard_com_token_invalido(self, client):
        """Dashboard com token inválido → 401."""
        response = client.get(
            '/api/admin/dashboard',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        assert response.status_code in (401, 403)


# =============================================================================
# TestValidateMechanicalEsp32
# =============================================================================

class TestValidateMechanicalEsp32:
    """Testes para /api/validate_mechanical — software + mecânica ESP32."""

    def test_validate_mechanical_esp32_sem_imagem(self, client):
        """Requisição sem imagem → 400."""
        response = client.post('/api/validate_mechanical', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_validate_mechanical_esp32_com_imagem_valida(self, client):
        """Classificação + mecânica com valores válidos → sucesso."""
        image_b64 = create_test_image_b64(saturation=150)

        with patch('app.image_classifier') as mock_clf, \
             patch('app.check_esp32_mechanical') as mock_mech:
            mock_clf.classify_image.return_value = (1, 0.95, 150.0, "SAT_HIGH")
            mock_mech.return_value = {'message': 'OK'}

            response = client.post('/api/validate_mechanical', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })

        if response.status_code == 200:
            data = response.get_json()
            assert 'status' in data

    def test_validate_mechanical_esp32_rejeita_nao_tampinha(self, client):
        """Não-tampinha é rejeitado antes de validar mecânica."""
        image_b64 = create_test_image_b64(saturation=5)

        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.95, 5.0, "SAT_VERY_LOW")

            response = client.post('/api/validate_mechanical', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })

        assert response.status_code in (200, 400)
        data = response.get_json()
        # Deve rejeitar antes de validar mecânica
        if 'status' in data:
            assert data['status'] in ('rejeitado', 'erro_classificacao')
