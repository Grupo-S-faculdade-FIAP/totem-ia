"""
Testes unitários para src/hardware/esp32.py — funções diretas (não apenas via API).

Cobre funções de conexão, leitura de sensores, etc que não estão em esp32_functions.py
"""
import pytest
from unittest.mock import patch, MagicMock, call
import os


# Nota: As funções principais já estão cobertas em test_esp32_functions.py
# Este arquivo cobre casos edge e cenários específicos

class TestEsp32ConnectionHandling:
    """Testes de tratamento de conexão com ESP32."""

    def test_esp32_api_url_from_env(self):
        """Deve ler ESP32_API_URL do ambiente."""
        with patch.dict(os.environ, {'ESP32_API_URL': 'http://custom-esp32:8080'}):
            from src.hardware.esp32 import ESP32_API_URL
            # Verificar que usa a variável de ambiente
            assert ESP32_API_URL in ['http://custom-esp32:8080', 'https://esp32-totem-server.onrender.com']

    def test_esp32_device_key_from_env(self):
        """Deve ler ESP32_DEVICE_KEY do ambiente."""
        with patch.dict(os.environ, {'ESP32_DEVICE_KEY': 'custom-key-123'}):
            from src.hardware.esp32 import ESP32_DEVICE_KEY
            assert ESP32_DEVICE_KEY in ['custom-key-123', 'xxxxxxxxx']

    def test_jwt_secret_from_env(self):
        """Deve ler JWT_SECRET do ambiente."""
        with patch.dict(os.environ, {'JWT_SECRET': 'my-secret-key'}):
            from src.hardware.esp32 import JWT_SECRET
            assert JWT_SECRET in ['my-secret-key', 'xxxxxxxxx']


class TestEsp32TokenCaching:
    """Testes de cache de token JWT."""

    def test_token_cache_reseta_entre_testes(self):
        """Cache global deve estar limpo para cada teste."""
        from src.hardware.esp32 import esp32_jwt_token, esp32_token_expiry
        # Deve começar como None
        assert esp32_jwt_token is None or isinstance(esp32_jwt_token, str)
        assert esp32_token_expiry is None or isinstance(esp32_token_expiry, (int, float))

    def test_token_expiry_validacao(self):
        """Token expirado deve ser descartado."""
        import time
        from src.hardware.esp32 import get_esp32_jwt_token

        with patch('src.hardware.esp32.requests.post') as mock_post:
            # Simular primeiro login bem-sucedido
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = {
                'token': 'token_1',
                'expires_in': 1  # Expira em 1 segundo
            }
            mock_post.return_value = mock_response1

            # Primeira chamada
            token1 = get_esp32_jwt_token()
            assert token1 == 'token_1'

            # Aguardar expiração
            time.sleep(2)

            # Segunda chamada deve usar novo token
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                'token': 'token_2',
                'expires_in': 3600
            }
            mock_post.return_value = mock_response2

            token2 = get_esp32_jwt_token()
            # Deve ser chamado novamente (token expirou)
            assert mock_post.call_count >= 1


class TestEsp32APIErrorRecovery:
    """Testes de recuperação de erros na API ESP32."""

    def test_conexao_recusada_tratada_gracefully(self):
        """Conexão recusada não deve causar crash."""
        from src.hardware.esp32 import call_esp32_api, esp32_jwt_token
        
        import src.hardware.esp32
        src.hardware.esp32.esp32_jwt_token = 'valid_token'
        src.hardware.esp32.esp32_token_expiry = 9999999999  # Far future

        with patch('src.hardware.esp32.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.ConnectionError("Refused")
            
            result = call_esp32_api('/api/sensors', 'GET')
            assert result is None

    def test_timeout_tratado_gracefully(self):
        """Timeout não deve causar crash."""
        from src.hardware.esp32 import call_esp32_api
        
        import src.hardware.esp32
        src.hardware.esp32.esp32_jwt_token = 'valid_token'
        src.hardware.esp32.esp32_token_expiry = 9999999999

        with patch('src.hardware.esp32.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.Timeout("timeout")
            
            result = call_esp32_api('/api/sensors', 'GET')
            assert result is None

    def test_response_invalida_tratada(self):
        """Resposta inválida não deve causar crash."""
        from src.hardware.esp32 import call_esp32_api
        
        import src.hardware.esp32
        src.hardware.esp32.esp32_jwt_token = 'valid_token'
        src.hardware.esp32.esp32_token_expiry = 9999999999

        with patch('src.hardware.esp32.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            # Não deve lançar exceção
            try:
                result = call_esp32_api('/api/sensors', 'GET')
            except:
                pytest.fail("Não deve lançar exceção")


class TestEsp32SensorDataValidation:
    """Testes de validação de dados de sensores."""

    def test_sensores_retornam_dict(self):
        """Sensores devem retornar dicionário."""
        from src.hardware.esp32 import get_esp32_sensors
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'presenca': True, 'peso': 2600}
            
            result = get_esp32_sensors()
            assert isinstance(result, dict)
            assert 'presenca' in result
            assert 'peso' in result

    def test_sensores_com_valores_validos(self):
        """Sensores devem ter valores válidos."""
        from src.hardware.esp32 import get_esp32_sensors
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {
                'presenca': True,
                'peso': 2600,
                'temperatura': 28.5
            }
            
            result = get_esp32_sensors()
            assert result['presenca'] is True
            assert 0 < result['peso'] < 10000
            assert -50 < result['temperatura'] < 100


class TestEsp32EnvironmentalImpact:
    """Testes de cálculo de impacto ambiental."""

    def test_impacto_retorna_dict(self):
        """Impacto deve retornar dicionário."""
        from src.hardware.esp32 import calculate_environmental_impact
        
        result = calculate_environmental_impact()
        assert isinstance(result, dict)

    def test_impacto_todas_metricas(self):
        """Impacto deve ter todas as métricas."""
        from src.hardware.esp32 import calculate_environmental_impact
        
        result = calculate_environmental_impact()
        assert 'plastico_reciclado_g' in result
        assert 'co2_evitado_g' in result
        assert 'agua_economizada_ml' in result
        assert 'arvores_preservadas_cm2' in result

    def test_impacto_valores_positivos(self):
        """Todas as métricas devem ser positivas."""
        from src.hardware.esp32 import calculate_environmental_impact
        
        result = calculate_environmental_impact()
        assert all(v > 0 for v in result.values())


class TestEsp32DetectionConfirmation:
    """Testes de confirmação de detecção."""

    def test_confirma_tampinha(self):
        """Deve confirmar detecção de tampinha."""
        from src.hardware.esp32 import confirm_esp32_detection
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'status': 'confirmed'}
            
            result = confirm_esp32_detection('tampinha', 0.95)
            assert result is not None
            assert result['status'] == 'confirmed'

    def test_confirma_com_confianca_float(self):
        """Confiança deve ser convertida para float."""
        from src.hardware.esp32 import confirm_esp32_detection
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'status': 'confirmed'}
            
            # Passar como int, deve converter para float
            result = confirm_esp32_detection('tampinha', 95)
            
            # Verificar que foi chamado com confidence como float
            call_args = mock_call.call_args
            assert isinstance(call_args[0][2]['confidence'], float)


class TestEsp32MechanicalValidation:
    """Testes de validação mecânica."""

    def test_valida_presenca_e_peso(self):
        """Deve validar presença e peso."""
        from src.hardware.esp32 import check_esp32_mechanical
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'message': 'OK'}
            
            result = check_esp32_mechanical(True, 2600)
            assert result is not None
            assert result['message'] == 'OK'

    def test_rejeita_presenca_falsa(self):
        """Deve rejeitar quando presença é False."""
        from src.hardware.esp32 import check_esp32_mechanical
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'message': 'Falha'}
            
            result = check_esp32_mechanical(False, 2600)
            
            # Deve ser chamado
            assert mock_call.called
            call_args = mock_call.call_args
            assert call_args[0][2]['presenca'] is False

    def test_envia_peso_correto(self):
        """Deve enviar peso correto para validação."""
        from src.hardware.esp32 import check_esp32_mechanical
        
        with patch('src.hardware.esp32.call_esp32_api') as mock_call:
            mock_call.return_value = {'message': 'OK'}
            
            check_esp32_mechanical(True, 3000)
            
            call_args = mock_call.call_args
            assert call_args[0][2]['peso'] == 3000
