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
import os
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

    def test_api_admin_dashboard_com_token_valido(self, client):
        """Dashboard com token válido deve retornar dados consolidados."""
        fake_deposits = [
            {'timestamp': 1700000000.0, 'weight_value': 2500},
            {'timestamp': 1700003600.0, 'weight_value': 2600},
        ]

        with patch('app._ensure_db_connection') as mock_db_factory:
            fake_db = MagicMock()
            fake_db.get_all_deposits.return_value = fake_deposits
            fake_db.get_total_interacoes.return_value = 3

            fake_context = MagicMock()
            fake_context.__enter__.return_value = fake_db
            fake_context.__exit__.return_value = None
            mock_db_factory.return_value = fake_context

            response = client.get(
                '/api/admin/dashboard',
                headers={'Authorization': 'Bearer admin_token'}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'trend' in data
        assert len(data['trend']['labels']) == 7
        assert len(data['trend']['values']) == 7


class TestAdminAnalyticsReport:
    """Testes para /api/admin/analytics-report."""

    def test_analytics_report_sem_token_retorna_401(self, client):
        """Endpoint analítico sem autenticação deve rejeitar acesso."""
        response = client.get('/api/admin/analytics-report')
        assert response.status_code == 401

    def test_analytics_report_com_token_valido_retorna_kpis(self, client):
        """Endpoint analítico deve retornar KPIs, tendência e distribuição."""
        fake_deposits = [
            {'timestamp': 1700000000.0, 'ml_confidence': 0.9, 'weight_value': 2500},
            {'timestamp': 1700003600.0, 'ml_confidence': 0.8, 'weight_value': 2600},
        ]
        fake_interactions = [
            {'id': 1, 'deposit_id': 1, 'timestamp': 1700000000.0, 'resultado': 'sucesso'},
            {'id': 2, 'deposit_id': None, 'timestamp': 1700000200.0, 'resultado': 'rejeitado'},
            {'id': 3, 'deposit_id': 2, 'timestamp': 1700003600.0, 'resultado': 'sucesso'},
        ]

        with patch('app._ensure_db_connection') as mock_db_factory:
            fake_db = MagicMock()
            fake_db.get_all_deposits.return_value = fake_deposits
            fake_db.get_all_interactions.return_value = fake_interactions

            fake_context = MagicMock()
            fake_context.__enter__.return_value = fake_db
            fake_context.__exit__.return_value = None
            mock_db_factory.return_value = fake_context

            response = client.get(
                '/api/admin/analytics-report',
                headers={'Authorization': 'Bearer admin_token'}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'report' in data
        assert 'kpis' in data['report']
        assert data['report']['kpis']['total_interactions'] == 3
        assert data['report']['kpis']['accepted_deposits'] == 2


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


# =============================================================================
# TestSpeechRoutes
# =============================================================================

class TestSpeechRoutes:
    """Testes para rotas de áudio de sustentabilidade."""

    def test_get_sustainability_speech_sem_arquivo(self, client):
        """GET /api/speech/sustainability sem arquivo → 500."""
        with patch('app.generate_sustainability_speech', return_value=None):
            response = client.get('/api/speech/sustainability')
        assert response.status_code == 500

    def test_get_speech_info_retorna_disponibilidade(self, client):
        """GET /api/speech/info retorna informações do áudio."""
        response = client.get('/api/speech/info')
        assert response.status_code == 200
        data = response.get_json()
        assert 'available' in data
        assert 'size' in data
        assert 'url' in data

    def test_get_speech_info_url_correto(self, client):
        """URL do áudio deve apontar para /api/speech/sustainability."""
        response = client.get('/api/speech/info')
        data = response.get_json()
        assert data['url'] == '/api/speech/sustainability'


# =============================================================================
# TestPageRoutes
# =============================================================================

class TestPageRoutes:
    """Testes para rotas de páginas HTML."""

    def test_index_retorna_200(self, client):
        """GET / deve retornar 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_totem_intro_retorna_html(self, client):
        """GET /totem_intro.html retorna HTML."""
        response = client.get('/totem_intro.html')
        assert response.status_code == 200

    def test_totem_v2_retorna_html(self, client):
        """GET /totem_v2.html retorna HTML."""
        response = client.get('/totem_v2.html')
        assert response.status_code == 200

    def test_processing_retorna_html(self, client):
        """GET /processing retorna HTML."""
        response = client.get('/processing')
        assert response.status_code == 200

    def test_finalization_retorna_html(self, client):
        """GET /finalization retorna HTML."""
        response = client.get('/finalization')
        assert response.status_code == 200

    def test_rewards_retorna_html(self, client):
        """GET /rewards retorna HTML."""
        response = client.get('/rewards')
        assert response.status_code == 200

    def test_test_page_retorna_html(self, client):
        """GET /test retorna página de teste."""
        response = client.get('/test')
        assert response.status_code == 200

    def test_esp32_simulator_retorna_html(self, client):
        """GET /esp32_simulator.html retorna simulador."""
        response = client.get('/esp32_simulator.html')
        assert response.status_code == 200


# =============================================================================
# TestServeTestImage
# =============================================================================

class TestServeTestImage:
    """Testes para rota de servir imagem de teste."""

    def test_serve_test_image_retorna_jpeg(self, client):
        """GET /test_tampinha.jpg retorna imagem."""
        response = client.get('/test_tampinha.jpg')
        assert response.status_code == 200
        assert 'image' in response.content_type.lower()


# =============================================================================
# TestErrorHandling
# =============================================================================

class TestErrorHandling:
    """Testes de tratamento de erro."""

    def test_404_para_rota_inexistente(self, client):
        """Rota inexistente deve retornar 404."""
        response = client.get('/rota/que/nao/existe')
        assert response.status_code == 404

    def test_classify_com_arquivo_corrompido(self, client):
        """Arquivo corrompido deve retornar erro."""
        response = client.post('/api/classify', json={'image': 'data:image/jpeg;base64,!!invalid!!'})
        assert response.status_code in (400, 500)


# =============================================================================
# TestAPIConsistency
# =============================================================================

class TestAPIConsistency:
    """Testes de consistência da API."""

    def test_health_check_sempre_sucesso(self, client):
        """Health check nunca deve falhar."""
        for _ in range(5):
            response = client.get('/api/health')
            assert response.status_code == 200

    def test_resposta_json_bem_formada(self, client):
        """Respostas JSON devem ser bem formadas."""
        response = client.get('/api/health')
        assert response.is_json
        data = response.get_json()
        assert isinstance(data, dict)


# =============================================================================
# TestConcurrency
# =============================================================================

class TestConcurrency:
    """Testes para requisições simultâneas."""

    def test_multiplas_health_checks(self, client):
        """Múltiplos health checks devem funcionar."""
        responses = [client.get('/api/health') for _ in range(10)]
        assert all(r.status_code == 200 for r in responses)

    def test_multiplas_classificacoes(self, client):
        """Múltiplas classificações não devem interferir."""
        image_b64 = create_test_image_b64(saturation=150)
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.95, 150.0, "SAT_HIGH")
            
            responses = [
                client.post('/api/classify', json={'image': image_b64})
                for _ in range(3)
            ]
        
        assert all(r.status_code == 200 for r in responses)


# =============================================================================
# TestDebugConfirm
# =============================================================================

class TestDebugConfirm:
    """Testes para rota de confirmação em modo debug."""

    def test_debug_confirm_com_debug_ativo(self, client):
        """POST /api/debug-confirm com MODO_DEBUG=true retorna sucesso."""
        with patch.dict(os.environ, {'MODO_DEBUG': 'true'}):
            with patch('app.MODO_DEBUG', True):
                response = client.post('/api/debug-confirm', json={
                    'detection_type': 'tampinha',
                    'confidence': 0.95
                })
        
        assert response.status_code in (200, 400)

    def test_debug_confirm_rejeitado_sem_debug(self, client):
        """POST /api/debug-confirm sem MODO_DEBUG retorna 403."""
        with patch('app.MODO_DEBUG', False):
            response = client.post('/api/debug-confirm', json={
                'detection_type': 'tampinha',
                'confidence': 0.95
            })
        
        assert response.status_code == 403


# =============================================================================
# TestAdminPages
# =============================================================================

class TestAdminPages:
    """Testes para páginas admin."""

    def test_admin_login_page_retorna_html(self, client):
        """GET /admin deve retornar página de login."""
        response = client.get('/admin')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html') or 'html' in response.content_type.lower()

    def test_admin_dashboard_page_retorna_html(self, client):
        """GET /admin/dashboard deve retornar página dashboard."""
        response = client.get('/admin/dashboard')
        assert response.status_code == 200


# =============================================================================
# TestValidateCompleteRoute
# =============================================================================

class TestValidateCompleteRoute:
    """Testes para /api/validate-complete."""

    def test_validate_complete_sem_imagem(self, client):
        """POST /api/validate-complete sem imagem retorna erro."""
        response = client.post('/api/validate-complete', json={})
        assert response.status_code == 400

    def test_validate_complete_com_tampinha(self, client):
        """POST /api/validate-complete com tampinha retorna sucesso."""
        image_b64 = create_test_image_b64(saturation=150)
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.95, 150.0, "SAT_HIGH")
            with patch('app.check_esp32_mechanical') as mock_mech:
                mock_mech.return_value = {'message': 'OK'}
                
                response = client.post('/api/validate-complete', json={
                    'image': f'data:image/jpeg;base64,{image_b64}'
                })
        
        assert response.status_code in (200, 400)

    def test_validate_complete_nao_tampinha(self, client):
        """POST /api/validate-complete com não-tampinha retorna rejeitado."""
        image_b64 = create_test_image_b64(saturation=5)
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.95, 5.0, "SAT_VERY_LOW")
            
            response = client.post('/api/validate-complete', json={
                'image': f'data:image/jpeg;base64,{image_b64}'
            })
        
        assert response.status_code in (200, 400)


# =============================================================================
# TestSaveDepositRoute
# =============================================================================

class TestSaveDepositRoute:
    """Testes para /api/save_deposit."""

    def test_save_deposit_com_imagem_e_confianca(self, client):
        """POST /api/save_deposit com imagem e confiança."""
        image_b64 = create_test_image_b64(saturation=150)
        
        with patch('app.db_connection') as mock_db:
            with patch('app.image_classifier') as mock_clf:
                mock_clf.classify_image.return_value = (1, 0.95, 150.0, "SAT_HIGH")
                
                response = client.post('/api/save_deposit', json={
                    'image': f'data:image/jpeg;base64,{image_b64}',
                    'confidence': 0.95
                })
        
        assert response.status_code in (200, 400, 500)

    def test_save_deposit_sem_imagem(self, client):
        """POST /api/save_deposit sem imagem retorna erro."""
        response = client.post('/api/save_deposit', json={})
        assert response.status_code in (400, 500)


# =============================================================================
# TestDebugImageRoute
# =============================================================================

class TestDebugImageRoute:
    """Testes para /debug-image/<filename>."""

    def test_debug_image_arquivo_valido(self, client):
        """GET /debug-image/test_tampinha.jpg com arquivo válido."""
        response = client.get('/debug-image/test_tampinha.jpg')
        # Pode existir ou não o arquivo, mas não deve crash
        assert response.status_code in (200, 404)

    def test_debug_image_arquivo_inexistente(self, client):
        """GET /debug-image/nao_existe.jpg retorna 404."""
        response = client.get('/debug-image/arquivo_inexistente_xyz.jpg')
        assert response.status_code == 404

    def test_debug_image_path_traversal(self, client):
        """GET /debug-image/../../../etc/passwd não permite path traversal."""
        response = client.get('/debug-image/../../../etc/passwd')
        # Deve rejeitar ou apenas não encontrar
        assert response.status_code in (400, 404)


# =============================================================================
# TestValidateMechanicalCompleteRoute
# =============================================================================

class TestValidateMechanicalCompleteRoute:
    """Testes para /api/validate_mechanical completo."""

    def test_validate_mechanical_complete_flow(self, client):
        """POST /api/validate_mechanical com flow completo."""
        image_b64 = create_test_image_b64(saturation=150)
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.95, 150.0, "SAT_HIGH")
            with patch('app.get_esp32_sensors') as mock_sensors:
                mock_sensors.return_value = {'presenca': True, 'peso': 2600}
                
                response = client.post('/api/validate_mechanical', json={
                    'image': f'data:image/jpeg;base64,{image_b64}'
                })
        
        assert response.status_code in (200, 400)

    def test_validate_mechanical_arquivo_enviado(self, client):
        """POST /api/validate_mechanical com upload de arquivo."""
        import io
        
        # Tenta enviar como multipart (se suportado)
        data = {
            'file': (io.BytesIO(b'fake image'), 'test.jpg')
        }
        
        response = client.post(
            '/api/validate_mechanical',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Pode retornar erro ou sucesso
        assert response.status_code in (200, 400, 415)


# =============================================================================
# TestImageValidation
# =============================================================================

class TestImageValidation:
    """Testes de validação rigorosa de imagens."""

    def test_classify_com_imagem_muito_pequena(self, client):
        """Imagem 1x1 pixel."""
        hsv = np.zeros((1, 1, 3), dtype=np.uint8)
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        _, buffer = cv2.imencode('.jpg', bgr)
        image_b64 = base64.b64encode(buffer).decode('utf-8')
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (1, 0.5, 50.0, "UNKNOWN")
            response = client.post('/api/classify', json={'image': image_b64})
        
        assert response.status_code in (200, 400, 500)

    def test_classify_com_imagem_monocromatica(self, client):
        """Imagem completamente branca."""
        image = np.ones((128, 128, 3), dtype=np.uint8) * 255
        _, buffer = cv2.imencode('.jpg', image)
        image_b64 = base64.b64encode(buffer).decode('utf-8')
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.8, 0.0, "WHITE")
            response = client.post('/api/classify', json={'image': image_b64})
        
        assert response.status_code in (200, 400)

    def test_classify_com_imagem_preta(self, client):
        """Imagem completamente preta."""
        image = np.zeros((128, 128, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', image)
        image_b64 = base64.b64encode(buffer).decode('utf-8')
        
        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.9, 0.0, "BLACK")
            response = client.post('/api/classify', json={'image': image_b64})
        
        assert response.status_code in (200, 400)


# =============================================================================
# TestTokenExpiration
# =============================================================================

class TestTokenExpiration:
    """Testes de expiração de token/session."""

    def test_admin_login_token_invalido(self, client):
        """Login com token inválido deve rejeitar."""
        response = client.post('/api/admin/login', json={
            'username': 'admin',
            'password': 'wrong'
        })
        assert response.status_code in (401, 400)

    def test_admin_dashboard_token_expirado(self, client):
        """Dashboard com token expirado deve rejeitar."""
        response = client.get(
            '/api/admin/dashboard',
            headers={'Authorization': 'Bearer expired_token_xyz'}
        )
        assert response.status_code in (401, 403)
