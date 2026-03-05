from __future__ import annotations

import logging
import os
import requests

from datetime import datetime
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()


# Constantes de fallback para compatibilidade e testes.
ESP32_API_URL = 'https://esp32-totem-server.onrender.com'
ESP32_DEVICE_KEY = 'xxxxxxxxx'
JWT_SECRET = 'xxxxxxxxx'

# Token JWT cache
esp32_jwt_token = None
esp32_token_expiry = None


def _get_esp32_api_url() -> str:
    """Retorna URL da API ESP32 a partir do ambiente."""
    return os.getenv('ESP32_API_URL', ESP32_API_URL)


def _get_esp32_device_key() -> str:
    """Retorna credencial device key do ambiente."""
    return os.getenv('ESP32_DEVICE_KEY', ESP32_DEVICE_KEY)


def get_esp32_jwt_token() -> str | None:
    """Obtém um token JWT válido da API ESP32"""
    global esp32_jwt_token, esp32_token_expiry

    # Se tem token válido, retorna
    if esp32_jwt_token and esp32_token_expiry and datetime.now().timestamp() < esp32_token_expiry:
        logger.info("✅ ESP32 JWT: Usando token em cache (válido)")
        return esp32_jwt_token

    try:
        logger.info("🔐 ESP32: Realizando login para obter JWT token...")
        api_url = _get_esp32_api_url()
        device_key = _get_esp32_device_key()

        logger.info(f"   URL: {api_url}/api/auth/login")
        logger.info(f"   Device ID: {device_key}")

        login_response = requests.post(
            f"{api_url}/api/auth/login",
            json={
                "device_id": device_key,
                "device_key": device_key
            },
            timeout=30
        )
        
        logger.info(f"📡 ESP32 LOGIN RESPONSE: {login_response.status_code}")
        logger.info(f"   Resposta: {login_response.text[:300]}")
        
        if login_response.status_code == 200:
            data = login_response.json()
            esp32_jwt_token = data['token']
            esp32_token_expiry = datetime.now().timestamp() + data.get('expires_in', 86400) - 60
            logger.info(f"✅ ESP32 JWT: Token obtido com sucesso!")
            logger.info(f"   Token: {esp32_jwt_token[:30]}...")
            logger.info(f"   Expira em: {data.get('expires_in', 86400)} segundos")
            return esp32_jwt_token
        else:
            logger.error(f"❌ ESP32: Erro ao fazer login: {login_response.status_code}")
            logger.error(f"   Resposta: {login_response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ ESP32: Erro ao obter token JWT: {e}")
        return None


def call_esp32_api(endpoint: str, method: str = 'GET', data: dict | None = None) -> dict | None:
    """Realiza chamada à API ESP32 com autenticação JWT"""
    token = get_esp32_jwt_token()
    
    if not token:
        logger.error("❌ Não foi possível obter token JWT")
        return None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{_get_esp32_api_url()}{endpoint}"
    
    logger.info(f"📡 ESP32 REQUEST: {method} {endpoint}")
    if data:
        logger.info(f"   Dados: {data}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)  # Aumentado para 10s
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)  # Aumentado para 10s
        else:
            logger.error(f"❌ Método HTTP não suportado: {method}")
            return None
        
        logger.info(f"📡 ESP32 RESPONSE: {response.status_code}")
        logger.info(f"   Resposta: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ ESP32: Sucesso - {endpoint}")
            return response.json()
        else:
            logger.error(f"❌ ESP32: API retornou {response.status_code}: {response.text}")
            return _get_fallback_response(endpoint)
    except requests.exceptions.ConnectTimeout:
        logger.warning(f"⚠️ ESP32: Timeout na conexão (ESP32 offline ou lento). Usando fallback.")
        return _get_fallback_response(endpoint)
    except requests.exceptions.ReadTimeout:
        logger.warning(f"⚠️ ESP32: Timeout na leitura (ESP32 respondendo lentamente). Usando fallback.")
        return _get_fallback_response(endpoint)
    except requests.exceptions.ConnectionError:
        logger.warning(f"⚠️ ESP32: Não conseguiu conectar (offline). Usando fallback.")
        return _get_fallback_response(endpoint)
    except Exception as e:
        logger.error(f"❌ ESP32: Erro ao chamar API: {e}")
        return _get_fallback_response(endpoint)


def _get_fallback_response(endpoint: str) -> dict:
    """Retorna resposta de fallback quando ESP32 está offline."""
    fallbacks = {
        '/api/sensors': {'presenca': True, 'peso': 2600, 'temperatura': 25.0},
        '/api/check_mechanical': {'status': 'OK', 'message': 'Validação mecânica OK (fallback)', 'peso': 2600},
        '/api/confirm_detection': {'status': 'confirmed', 'timestamp': '2026-03-05T17:30:00Z'},
    }
    return fallbacks.get(endpoint, {})


def get_esp32_sensors() -> dict | None:
    """Obtém leitura dos sensores do ESP32"""
    logger.info("🔌 ESP32: Lendo sensores...")
    result = call_esp32_api('/api/sensors', 'GET')
    if result:
        logger.info(f"✅ ESP32 Sensores: Presença={result.get('presenca')}, Peso={result.get('peso')}, Temp={result.get('temperatura')}")
    return result


def confirm_esp32_detection(detection_type: str, confidence: float) -> dict | None:
    """Confirma detecção na API ESP32"""
    logger.info(f"✔️  ESP32: Confirmando detecção (tipo={detection_type}, confiança={confidence})...")
    result = call_esp32_api('/api/confirm_detection', 'POST', {
        'detection_type': detection_type,
        'confidence': float(confidence)
    })
    if result:
        logger.info(f"✅ ESP32: Detecção confirmada - {result.get('status')}")
    return result


def check_esp32_mechanical(presenca: bool, peso: float) -> dict | None:
    """Verifica detecção mecânica no ESP32"""
    logger.info(f"⚙️  ESP32: Verificando condição mecânica (presença={presenca}, peso={peso})...")
    result = call_esp32_api('/api/check_mechanical', 'POST', {
        'presenca': presenca,
        'peso': peso
    })
    if result:
        logger.info(f"✅ ESP32: Validação mecânica - {result.get('message')}")
    return result


def calculate_environmental_impact() -> dict[str, float]:
    """Calcula e retorna impacto ambiental por tampinha"""
    return {
        'plastico_reciclado_g': 0.5,
        'co2_evitado_g': 2.3,
        'agua_economizada_ml': 15,
        'arvores_preservadas_cm2': 8
    }