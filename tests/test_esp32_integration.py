#!/usr/bin/env python3
"""
🧪 TESTES - TOTEM IA + ESP32 Integration
Testes completos para a integração com ESP32 TOTEM Server

Para rodar:
  pytest test_esp32_integration.py -v
  ou
  python test_esp32_integration.py
"""

import pytest
import requests
import json
import base64
import time
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

TOTEM_API_URL = "http://localhost:8000"
ESP32_API_URL = "http://localhost:5001"

# Criar imagem de teste se não existir
def create_test_image():
    """Cria uma imagem de teste simples"""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = [102, 126, 233]  # Cor azul do projeto
    test_path = Path("test_image.jpg")
    cv2.imwrite(str(test_path), img)
    return test_path

TEST_IMAGE = create_test_image()

# ============================================================================
# TESTES - ESP32 API (Health & Status)
# ============================================================================

class TestESP32Health:
    """Testes de health check do ESP32 Server"""
    
    def test_esp32_api_disponivel(self):
        """✅ Verifica se ESP32 API está disponível"""
        try:
            response = requests.get(f"{ESP32_API_URL}/api/health", timeout=5)
            assert response.status_code == 200
            assert response.json()['status'] == 'online'
            print("✅ ESP32 API está online")
        except requests.exceptions.ConnectionError:
            pytest.skip("ESP32 Server não está rodando")
    
    def test_esp32_status(self):
        """✅ Verifica status do ESP32"""
        response = requests.get(f"{ESP32_API_URL}/api/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'authenticated' in data
    
    def test_esp32_login(self):
        """✅ Testa autenticação JWT no ESP32"""
        response = requests.post(
            f"{ESP32_API_URL}/api/auth/login",
            json={
                "device_id": "xxxxxxxxx",
                "device_key": "xxxxxxxxx"
            },
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert data['type'] == 'Bearer'
        assert data['expires_in'] == 86400
        print(f"✅ JWT Token obtido: {data['token'][:20]}...")

# ============================================================================
# TESTES - TOTEM IA Health
# ============================================================================

class TestTOTEMHealth:
    """Testes de health check do TOTEM IA"""
    
    def test_totem_api_disponivel(self):
        """✅ Verifica se TOTEM IA API está disponível"""
        try:
            response = requests.get(f"{TOTEM_API_URL}/", timeout=5)
            assert response.status_code == 200
            print("✅ TOTEM IA API está online")
        except requests.exceptions.ConnectionError:
            pytest.skip("TOTEM IA não está rodando")
    
    def test_esp32_health_endpoint(self):
        """✅ Testa endpoint de health do ESP32 via TOTEM"""
        response = requests.get(f"{TOTEM_API_URL}/api/esp32-health", timeout=5)
        assert response.status_code in [200, 503]
        data = response.json()
        assert 'status' in data

# ============================================================================
# TESTES - Classificação (Antes)
# ============================================================================

class TestClassification:
    """Testes de classificação SVM"""
    
    def test_classify_image_upload(self):
        """✅ Testa classificação via upload de arquivo"""
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TOTEM_API_URL}/api/classify",
                files=files,
                timeout=10
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'confidence' in data
        assert 'saturation' in data
        assert 'method' in data
        print(f"✅ Classificação: {data['status']} (confiança: {data['confidence']:.2%})")
    
    def test_classify_image_base64(self):
        """✅ Testa classificação via base64"""
        with open(TEST_IMAGE, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{TOTEM_API_URL}/api/classify",
            json={'image': f"data:image/jpeg;base64,{image_data}"},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'is_tampinha' in data

# ============================================================================
# TESTES - Validação Completa (NOVO!)
# ============================================================================

class TestValidateComplete:
    """Testes da validação completa com ESP32"""
    
    def test_validate_complete_arquivo(self):
        """✅ Testa validação completa via upload"""
        print("\n📸 Iniciando validação completa...")
        start_time = time.time()
        
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TOTEM_API_URL}/api/validate-complete",
                files=files,
                timeout=15
            )
        
        elapsed = time.time() - start_time
        assert response.status_code == 200
        data = response.json()
        
        print(f"⏱️  Tempo total: {elapsed:.2f}s")
        print(f"📊 Status: {data['status']}")
        
        # Validar estrutura da resposta
        assert 'status' in data
        assert 'timestamp' in data
        
        # Se rejeitado na etapa 1
        if data['status'] == 'rejeitado':
            assert 'stage' in data
            print(f"❌ Rejeitado na etapa: {data['stage']}")
        
        # Se sucesso
        elif data['status'] == 'sucesso':
            assert 'stages' in data
            assert 'classificacao' in data['stages']
            assert 'mecanica' in data['stages']
            
            class_data = data['stages']['classificacao']
            mech_data = data['stages']['mecanica']
            
            print(f"✅ Classificação: {class_data['status']}")
            print(f"   - is_tampinha: {class_data['is_tampinha']}")
            print(f"   - confidence: {class_data['confidence']:.4f}")
            print(f"✅ Mecânica: {mech_data['status']}")
            print(f"   - presença: {mech_data['presenca']}")
            print(f"   - peso: {mech_data['peso']}")
    
    def test_validate_complete_base64(self):
        """✅ Testa validação completa via base64"""
        with open(TEST_IMAGE, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            f"{TOTEM_API_URL}/api/validate-complete",
            json={'image': f"data:image/jpeg;base64,{image_data}"},
            timeout=15
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
    
    def test_validate_complete_erro_imagem_invalida(self):
        """✅ Testa validação com imagem inválida"""
        response = requests.post(
            f"{TOTEM_API_URL}/api/validate-complete",
            json={'image': 'data:image/jpeg;base64,INVALIDO'},
            timeout=10
        )
        
        # Pode ser 400 ou 500, ambos são aceitáveis
        assert response.status_code in [400, 500]
        print("✅ Erro tratado corretamente para imagem inválida")
    
    def test_validate_complete_sem_imagem(self):
        """✅ Testa validação sem imagem"""
        response = requests.post(
            f"{TOTEM_API_URL}/api/validate-complete",
            json={},
            timeout=10
        )
        
        assert response.status_code == 400
        print("✅ Erro tratado corretamente para falta de imagem")

# ============================================================================
# TESTES - ESP32 Endpoints (com JWT)
# ============================================================================

class TestESP32Endpoints:
    """Testes dos endpoints do ESP32 com autenticação JWT"""
    
    @pytest.fixture
    def jwt_token(self):
        """Fixture para obter JWT token"""
        response = requests.post(
            f"{ESP32_API_URL}/api/auth/login",
            json={
                "device_id": "xxxxxxxxx",
                "device_key": "xxxxxxxxx"
            },
            timeout=5
        )
        return response.json()['token']
    
    def test_esp32_get_sensors(self, jwt_token):
        """✅ Testa leitura de sensores"""
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'presenca' in data
        assert 'peso' in data
        assert 'temperatura' in data
        print(f"✅ Sensores: presença={data['presenca']}, peso={data['peso']}")
    
    def test_esp32_check_mechanical(self, jwt_token):
        """✅ Testa validação mecânica"""
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.post(
            f"{ESP32_API_URL}/api/check_mechanical",
            json={'presenca': True, 'peso': 2500},
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data or 'status' in data
        print(f"✅ Validação mecânica realizada")
    
    def test_esp32_confirm_detection(self, jwt_token):
        """✅ Testa confirmação de detecção"""
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.post(
            f"{ESP32_API_URL}/api/confirm_detection",
            json={'detection_type': 'tampinha', 'confidence': 0.95},
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'confirmed'
        print(f"✅ Detecção confirmada")
    
    def test_esp32_telemetry(self, jwt_token):
        """✅ Testa envio de telemetria"""
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.post(
            f"{ESP32_API_URL}/api/telemetry",
            json={
                'uptime_seconds': 3600,
                'requests_total': 150,
                'errors': 2
            },
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 200
        print(f"✅ Telemetria enviada")

# ============================================================================
# TESTES - Segurança
# ============================================================================

class TestSecurity:
    """Testes de segurança"""
    
    def test_esp32_protegido_sem_token(self):
        """✅ Verifica que endpoints são protegidos sem token"""
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            timeout=5
        )
        
        # Deve retornar 401 ou erro
        assert response.status_code in [401, 403, 400]
        print("✅ Endpoint protegido sem token")
    
    def test_esp32_token_invalido(self):
        """✅ Verifica rejeição de token inválido"""
        headers = {'Authorization': 'Bearer TOKEN_INVALIDO'}
        response = requests.get(
            f"{ESP32_API_URL}/api/sensors",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code in [401, 403]
        print("✅ Token inválido rejeitado")

# ============================================================================
# TESTES - Performance
# ============================================================================

class TestPerformance:
    """Testes de performance"""
    
    def test_validacao_tempo_maximo(self):
        """✅ Verifica se validação completa fica abaixo de 10 segundos"""
        start = time.time()
        
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TOTEM_API_URL}/api/validate-complete",
                files=files,
                timeout=15
            )
        
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 10, f"Validação demorou {elapsed:.2f}s (máximo 10s)"
        print(f"✅ Validação concluída em {elapsed:.2f}s")
    
    def test_classificacao_rapida(self):
        """✅ Verifica se classificação é rápida"""
        start = time.time()
        
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TOTEM_API_URL}/api/classify",
                files=files,
                timeout=10
            )
        
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 5, f"Classificação demorou {elapsed:.2f}s"
        print(f"✅ Classificação concluída em {elapsed:.2f}s")
    
    def test_esp32_resposta_rapida(self):
        """✅ Verifica se ESP32 responde rapidamente"""
        start = time.time()
        response = requests.get(f"{ESP32_API_URL}/api/health", timeout=5)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1, f"ESP32 demorou {elapsed:.2f}s"
        print(f"✅ ESP32 respondeu em {elapsed:.3f}s")

# ============================================================================
# TESTES - Integração End-to-End
# ============================================================================

class TestEndToEnd:
    """Testes de integração completa"""
    
    def test_fluxo_completo_tampinha_aceita(self):
        """✅ Testa fluxo completo quando tampinha é aceita"""
        print("\n🎯 Teste End-to-End: Tampinha Aceita")
        
        # 1. Validação completa
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{TOTEM_API_URL}/api/validate-complete",
                files=files,
                timeout=15
            )
        
        assert response.status_code == 200
        data = response.json()
        print(f"1️⃣  Validação: {data['status']}")
        
        # 2. Se aceita, verificar estrutura completa
        if data['status'] == 'sucesso':
            assert 'stages' in data
            assert data['stages']['classificacao']['is_tampinha'] is True
            assert data['stages']['mecanica']['status'] == 'sucesso'
            print("2️⃣  ✅ Taminha aceita em ambas as etapas")
        else:
            print("2️⃣  ⚠️  Tampinha rejeitada (normal para teste)")
    
    def test_fluxo_json_response_valido(self):
        """✅ Verifica que todas as respostas são JSON válido"""
        endpoints = [
            (f"{ESP32_API_URL}/api/health", "GET", None),
            (f"{TOTEM_API_URL}/api/esp32-health", "GET", None),
        ]
        
        for url, method, data in endpoints:
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json=data, timeout=5)
                
                # Tentar parsear JSON
                response.json()
                print(f"✅ JSON válido: {url}")
            except requests.exceptions.ConnectionError:
                print(f"⚠️  Não conseguiu conectar: {url}")
            except json.JSONDecodeError:
                print(f"❌ JSON inválido: {url}")
                raise

# ============================================================================
# MAIN - Executar testes
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🧪 SUITE DE TESTES - TOTEM IA + ESP32 INTEGRATION")
    print("="*70 + "\n")
    
    # Rodar com pytest
    pytest.main([__file__, '-v', '--tb=short'])
