"""
Tests to cover missing branches in src/hardware/esp32.py

Missing lines: 120-121 (ConnectTimeout), 123-124 (ReadTimeout),
153 (non-bool presenca), 160-161 (invalid peso), 166-168 (peso out of range),
170-171 (invalid temp), 176-177 (temp out of range), 179-180 (temp out of range),
194 (validated is None in get_esp32_sensors)
"""
import pytest
import requests
from unittest.mock import patch, MagicMock

from src.hardware import esp32
from src.hardware.esp32 import (
    _validate_sensors_response,
    _get_fallback_response,
    get_esp32_sensors,
    call_esp32_api,
)


@pytest.fixture(autouse=True)
def reset_esp32_globals():
    """Reset JWT token state before and after each test."""
    esp32.esp32_jwt_token = None
    esp32.esp32_token_expiry = None
    yield
    esp32.esp32_jwt_token = None
    esp32.esp32_token_expiry = None


@pytest.fixture
def jwt_ready():
    """Pre-configure a valid cached JWT token."""
    esp32.esp32_jwt_token = "test_jwt_token_abc123"
    esp32.esp32_token_expiry = 9_999_999_999  # far future


# =============================================================================
# call_esp32_api — non-200/201 status (lines 116-118 equivalent by coverage)
# =============================================================================

class TestCallEsp32ApiNon200Status:
    """Covers the else: branch when status code is not 200/201."""

    def test_non_200_status_known_endpoint_returns_fallback(self, jwt_ready):
        """API returns 400 → falls through to _get_fallback_response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"

        with patch("src.hardware.esp32.requests.get", return_value=mock_resp):
            result = call_esp32_api("/api/sensors", "GET")

        # Should return the fallback for /api/sensors
        assert result is not None
        assert "presenca" in result

    def test_non_201_status_unknown_endpoint_returns_empty(self, jwt_ready):
        """API returns 500 for unknown endpoint → empty fallback {}."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("src.hardware.esp32.requests.get", return_value=mock_resp):
            result = call_esp32_api("/api/unknown_endpoint", "GET")

        assert result == {}

    def test_status_201_is_success(self, jwt_ready):
        """Status 201 is in [200, 201] → returns json directly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"status": "created"}

        with patch("src.hardware.esp32.requests.post", return_value=mock_resp):
            result = call_esp32_api("/api/sensors", "POST", {"data": 1})

        assert result == {"status": "created"}


# =============================================================================
# call_esp32_api — ConnectTimeout (lines 120-121)
# =============================================================================

class TestCallEsp32ApiConnectTimeout:
    """Covers lines 120-121: ConnectTimeout exception handler."""

    def test_connect_timeout_returns_fallback(self, jwt_ready):
        """Lines 120-121: ConnectTimeout → fallback response."""
        with patch(
            "src.hardware.esp32.requests.get",
            side_effect=requests.exceptions.ConnectTimeout(),
        ):
            result = call_esp32_api("/api/sensors", "GET")

        assert isinstance(result, dict)
        assert "presenca" in result

    def test_connect_timeout_unknown_endpoint(self, jwt_ready):
        """ConnectTimeout on unknown endpoint → empty dict {}."""
        with patch(
            "src.hardware.esp32.requests.get",
            side_effect=requests.exceptions.ConnectTimeout(),
        ):
            result = call_esp32_api("/api/nonexistent", "GET")

        assert result == {}


# =============================================================================
# call_esp32_api — ReadTimeout (lines 123-124)
# =============================================================================

class TestCallEsp32ApiReadTimeout:
    """Covers lines 123-124: ReadTimeout exception handler."""

    def test_read_timeout_returns_fallback(self, jwt_ready):
        """Lines 123-124: ReadTimeout → fallback response."""
        with patch(
            "src.hardware.esp32.requests.get",
            side_effect=requests.exceptions.ReadTimeout(),
        ):
            result = call_esp32_api("/api/sensors", "GET")

        assert isinstance(result, dict)
        assert "presenca" in result

    def test_read_timeout_check_mechanical_endpoint(self, jwt_ready):
        """ReadTimeout on check_mechanical endpoint → fallback."""
        with patch(
            "src.hardware.esp32.requests.post",
            side_effect=requests.exceptions.ReadTimeout(),
        ):
            result = call_esp32_api("/api/check_mechanical", "POST", {})

        assert result is not None
        assert "status" in result


# =============================================================================
# _validate_sensors_response — presenca not bool (line 153)
# =============================================================================

class TestValidateSensorsResponsePresenca:
    """Covers line 153: presenca is not bool → bool(presenca)."""

    def test_presenca_as_integer_1_converts_to_true(self):
        """Line 153: presenca = 1 (int) → converts to True."""
        data = {"presenca": 1, "peso": 2600, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["presenca"] is True

    def test_presenca_as_integer_0_converts_to_false(self):
        """Line 153: presenca = 0 (int) → converts to False."""
        data = {"presenca": 0, "peso": 2600, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["presenca"] is False

    def test_presenca_as_string_true_converts(self):
        """Line 153: presenca = 'yes' (truthy string) → True."""
        data = {"presenca": "yes", "peso": 2600, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["presenca"] is True

    def test_presenca_as_none_defaults_to_true(self):
        """Line 153: presenca = None → defaults to True."""
        data = {"presenca": None, "peso": 2600, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["presenca"] is True


# =============================================================================
# _validate_sensors_response — peso invalid type (lines 160-161)
# =============================================================================

class TestValidateSensorsResponsePesoInvalid:
    """Covers lines 160-161: peso TypeError/ValueError → fallback 2600."""

    def test_peso_non_numeric_string_uses_fallback(self):
        """Lines 160-161: peso = 'invalid' → TypeError/ValueError → 2600."""
        data = {"presenca": True, "peso": "invalid_peso", "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 2600

    def test_peso_as_list_uses_fallback(self):
        """Lines 160-161: peso = [1,2] (list) → TypeError → 2600."""
        data = {"presenca": True, "peso": [1, 2, 3], "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 2600

    def test_peso_as_dict_uses_fallback(self):
        """Lines 160-161: peso = {} → float({}) raises TypeError → 2600."""
        data = {"presenca": True, "peso": {}, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 2600


# =============================================================================
# _validate_sensors_response — peso out of range (lines 166-168)
# =============================================================================

class TestValidateSensorsResponsePesoOutOfRange:
    """Covers lines 166-168: peso outside [PESO_MIN_VALIDO, PESO_MAX_VALIDO]."""

    def test_peso_negative_out_of_range(self):
        """Lines 166-168: peso = -500 < PESO_MIN_VALIDO (0) → 2600."""
        data = {"presenca": True, "peso": -500, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 2600

    def test_peso_too_large_out_of_range(self):
        """Lines 166-168: peso = 99999 > PESO_MAX_VALIDO (10000) → 2600."""
        data = {"presenca": True, "peso": 99999, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 2600

    def test_peso_just_at_max_valid(self):
        """Boundary: peso = 10000 (max valid) → keeps value."""
        data = {"presenca": True, "peso": 10000, "temperatura": 25.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["peso"] == 10000


# =============================================================================
# _validate_sensors_response — temperatura invalid type (lines 170-171)
# =============================================================================

class TestValidateSensorsResponseTempInvalid:
    """Covers lines 170-171: temperatura TypeError/ValueError → fallback 25.0."""

    def test_temp_non_numeric_string_uses_fallback(self):
        """Lines 170-171: temperatura = 'hot' → ValueError → 25.0."""
        data = {"presenca": True, "peso": 2600, "temperatura": "hot"}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == 25.0

    def test_temp_as_list_uses_fallback(self):
        """Lines 170-171: temperatura = [25, 26] → TypeError → 25.0."""
        data = {"presenca": True, "peso": 2600, "temperatura": [25, 26]}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == 25.0


# =============================================================================
# _validate_sensors_response — temperatura out of range (lines 176-177, 179-180)
# =============================================================================

class TestValidateSensorsResponseTempOutOfRange:
    """Covers lines 176-177, 179-180: temp outside [-20, 80]."""

    def test_temp_below_minimum(self):
        """Lines 176-177, 179-180: temperatura = -100 < TEMP_MIN_VALIDO (-20) → 25.0."""
        data = {"presenca": True, "peso": 2600, "temperatura": -100.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == 25.0

    def test_temp_above_maximum(self):
        """Lines 176-177, 179-180: temperatura = 200 > TEMP_MAX_VALIDO (80) → 25.0."""
        data = {"presenca": True, "peso": 2600, "temperatura": 200.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == 25.0

    def test_temp_just_at_max_valid(self):
        """Boundary: temperatura = 80 (max valid) → keeps value."""
        data = {"presenca": True, "peso": 2600, "temperatura": 80.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == 80.0

    def test_temp_just_at_min_valid(self):
        """Boundary: temperatura = -20 (min valid) → keeps value."""
        data = {"presenca": True, "peso": 2600, "temperatura": -20.0}
        result = _validate_sensors_response(data)
        assert result is not None
        assert result["temperatura"] == -20.0


# =============================================================================
# _validate_sensors_response — None / non-dict input
# =============================================================================

class TestValidateSensorsResponseEdgeCases:
    """Covers edge cases in _validate_sensors_response."""

    def test_none_input_returns_none(self):
        """None input → returns None."""
        assert _validate_sensors_response(None) is None

    def test_empty_dict_returns_none(self):
        """Empty dict → not data (falsy) → returns None."""
        assert _validate_sensors_response({}) is None  # type: ignore

    def test_non_dict_list_returns_none(self):
        """List input → not dict → returns None."""
        assert _validate_sensors_response([1, 2, 3]) is None  # type: ignore


# =============================================================================
# get_esp32_sensors — validated is None (line 194)
# =============================================================================

class TestGetEsp32SensorsValidatedNone:
    """Covers line 194: _validate_sensors_response returns None → fallback."""

    @patch("src.hardware.esp32._validate_sensors_response")
    @patch("src.hardware.esp32.call_esp32_api")
    def test_validated_none_returns_fallback(self, mock_call_api, mock_validate):
        """Line 194: validated=None → return _get_fallback_response('/api/sensors')."""
        mock_call_api.return_value = {"presenca": True, "peso": 2600, "temperatura": 25.0}
        mock_validate.return_value = None  # validator says data is invalid

        result = get_esp32_sensors()

        # Should return the fallback for /api/sensors
        assert result is not None
        assert "presenca" in result
        assert result == _get_fallback_response("/api/sensors")

    @patch("src.hardware.esp32.call_esp32_api")
    def test_call_api_returns_none_get_sensors_returns_none(self, mock_call_api):
        """get_esp32_sensors when call_esp32_api returns None → returns None."""
        mock_call_api.return_value = None

        result = get_esp32_sensors()

        assert result is None
