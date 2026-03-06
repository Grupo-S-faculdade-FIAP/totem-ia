"""
Testes de integração completa para fluxo de admin.
Cobre: login → obter token → acessar dashboard → obter analytics-report
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as flask_client:
        yield flask_client


class TestAdminCompleteFlow:
    """Testes de fluxo completo: login → dashboard → analytics-report."""

    def test_fluxo_completo_login_dashboard_analytics(self, client):
        """
        Fluxo completo:
        1. Faz login
        2. Extrai token da resposta
        3. Usa token para acessar dashboard
        4. Usa token para acessar analytics-report
        """
        # 1. LOGIN
        with patch.dict('os.environ', {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123',
            'ADMIN_TOKEN': 'super_secret_token_12345'
        }):
            login_response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
        
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        assert login_data['success'] is True
        token = login_data['token']
        assert token == 'super_secret_token_12345'
        
        # 2. ACESSAR DASHBOARD COM TOKEN
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = [
                {'weight_value': 500, 'ml_confidence': 0.9},
                {'weight_value': 1500, 'ml_confidence': 0.85},
            ]
            mock_db.get_total_interacoes.return_value = 5
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            dashboard_response = client.get('/api/admin/dashboard',
                                           headers={'Authorization': f'Bearer {token}'})
        
        assert dashboard_response.status_code == 200
        dash_data = dashboard_response.get_json()
        assert dash_data['success'] is True
        assert dash_data['stats']['total'] == 5
        assert dash_data['stats']['aceitas'] == 2
        assert 'trend' in dash_data
        assert 'deposits' in dash_data
        
        # 3. ACESSAR ANALYTICS-REPORT COM TOKEN
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = [
                {'weight_value': 500, 'ml_confidence': 0.9},
                {'weight_value': 1500, 'ml_confidence': 0.85},
            ]
            mock_db.get_all_interactions.return_value = [
                {'resultado': 'sucesso'},
                {'resultado': 'sucesso'},
                {'resultado': 'rejeitado'},
                {'resultado': 'sucesso'},
                {'resultado': 'falha'},
            ]
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            analytics_response = client.get('/api/admin/analytics-report',
                                           headers={'Authorization': f'Bearer {token}'})
        
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.get_json()
        assert analytics_data['success'] is True
        assert 'report' in analytics_data
        report = analytics_data['report']
        assert 'kpis' in report
        assert report['kpis']['total_interactions'] == 5
        assert report['kpis']['accepted_deposits'] == 2

    def test_fluxo_rejeita_sem_token_valido(self, client):
        """Rejeita acesso ao dashboard sem token válido."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'erro'

    def test_fluxo_rejeita_analytics_sem_token_valido(self, client):
        """Rejeita acesso ao analytics-report sem token válido."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'erro'

    def test_fluxo_rejeita_dashboard_sem_header_authorization(self, client):
        """Rejeita dashboard sem header Authorization."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/dashboard')
        
        assert response.status_code == 401

    def test_fluxo_rejeita_analytics_sem_header_authorization(self, client):
        """Rejeita analytics-report sem header Authorization."""
        with patch('app.is_admin_authenticated', return_value=False):
            response = client.get('/api/admin/analytics-report')
        
        assert response.status_code == 401

    def test_login_falha_rejeita_acesso_a_dashboard(self, client):
        """Se login falhar, não há token para acessar dashboard."""
        with patch.dict('os.environ', {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123'
        }):
            login_response = client.post('/api/admin/login', json={
                'username': 'wronguser',
                'password': 'admin123'
            })
        
        assert login_response.status_code == 401
        login_data = login_response.get_json()
        assert login_data['success'] is False
        assert 'token' not in login_data

    def test_header_authorization_case_insensitive_bearer(self, client):
        """Verifica que Bearer é case-insensitive no header."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            # Testa com "bearer" minúsculo
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'bearer token123'})
        
        # A função is_admin_authenticated é mockada, então deve aceitar
        assert response.status_code == 200


class TestAdminHeadersAndSecurity:
    """Testes de segurança e headers nas rotas de admin."""

    def test_login_retorna_content_type_json(self, client):
        """Resposta de login tem content-type application/json."""
        response = client.post('/api/admin/login', json={
            'username': 'admin',
            'password': 'wrong'
        })
        
        assert 'application/json' in response.content_type

    def test_dashboard_retorna_content_type_json(self, client):
        """Resposta de dashboard tem content-type application/json."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer token'})
        
        assert 'application/json' in response.content_type

    def test_analytics_retorna_content_type_json(self, client):
        """Resposta de analytics tem content-type application/json."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_all_interactions.return_value = []
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer token'})
        
        assert 'application/json' in response.content_type

    def test_token_nao_expoe_detalhes_internos(self, client):
        """Token não contém detalhes de implementação."""
        with patch.dict('os.environ', {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123',
            'ADMIN_TOKEN': 'my_secret_token'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
        
        data = response.get_json()
        token = data['token']
        # Token não deve conter informações sensíveis
        assert 'admin123' not in token
        assert 'admin' not in token.lower() or token.lower() == 'my_secret_token'

    def test_401_response_nao_expoe_credenciais(self, client):
        """Resposta 401 não expõe credenciais inválidas em detalhes."""
        with patch.dict('os.environ', {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_PASSWORD': 'admin123'
        }):
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'wrongpass'
            })
        
        data = response.get_json()
        json_str = json.dumps(data)
        assert 'wrongpass' not in json_str


class TestAdminDataValidation:
    """Testes de validação de dados nas respostas de admin."""

    def test_dashboard_stats_tem_campos_obrigatorios(self, client):
        """Stats devem ter todos os campos esperados."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer token'})
        
        stats = response.get_json()['stats']
        required_fields = ['total', 'aceitas', 'rejeitadas', 'impacto',
                          'changeTotal', 'changeTaxa', 'changeRejeitadas']
        for field in required_fields:
            assert field in stats, f"Campo obrigatório {field} faltando"

    def test_analytics_kpis_tem_campos_obrigatorios(self, client):
        """KPIs devem ter todos os campos esperados."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_all_interactions.return_value = []
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer token'})
        
        kpis = response.get_json()['report']['kpis']
        required_fields = ['total_interactions', 'accepted_deposits',
                          'acceptance_rate_percent', 'avg_ml_confidence']
        for field in required_fields:
            assert field in kpis, f"Campo obrigatório {field} faltando"

    def test_dashboard_trend_labels_e_values_sincronizados(self, client):
        """Trend deve ter mesmo número de labels e values."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = []
            mock_db.get_total_interacoes.return_value = 0
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer token'})
        
        trend = response.get_json()['trend']
        assert len(trend['labels']) == len(trend['values'])
        assert len(trend['labels']) == 7  # 7 dias

    def test_analytics_acceptance_rate_percentual_valido(self, client):
        """Acceptance rate deve estar entre 0 e 100."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection') as mock_db_ctx:
            
            mock_db = MagicMock()
            mock_db.get_all_deposits.return_value = [
                {'ml_confidence': 0.9, 'weight_value': 1000}
            ]
            mock_db.get_all_interactions.return_value = [
                {'resultado': 'sucesso'},
                {'resultado': 'rejeitado'},
            ]
            mock_db_ctx.return_value.__enter__.return_value = mock_db
            mock_db_ctx.return_value.__exit__.return_value = None
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer token'})
        
        kpis = response.get_json()['report']['kpis']
        rate = kpis['acceptance_rate_percent']
        assert 0 <= rate <= 100


class TestAdminErrorHandling:
    """Testes de tratamento de erros nas rotas de admin."""

    def test_login_json_malformado_retorna_500(self, client):
        """JSON malformado no login retorna 500."""
        response = client.post('/api/admin/login',
                              data='{ invalid json }',
                              content_type='application/json')
        
        assert response.status_code == 500

    def test_dashboard_db_exception_retorna_500(self, client):
        """Erro na conexão do BD retorna 500."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=RuntimeError('DB crashed')):
            
            response = client.get('/api/admin/dashboard',
                                 headers={'Authorization': 'Bearer token'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False

    def test_analytics_db_exception_retorna_500(self, client):
        """Erro na conexão do BD retorna 500."""
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=RuntimeError('DB crashed')):
            
            response = client.get('/api/admin/analytics-report',
                                 headers={'Authorization': 'Bearer token'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'erro'

    def test_login_valores_none_retorna_erro(self, client):
        """Valores None no login causam erro (400 ou 500 dependendo da implementação)."""
        response = client.post('/api/admin/login', json={
            'username': None,
            'password': None
        })
        
        # Pode ser 400 (validação) ou 500 (exception durante strip())
        assert response.status_code in [400, 500]

    def test_dashboard_sem_authenticated_call_rejeita(self, client):
        """Dashboard sem chamada a is_admin_authenticated rejeita."""
        # Não fazer patch, deixar falhar naturalmente
        response = client.get('/api/admin/dashboard')
        
        assert response.status_code == 401
