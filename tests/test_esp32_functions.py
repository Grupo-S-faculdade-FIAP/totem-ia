"""
Testes unitários para src/hardware/esp32.py — funções de API e autenticação.

Cobre:
    get_esp32_jwt_token(), call_esp32_api(), get_esp32_sensors(),
    confirm_esp32_detection(), check_esp32_mechanical(),
    calculate_environmental_impact()
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.hardware import esp32


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_esp32_globals():
    """Reseta estado global do módulo esp32 antes de cada teste."""
    esp32.esp32_jwt_token = None
    esp32.esp32_token_expiry = None
    yield
    esp32.esp32_jwt_token = None
    esp32.esp32_token_expiry = None


@pytest.fixture
def mock_requests_post():
    """Mock para requests.post."""
    with patch('src.hardware.esp32.requests.post') as mock:
        yield mock


@pytest.fixture
def mock_requests_get():
    """Mock para requests.get."""
    with patch('src.hardware.esp32.requests.get') as mock:
        yield mock


# =============================================================================
# TestGetEsp32JwtToken
# =============================================================================

class TestGetEsp32JwtToken:
    """Testes para get_esp32_jwt_token()."""

    def test_get_token_success(self, mock_requests_post):
        """Deve retornar token JWT quando login é bem-sucedido (200)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'test_token_abc123xyz',
            'expires_in': 3600
        }
        mock_requests_post.return_value = mock_response

        # Act
        token = esp32.get_esp32_jwt_token()

        # Assert
        assert token == 'test_token_abc123xyz'
        assert esp32.esp32_jwt_token == 'test_token_abc123xyz'
        assert esp32.esp32_token_expiry is not None
        mock_requests_post.assert_called_once()

    def test_get_token_caches_valid_token(self, mock_requests_post):
        """Deve reutilizar token em cache se ainda válido."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'first_token',
            'expires_in': 3600
        }
        mock_requests_post.return_value = mock_response

        # Act
        token1 = esp32.get_esp32_jwt_token()
        token2 = esp32.get_esp32_jwt_token()  # Segunda chamada

        # Assert
        assert token1 == token2 == 'first_token'
        assert mock_requests_post.call_count == 1  # Apenas uma chamada HTTP

    def test_get_token_login_failure(self, mock_requests_post):
        """Deve retornar None quando login falha (não 200)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_post.return_value = mock_response

        # Act
        token = esp32.get_esp32_jwt_token()

        # Assert
        assert token is None
        assert esp32.esp32_jwt_token is None

    def test_get_token_connection_error(self, mock_requests_post):
        """Deve retornar None quando há erro de conexão."""
        # Arrange
        mock_requests_post.side_effect = ConnectionError("Cannot connect to ESP32")

        # Act
        token = esp32.get_esp32_jwt_token()

        # Assert
        assert token is None

    def test_get_token_timeout(self, mock_requests_post):
        """Deve retornar None quando há timeout na requisição."""
        # Arrange
        import requests
        mock_requests_post.side_effect = requests.exceptions.Timeout("Request timeout")

        # Act
        token = esp32.get_esp32_jwt_token()

        # Assert
        assert token is None


# =============================================================================
# TestCallEsp32Api
# =============================================================================

class TestCallEsp32Api:
    """Testes para call_esp32_api()."""

    def test_call_esp32_api_get_success(self, mock_requests_post, mock_requests_get):
        """Deve fazer GET request com autenticação JWT."""
        # Arrange
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'response'}
        mock_requests_get.return_value = mock_response

        # Act
        result = esp32.call_esp32_api('/api/test', method='GET')

        # Assert
        assert result == {'data': 'response'}
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert 'Authorization' in call_args.kwargs['headers']
        assert call_args.kwargs['headers']['Authorization'] == 'Bearer valid_token'

    def test_call_esp32_api_post_success(self, mock_requests_post, mock_requests_get):
        """Deve fazer POST request com dados e autenticação JWT."""
        # Arrange
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'status': 'created'}
        mock_requests_post.return_value = mock_response

        # Act
        result = esp32.call_esp32_api(
            '/api/confirm',
            method='POST',
            data={'detection': 'tampinha'}
        )

        # Assert
        assert result == {'status': 'created'}
        mock_requests_post.assert_called_once()

    def test_call_esp32_api_no_token(self, mock_requests_get):
        """Deve retornar None se não conseguir token JWT."""
        # Arrange
        esp32.esp32_jwt_token = None

        # Act
        with patch.object(esp32, 'get_esp32_jwt_token', return_value=None):
            result = esp32.call_esp32_api('/api/test')

        # Assert
        assert result is None
        mock_requests_get.assert_not_called()

    def test_call_esp32_api_invalid_method(self):
        """Deve retornar None para método HTTP não suportado."""
        # Arrange
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        # Act
        result = esp32.call_esp32_api('/api/test', method='DELETE')

        # Assert
        assert result is None

    def test_call_esp32_api_http_error(self, mock_requests_get):
        """Deve retornar None quando API retorna erro HTTP."""
        # Arrange
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests_get.return_value = mock_response

        # Act
        result = esp32.call_esp32_api('/api/test')

        # Assert (fallback retorna dict vazio para endpoint desconhecido)
        assert result == {}

    def test_call_esp32_api_exception(self, mock_requests_get):
        """Deve retornar None quando há exceção na requisição."""
        # Arrange
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600
        mock_requests_get.side_effect = Exception("Network error")

        # Act
        result = esp32.call_esp32_api('/api/test')

        # Assert (fallback retorna dict vazio)
        assert result == {}

    def test_call_esp32_api_get_usa_timeout_hardcoded(self, mock_requests_get):
        """GET na API ESP32 deve usar timeout fixo."""
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_requests_get.return_value = mock_response

        esp32.call_esp32_api('/api/sensors', method='GET')

        call_args = mock_requests_get.call_args
        assert call_args.kwargs['timeout'] == 10

    def test_call_esp32_api_post_usa_timeout_hardcoded(self, mock_requests_post):
        """POST na API ESP32 deve usar timeout fixo."""
        esp32.esp32_jwt_token = 'valid_token'
        esp32.esp32_token_expiry = datetime.now().timestamp() + 3600

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_requests_post.return_value = mock_response

        esp32.call_esp32_api('/api/check_mechanical', method='POST', data={'peso': 2600, 'presenca': True})

        call_args = mock_requests_post.call_args
        assert call_args.kwargs['timeout'] == 10


# =============================================================================
# TestGetEsp32Sensors
# =============================================================================

class TestGetEsp32Sensors:
    """Testes para get_esp32_sensors()."""

    def test_get_sensors_success(self):
        """Deve retornar leitura de sensores quando disponível."""
        # Arrange
        sensor_data = {
            'presenca': True,
            'peso': 2600,
            'temperatura': 28.5
        }

        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=sensor_data):
            result = esp32.get_esp32_sensors()

        # Assert
        assert result == sensor_data
        assert result['presenca'] is True
        assert result['peso'] == 2600

    def test_get_sensors_api_failure(self):
        """Deve retornar None quando API falha."""
        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=None):
            result = esp32.get_esp32_sensors()

        # Assert
        assert result is None


# =============================================================================
# TestConfirmEsp32Detection
# =============================================================================

class TestConfirmEsp32Detection:
    """Testes para confirm_esp32_detection()."""

    def test_confirm_detection_success(self):
        """Deve enviar confirmação de detecção com sucesso."""
        # Arrange
        response_data = {'status': 'confirmed', 'id': '123'}

        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=response_data):
            result = esp32.confirm_esp32_detection('tampinha', 0.95)

        # Assert
        assert result == response_data

    def test_confirm_detection_failure(self):
        """Deve retornar None quando confirmação falha."""
        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=None):
            result = esp32.confirm_esp32_detection('tampinha', 0.95)

        # Assert
        assert result is None

    def test_confirm_detection_with_float_confidence(self):
        """Deve converter confidence para float."""
        # Arrange
        response_data = {'status': 'confirmed'}

        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=response_data) as mock_call:
            esp32.confirm_esp32_detection('tampinha', 0.95)

        # Assert
        call_args = mock_call.call_args
        data = call_args[0][2] if len(call_args[0]) > 2 else call_args.kwargs['data']
        assert isinstance(data['confidence'], float)
        assert data['confidence'] == 0.95


# =============================================================================
# TestCheckEsp32Mechanical
# =============================================================================

class TestCheckEsp32Mechanical:
    """Testes para check_esp32_mechanical()."""

    def test_check_mechanical_success(self):
        """Deve verificar condição mecânica com sucesso."""
        # Arrange
        response_data = {'message': 'Mechanical check passed'}

        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=response_data):
            result = esp32.check_esp32_mechanical(True, 2600)

        # Assert
        assert result == response_data

    def test_check_mechanical_failure(self):
        """Deve retornar None quando verificação falha."""
        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=None):
            result = esp32.check_esp32_mechanical(True, 2600)

        # Assert
        assert result is None

    def test_check_mechanical_with_different_values(self):
        """Deve aceitar diferentes valores de presença e peso."""
        # Arrange
        response_data = {'message': 'OK'}

        # Act
        with patch.object(esp32, 'call_esp32_api', return_value=response_data) as mock_call:
            esp32.check_esp32_mechanical(False, 1500)

        # Assert
        call_args = mock_call.call_args
        data = call_args[0][2] if len(call_args[0]) > 2 else call_args.kwargs['data']
        assert data['presenca'] is False
        assert data['peso'] == 1500


# =============================================================================
# TestCalculateEnvironmentalImpact
# =============================================================================

class TestCalculateEnvironmentalImpact:
    """Testes para calculate_environmental_impact()."""

    def test_calculate_impact_returns_dict(self):
        """Deve retornar dicionário com métricas de impacto."""
        # Act
        result = esp32.calculate_environmental_impact()

        # Assert
        assert isinstance(result, dict)
        assert 'plastico_reciclado_g' in result
        assert 'co2_evitado_g' in result
        assert 'agua_economizada_ml' in result
        assert 'arvores_preservadas_cm2' in result

    def test_calculate_impact_values_are_positive(self):
        """Todas as métricas devem ser números positivos."""
        # Act
        result = esp32.calculate_environmental_impact()

        # Assert
        for key, value in result.items():
            assert isinstance(value, (int, float))
            assert value > 0

    def test_calculate_impact_consistent(self):
        """Deve retornar sempre os mesmos valores."""
        # Act
        result1 = esp32.calculate_environmental_impact()
        result2 = esp32.calculate_environmental_impact()

        # Assert
        assert result1 == result2

    def test_calculate_impact_expected_values(self):
        """Deve retornar valores esperados (constantes)."""
        # Act
        result = esp32.calculate_environmental_impact()

        # Assert
        assert result['plastico_reciclado_g'] == 0.5
        assert result['co2_evitado_g'] == 2.3
        assert result['agua_economizada_ml'] == 15
        assert result['arvores_preservadas_cm2'] == 8


class TestEsp32EnvHelpers:
    """Testes para helpers internos de ambiente."""

    def test_get_esp32_api_url_usa_env(self):
        """Helper de URL deve priorizar ESP32_API_URL do ambiente."""
        with patch.dict('os.environ', {'ESP32_API_URL': 'http://esp32-local:5001'}):
            assert esp32._get_esp32_api_url() == 'http://esp32-local:5001'

    def test_get_esp32_device_key_usa_env(self):
        """Helper de credencial deve priorizar ESP32_DEVICE_KEY do ambiente."""
        with patch.dict('os.environ', {'ESP32_DEVICE_KEY': 'device-key-abc'}):
            assert esp32._get_esp32_device_key() == 'device-key-abc'


class TestEsp32TimeoutConfig:
    """Testes para garantir timeouts fixos (hardcoded)."""

    def test_get_esp32_jwt_token_usa_timeout_30(self, mock_requests_post):
        """Login JWT deve usar timeout fixo de 30s."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'abc', 'expires_in': 3600}
        mock_requests_post.return_value = mock_response

        token = esp32.get_esp32_jwt_token()

        assert token == 'abc'
        call_args = mock_requests_post.call_args
        assert call_args.kwargs['timeout'] == 30
