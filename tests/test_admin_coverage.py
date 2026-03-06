"""
Testes de cobertura completa para as rotas de administrador.
Foca em autenticação, autorização, validação de dados e tratamento de erros.
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as flask_client:
        yield flask_client


class TestAdminPageRoutes:
    """Testes das rotas de apresentação (HTML) do admin."""

    def test_admin_login_page_retorna_200(self, client):
        """GET /admin/login deve retornar página HTML."""
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_admin_index_page_retorna_200(self, client):
        """GET /admin é alias para /admin/login."""
        response = client.get('/admin')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_admin_dashboard_page_retorna_200(self, client):
        """GET /admin/dashboard deve retornar página HTML."""
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_admin_pages_passam_parametro_versao(self, client):
        """Verificar que páginas recebem parâmetro v=1 do template."""
        with patch('app.render_template') as mock_render:
            mock_render.return_value = '<html></html>'
            
            client.get('/admin/login')
            mock_render.assert_called()
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs.get('v') == 1


class TestApiAdminLogin:
    """Testes da rota POST /api/admin/login."""

    def test_login_sucesso_com_credenciais_corretas(self, client):
        """Login bem-sucedido com username e password corretos."""
        with patch.dict(os.environ, {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123',
            'ADMIN_TOKEN': 'token_secreto'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['token'] == 'token_secreto'
        assert 'message' in data

    def test_login_falha_com_username_incorreto(self, client):
        """Rejeita credenciais com username errado."""
        with patch.dict(os.environ, {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'wronguser',
                'password': 'admin123'
            })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'senha' in data.get('message', '').lower() or 'inválido' in data.get('message', '').lower()

    def test_login_falha_com_password_incorreto(self, client):
        """Rejeita credenciais com password errado."""
        with patch.dict(os.environ, {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'wrongpassword'
            })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_login_falha_sem_username(self, client):
        """Retorna 400 quando username está faltando."""
        response = client.post('/api/admin/login', json={
            'password': 'admin123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'obrigatório' in data.get('message', '').lower()

    def test_login_falha_sem_password(self, client):
        """Retorna 400 quando password está faltando."""
        response = client.post('/api/admin/login', json={
            'username': 'admin'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_falha_com_username_vazio(self, client):
        """Retorna 400 quando username é string vazia."""
        response = client.post('/api/admin/login', json={
            'username': '   ',
            'password': 'admin123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_falha_com_password_vazio(self, client):
        """Retorna 400 quando password é string vazia."""
        response = client.post('/api/admin/login', json={
            'username': 'admin',
            'password': '   '
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_sem_json_retorna_500(self, client):
        """Erro 500 quando body não é JSON válido."""
        response = client.post('/api/admin/login', 
                              data='not json',
                              content_type='text/plain')
        
        assert response.status_code == 500

    def test_login_json_vazio_retorna_400(self, client):
        """Erro 400 quando JSON é vazio {}."""
        response = client.post('/api/admin/login', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_usa_variaveis_ambiente_customizadas(self, client):
        """Verifica se credenciais são lidas do environment."""
        with patch.dict(os.environ, {
            'ADMIN_USERNAME': 'custom_admin',
            'ADMIN_PASSWORD': 'custom_pass',
            'ADMIN_TOKEN': 'custom_token'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'custom_admin',
                'password': 'custom_pass'
            })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['token'] == 'custom_token'

    def test_login_usa_valores_padrao_quando_env_nao_definidos(self, client):
        """Usa valores padrão se variáveis de ambiente não estão definidas."""
        # Remove variáveis do ambiente
        with patch.dict(os.environ, {}, clear=False):
            for var in ['ADMIN_USERNAME', 'ADMIN_PASSWORD', 'ADMIN_TOKEN']:
                os.environ.pop(var, None)
            
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestApiAdminDashboard:
    """Testes da rota GET /api/admin/dashboard."""

    def test_dashboard_retorna_200_quando_autenticado(self, client):
        """Dashboard retorna dados quando token é válido."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'stats' in data
        assert 'trend' in data
        assert 'deposits' in data

    def test_dashboard_retorna_401_sem_autenticacao(self, client):
        """Dashboard retorna 401 quando não autenticado."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/dashboard')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'erro'
        assert 'não autorizado' in data.get('error', '').lower()

    def test_dashboard_retorna_401_sem_header_authorization(self, client):
        """Rejeita quando Authorization header está faltando."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/dashboard')
        
        assert response.status_code == 401

    def test_dashboard_retorna_500_em_erro_interno(self, client):
        """Retorna 500 quando ocorre exceção interna."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=Exception('DB error')):
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer token'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_dashboard_valida_estrutura_stats(self, client):
        """Verifica se stats contém campos obrigatórios."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 5
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        stats = data['stats']
        assert stats['total'] == 5
        assert stats['aceitas'] >= 0
        assert stats['rejeitadas'] >= 0
        assert 'impacto' in stats
        assert 'changeTotal' in stats
        assert 'changeTaxa' in stats

    def test_dashboard_calcula_impacto_corretamente(self, client):
        """Verifica cálculo do impacto (kg reciclado)."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            # 2 depósitos de 1000g cada = 2kg, impacto = 2kg * 0.002 = 0.004
            mock_db.get_all_deposits.return_value = [
                {'weight_value': 1000},
                {'weight_value': 1000},
            ]
            mock_db.get_total_interacoes.return_value = 2
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        assert data['stats']['impacto'] == 0.004

    def test_dashboard_limita_depositos_aos_10_ultimos(self, client):
        """Retorna apenas os 10 últimos depósitos."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            # 15 depósitos, mas deve retornar apenas 10
            deposits = [{'id': i} for i in range(15)]
            mock_db.get_all_deposits.return_value = deposits
            mock_db.get_total_interacoes.return_value = 15
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        assert len(data['deposits']) == 10

    def test_dashboard_trend_tem_7_dias(self, client):
        """Verifica que trend contém dados de 7 dias."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        trend = data['trend']
        assert len(trend['labels']) == 7
        assert len(trend['values']) == 7

    def test_dashboard_retorna_dados_estruturados(self, client):
        """Resposta contém dados bem estruturados (stats, trend, deposits)."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        assert 'success' in data
        assert 'stats' in data
        assert 'trend' in data
        assert 'deposits' in data


class TestApiAdminAnalyticsReport:
    """Testes da rota GET /api/admin/analytics-report."""

    def test_analytics_retorna_200_quando_autenticado(self, client):
        """Analytics retorna dados quando token é válido."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_all_interactions.return_value = []
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data.get('timestamp') is not None
        assert 'report' in data

    def test_analytics_retorna_401_sem_autenticacao(self, client):
        """Analytics retorna 401 quando não autenticado."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/analytics-report')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'erro'
        assert 'não autorizado' in data.get('error', '').lower()

    def test_analytics_retorna_500_em_erro_interno(self, client):
        """Retorna 500 quando ocorre exceção interna."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=Exception('DB error')):
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer token'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'erro'

    def test_analytics_valida_estrutura_report(self, client):
        """Verifica se report contém campos obrigatórios."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_all_interactions.return_value = []
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report')
        
        data = response.get_json()
        report = data['report']
        assert 'kpis' in report
        assert 'generated_at' in report

    def test_analytics_calcula_kpis_corretamente(self, client):
        """Verifica se KPIs são calculados corretamente."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = [
                {'ml_confidence': 0.9, 'weight_value': 1000},
                {'ml_confidence': 0.8, 'weight_value': 2000},
            ]
            mock_db.get_all_interactions.return_value = [
                {'resultado': 'sucesso'},
                {'resultado': 'sucesso'},
                {'resultado': 'rejeitado'},
            ]
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report')
        
        data = response.get_json()
        kpis = data['report']['kpis']
        assert kpis['total_interactions'] == 3
        assert kpis['accepted_deposits'] == 2
        assert kpis['acceptance_rate_percent'] > 0


class TestAdminAuthenticationHelper:
    """Testes da função is_admin_authenticated."""

    def test_is_admin_authenticated_com_token_valido(self):
        """Autentica com Bearer token válido."""
        from src.modules.sprint3_analytics import is_admin_authenticated
        
        assert is_admin_authenticated('Bearer secret_token', 'secret_token') is True

    def test_is_admin_authenticated_rejeita_sem_bearer(self):
        """Rejeita se estiver faltando prefixo Bearer."""
        from src.modules.sprint3_analytics import is_admin_authenticated
        
        assert is_admin_authenticated('secret_token', 'secret_token') is False

    def test_is_admin_authenticated_rejeita_token_errado(self):
        """Rejeita quando token não combina."""
        from src.modules.sprint3_analytics import is_admin_authenticated
        
        assert is_admin_authenticated('Bearer wrong_token', 'secret_token') is False

    def test_is_admin_authenticated_rejeita_header_vazio(self):
        """Rejeita quando header está vazio."""
        from src.modules.sprint3_analytics import is_admin_authenticated
        
        assert is_admin_authenticated('', 'secret_token') is False

    def test_is_admin_authenticated_case_sensitive_token(self):
        """Token é case-sensitive."""
        from src.modules.sprint3_analytics import is_admin_authenticated
        
        assert is_admin_authenticated('Bearer SecretToken', 'secret_token') is False


class TestAdminSecurityHeaders:
    """Testes de segurança nas respostas do admin."""

    def test_login_response_nao_expoe_detalhes_internos(self, client):
        """Resposta de login não expõe stack trace ou detalhes internos."""
        response = client.post('/api/admin/login', json={
            'username': 'wrong',
            'password': 'wrong'
        })
        
        data = response.get_json()
        response_str = json.dumps(data)
        assert 'traceback' not in response_str.lower()
        assert 'exception' not in response_str.lower()

    def test_dashboard_timestamp_no_erro_em_iso_format(self, client):
        """Timestamp (quando presente no erro) está em formato ISO."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/dashboard')
        
        data = response.get_json()
        timestamp = data.get('timestamp')
        # Tenta fazer parse de ISO format
        assert timestamp is not None
        assert 'T' in timestamp  # ISO format has T

    def test_password_nao_retorna_resposta(self, client):
        """Senha não é retornada em nenhuma resposta."""
        response = client.post('/api/admin/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        data = response.get_json()
        response_str = json.dumps(data)
        assert 'admin123' not in response_str
        assert 'password' not in response_str.lower() or 'obrigatório' in response_str.lower()
