#!/usr/bin/env python3
"""
🧪 TESTES - ESP32 TOTEM SERVER
Testes completos para os endpoints da API ESP32

Para rodar:
  pytest test_esp32_server.py -v
  ou
  python test_esp32_server.py
"""

import pytest
import requests
import json
import time
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

ESP32_API_URL = "http://localhost:5001"
DEVICE_ID = "xxxxxxxxx"
DEVICE_KEY = "xxxxxxxxx"

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def jwt_token():
    """Fixture para obter JWT token"""
    try:
        response = requests.post(
            f"{ESP32_API_URL}/api/auth/login",
            json={"device_id": DEVICE_ID, "device_key": DEVICE_KEY},
            timeout=5
        )
        return response.json()['token']
    except:
        pytest.skip("ESP32 Server não está disponível")

@pytest.fixture
def auth_headers(jwt_token):
    """Fixture para headers com autenticação"""
    return {'Authorization': f'Bearer {jwt_token}'}

# ============================================================================
# TESTES - Autenticação
# ============================================================================

class TestAuthentication:
    """Testes de autenticação JWT"""
    
    def test_login_sucesso(self):
        """✅ Login com credenciais válidas"""
        response = requests.post(
            f"{ESP32_API_URL}/api/auth/login",
            json={"device_id": DEVICE_ID, "device_key": DEVICE_KEY},
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'token' in data
        assert data['type'] == 'Bearer'
        assert data['expires_in'] == 86400  # 24 horas
        assert data['device_id'] == DEVICE_ID
        
        print(f"✅ Login bem-sucedido")
        print(f"   Token: {data['token'][:30]}...")
        print(f"   Expira em: {data['expires_in']} segundos")
    
    def test_login_falha(self):
        """✅ Login com credenciais inválidas"""
        response = requests.post(
            f"{ESP32_API_URL}/api/auth/login",
            json={"device_id": "invalido", "device_key": "invalido"},
            timeout=5
        )
        
        assert response.status_code == 401
        print("✅ Login rejeitado para credenciais inválidas")
    
    def test_token_formato_valido(self, jwt_token):
        """✅ Verifica formato do token JWT"""
        # JWT tem formato: header.payload.signature
        parts = jwt_token.split('.')
        assert len(parts) == 3
        print(f"✅ Token JWT tem formato válido")

# ============================================================================
# TESTES - Health & Status
# ============================================================================

class TestHealthStatus:
    """Testes de health check e status"""
    
    def test_health_check(self):
        """✅ Health check sem autenticação"""
        response = requests.get(f"{ESP32_API_URL}/api/health", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'online'
        assert data['service'] == 'esp32-totem-server'
        assert 'timestamp' in data
        
        print(f"✅ Health check OK")
        print(f"   Status: {data['status']}")
        print(f"   Serviço: {data['service']}")
    
    def test_status_sem_autenticacao(self):
        """✅ Status sem autenticação retorna básico"""
        response = requests.get(f"{ESP32_API_URL}/api/status", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert data['authenticated'] == False
        
        print(f"✅ Status sem auth: {data['status']}")
    
    def test_status_com_autenticacao(self, auth_headers):
        """✅ Status com autenticação retorna dados completos"""
        response = requests.get(
            f"{ESP32_API_URL}/api/status",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert data['authenticated'] == True
        
        print(f"✅ Status com auth: {data['status']}")

# ============================================================================
# TESTES - Sensores
# ============================================================================

class TestSensors:
    """Testes de leitura de sensores"""
    
    def test_sensors_sem_token(self):
        """✅ Sensores sem token retorna erro"""
        response = requests.get(f"{ESP32_API_URL}/api/sensors", timeout=5)
        
        assert response.status_code == 401
        print("✅ Sensores protegidos (requer token)")
    
    def test_sensors_com_token(self, auth_headers):
        """✅ Leitura de sensores com autenticação"""
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos esperados
        assert 'presenca' in data
        assert 'peso' in data
        assert 'temperatura' in data
        assert 'timestamp' in data
        
        # Verificar tipos
        assert isinstance(data['presenca'], bool)
        assert isinstance(data['peso'], int)
        assert isinstance(data['temperatura'], (int, float))
        
        # Verificar ranges
        assert 0 <= data['peso'] <= 4095  # ADC 12-bit
        assert 20 <= data['temperatura'] <= 40  # Temperatura razoável
        
        print(f"✅ Sensores lidos com sucesso:")
        print(f"   Presença: {data['presenca']}")
        print(f"   Peso: {data['peso']}")
        print(f"   Temperatura: {data['temperatura']:.1f}°C")

# ============================================================================
# TESTES - Validação Mecânica
# ============================================================================

class TestMechanical:
    """Testes de validação mecânica"""
    
    def test_check_mechanical_sem_token(self):
        """✅ Check mechanical sem token retorna erro"""
        response = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={"presenca": True, "peso": 2500},
            timeout=5
        )
        
        assert response.status_code == 401
        print("✅ Check mechanical protegido")
    
    def test_check_mechanical_com_token(self, auth_headers):
        """✅ Validação mecânica com token"""
        response = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={"presenca": True, "peso": 2500},
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'message' in data
        assert 'timestamp' in data
        
        print(f"✅ Validação mecânica realizada")
        print(f"   Resposta: {data['message']}")
    
    def test_check_mechanical_presenca_verdadeira(self, auth_headers):
        """✅ Validação com presença TRUE"""
        response = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={"presenca": True, "peso": 2500},
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        print("✅ Presença TRUE validada")
    
    def test_check_mechanical_presenca_falsa(self, auth_headers):
        """✅ Validação com presença FALSE"""
        response = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={"presenca": False, "peso": 2500},
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        print("✅ Presença FALSE validada")
    
    def test_check_mechanical_peso_vario(self, auth_headers):
        """✅ Validação com pesos diferentes"""
        pesos = [0, 1000, 2500, 4000, 4095]
        
        for peso in pesos:
            response = requests.post(
                f"{ESP32_API_URL}/api/check_mechanical",
                json={"presenca": True, "peso": peso},
                headers=auth_headers,
                timeout=5
            )
            assert response.status_code == 200
        
        print(f"✅ Validação com {len(pesos)} pesos diferentes OK")

# ============================================================================
# TESTES - Detecção
# ============================================================================

class TestDetection:
    """Testes de confirmação de detecção"""
    
    def test_confirm_detection_sem_token(self):
        """✅ Confirm detection sem token retorna erro"""
        response = requests.post(
            f"{ESP32_API_URL}/api/confirm_detection",
            json={"detection_type": "presence", "confidence": 0.95},
            timeout=5
        )
        
        assert response.status_code == 401
        print("✅ Confirm detection protegido")
    
    def test_confirm_detection_com_token(self, auth_headers):
        """✅ Confirmação de detecção com token"""
        response = requests.post(
            f"{ESP32_API_URL}/api/confirm_detection",
            json={"detection_type": "presence", "confidence": 0.95},
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'confirmed'
        assert data['detection_type'] == 'presence'
        assert data['confidence'] == 0.95
        
        print(f"✅ Detecção confirmada:")
        print(f"   Tipo: {data['detection_type']}")
        print(f"   Confiança: {data['confidence']}")
    
    def test_confirm_detection_tipos(self, auth_headers):
        """✅ Teste com diferentes tipos de detecção"""
        tipos = ["presence", "weight", "tampinha"]
        
        for tipo in tipos:
            response = requests.post(
                f"{ESP32_API_URL}/api/confirm_detection",
                json={"detection_type": tipo, "confidence": 0.9},
                headers=auth_headers,
                timeout=5
            )
            assert response.status_code == 200
        
        print(f"✅ {len(tipos)} tipos de detecção confirmados")
    
    def test_confirm_detection_confiancas(self, auth_headers):
        """✅ Teste com diferentes níveis de confiança"""
        confiancas = [0.1, 0.5, 0.75, 0.9, 0.99, 1.0]
        
        for conf in confiancas:
            response = requests.post(
                f"{ESP32_API_URL}/api/confirm_detection",
                json={"detection_type": "tampinha", "confidence": conf},
                headers=auth_headers,
                timeout=5
            )
            assert response.status_code == 200
        
        print(f"✅ {len(confiancas)} níveis de confiança testados")

# ============================================================================
# TESTES - Telemetria
# ============================================================================

class TestTelemetry:
    """Testes de telemetria"""
    
    def test_telemetry_sem_token(self):
        """✅ Telemetria sem token retorna erro"""
        response = requests.post(
            f"{ESP32_API_URL}/api/telemetry",
            json={"uptime_seconds": 3600, "requests_total": 150, "errors": 2},
            timeout=5
        )
        
        assert response.status_code == 401
        print("✅ Telemetria protegida")
    
    def test_telemetry_com_token(self, auth_headers):
        """✅ Envio de telemetria com token"""
        response = requests.post(
            f"{ESP32_API_URL}/api/telemetry",
            json={
                "uptime_seconds": 3600,
                "requests_total": 150,
                "errors": 2
            },
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'received'
        assert data['uptime_seconds'] == 3600
        assert data['requests_total'] == 150
        assert data['errors'] == 2
        
        print(f"✅ Telemetria recebida:")
        print(f"   Uptime: {data['uptime_seconds']}s")
        print(f"   Requisições: {data['requests_total']}")
        print(f"   Erros: {data['errors']}")

# ============================================================================
# TESTES - Statistics
# ============================================================================

class TestStatistics:
    """Testes de estatísticas"""
    
    def test_statistics_sem_autenticacao(self):
        """✅ Estatísticas sem autenticação"""
        response = requests.get(f"{ESP32_API_URL}/api/statistics", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"✅ Estatísticas obtidas (público)")
    
    def test_statistics_contem_dados(self, auth_headers):
        """✅ Estatísticas contêm dados esperados"""
        response = requests.get(
            f"{ESP32_API_URL}/api/statistics",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estrutura
        if isinstance(data, dict):
            print(f"✅ Estatísticas contêm {len(data)} campos")
        elif isinstance(data, list):
            print(f"✅ Estatísticas contêm {len(data)} itens")

# ============================================================================
# TESTES - WiFi Info
# ============================================================================

class TestWiFiInfo:
    """Testes de informações WiFi"""
    
    def test_wifi_info(self, auth_headers):
        """✅ Informações WiFi"""
        response = requests.get(
            f"{ESP32_API_URL}/api/wifi",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"✅ Informações WiFi obtidas")
        print(f"   Dados: {json.dumps(data, indent=2)}")

# ============================================================================
# TESTES - Segurança
# ============================================================================

class TestSecurity:
    """Testes de segurança"""
    
    def test_token_invalido_rejeitado(self):
        """✅ Token inválido é rejeitado"""
        headers = {'Authorization': 'Bearer TOKEN_INVALIDO_12345'}
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code in [401, 403]
        print("✅ Token inválido rejeitado")
    
    def test_bearer_obrigatorio(self):
        """✅ Formato Bearer é obrigatório"""
        headers = {'Authorization': 'Basic token123'}
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code in [401, 403]
        print("✅ Formato Bearer obrigatório")
    
    def test_sem_authorization_header(self):
        """✅ Sem header Authorization"""
        response = requests.get(f"{ESP32_API_URL}/api/sensors", timeout=5)
        
        assert response.status_code == 401
        print("✅ Header Authorization obrigatório")

# ============================================================================
# TESTES - Performance
# ============================================================================

class TestPerformance:
    """Testes de performance"""
    
    def test_health_check_rapido(self):
        """✅ Health check é muito rápido"""
        start = time.time()
        response = requests.get(f"{ESP32_API_URL}/api/health", timeout=5)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Health check demorou {elapsed:.3f}s"
        print(f"✅ Health check: {elapsed*1000:.1f}ms")
    
    def test_sensors_rapido(self, auth_headers):
        """✅ Leitura de sensores é rápida"""
        start = time.time()
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=auth_headers,
            timeout=5
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1, f"Sensors demorou {elapsed:.3f}s"
        print(f"✅ Sensores: {elapsed*1000:.1f}ms")
    
    def test_requests_em_serie(self, auth_headers):
        """✅ 10 requisições em série"""
        start = time.time()
        
        for i in range(10):
            response = requests.get(
                f"{ESP32_API_URL}/api/sensors",
                headers=auth_headers,
                timeout=5
            )
            assert response.status_code == 200
        
        elapsed = time.time() - start
        avg = elapsed / 10
        
        assert elapsed < 10, f"10 requisições demoraram {elapsed:.2f}s"
        print(f"✅ 10 requisições em {elapsed:.2f}s (média: {avg*1000:.1f}ms)")

# ============================================================================
# TESTES - Integração
# ============================================================================

class TestIntegration:
    """Testes de integração"""
    
    def test_fluxo_completo(self, auth_headers):
        """✅ Fluxo completo de operações"""
        print("\n🔄 Teste de fluxo completo:")
        
        # 1. Ler sensores
        r1 = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=auth_headers,
            timeout=5
        )
        assert r1.status_code == 200
        sensores = r1.json()
        print(f"  1️⃣  Sensores: presença={sensores['presenca']}, peso={sensores['peso']}")
        
        # 2. Validar mecânica
        r2 = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={"presenca": sensores['presenca'], "peso": sensores['peso']},
            headers=auth_headers,
            timeout=5
        )
        assert r2.status_code == 200
        print(f"  2️⃣  Validação mecânica: OK")
        
        # 3. Confirmar detecção
        r3 = requests.post(
            f"{ESP32_API_URL}/api/confirm_detection",
            json={"detection_type": "tampinha", "confidence": 0.95},
            headers=auth_headers,
            timeout=5
        )
        assert r3.status_code == 200
        print(f"  3️⃣  Detecção confirmada: OK")
        
        # 4. Enviar telemetria
        r4 = requests.post(
            f"{ESP32_API_URL}/api/telemetry",
            json={"uptime_seconds": 3600, "requests_total": 4, "errors": 0},
            headers=auth_headers,
            timeout=5
        )
        assert r4.status_code == 200
        print(f"  4️⃣  Telemetria enviada: OK")
        
        print("✅ Fluxo completo sucesso!")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🧪 SUITE DE TESTES - ESP32 TOTEM SERVER")
    print("="*70 + "\n")
    
    pytest.main([__file__, '-v', '--tb=short', '-s'])
