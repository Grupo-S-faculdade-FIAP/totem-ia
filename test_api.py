#!/usr/bin/env python3
"""
Script de testes para a API do Totem de Reciclagem
Valida todos os endpoints principais
"""

import requests
import json
import time
from pathlib import Path

# URL base da API
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Imprime um cabeçalho de seção"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_health():
    """Testa o endpoint GET /"""
    print_section("1. TESTE: Health Check (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_status():
    """Testa o endpoint GET /status"""
    print_section("2. TESTE: Status do Sistema (GET /status)")
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_classify_image():
    """Testa o endpoint POST /classify com uma imagem"""
    print_section("3. TESTE: Classificação de Imagem (POST /classify)")
    
    # Procura por uma imagem na pasta /images
    images_dir = Path("images")
    if not images_dir.exists():
        print(f"❌ Pasta 'images' não encontrada em {images_dir.absolute()}")
        return False
    
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if not image_files:
        print(f"❌ Nenhuma imagem encontrada em {images_dir.absolute()}")
        return False
    
    image_path = image_files[0]
    print(f"Usando imagem: {image_path.name}")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/jpeg")}
            response = requests.post(f"{BASE_URL}/classify", files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_batch():
    """Testa o endpoint POST /batch com múltiplas imagens"""
    print_section("4. TESTE: Processamento em Lote (POST /batch)")
    
    images_dir = Path("images")
    if not images_dir.exists():
        print(f"❌ Pasta 'images' não encontrada")
        return False
    
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if not image_files:
        print(f"❌ Nenhuma imagem encontrada")
        return False
    
    # Limita a 3 imagens para o teste
    image_files = image_files[:3]
    print(f"Processando {len(image_files)} imagens...")
    
    try:
        files = []
        for img_path in image_files:
            with open(img_path, "rb") as f:
                files.append(("files", (img_path.name, f.read(), "image/jpeg")))
        
        response = requests.post(f"{BASE_URL}/batch", files=files, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_esp32_endpoint():
    """Testa o endpoint otimizado para ESP32"""
    print_section("5. TESTE: Endpoint Otimizado ESP32 (POST /esp32/check)")
    
    images_dir = Path("images")
    if not images_dir.exists():
        print(f"❌ Pasta 'images' não encontrada")
        return False
    
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if not image_files:
        print(f"❌ Nenhuma imagem encontrada")
        return False
    
    image_path = image_files[0]
    print(f"Usando imagem: {image_path.name}")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/jpeg")}
            response = requests.post(f"{BASE_URL}/esp32/check", files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            print(f"\n💡 Interpretação para ESP32:")
            print(f"   - accept: {result.get('accept')} (envia carrinho se True)")
            print(f"   - color: {result.get('color')} (tampinha {result.get('color')})")
            print(f"   - confidence: {result.get('confidence'):.2%} (nível de certeza)")
            print(f"   - action: {result.get('action')} (comando para hardware)")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("\n" + "="*70)
    print("  🧪 TESTES DA API DO TOTEM DE RECICLAGEM")
    print("="*70)
    print(f"\nServidor: {BASE_URL}")
    
    # Aguarda um pouco para garantir que a API está pronta
    print("\nAguardando API estar pronta...")
    time.sleep(2)
    
    results = {}
    
    # Executa todos os testes
    results["Health Check"] = test_health()
    results["Status"] = test_status()
    results["Classificação"] = test_classify_image()
    results["Batch"] = test_batch()
    results["ESP32"] = test_esp32_endpoint()
    
    # Resumo
    print_section("📊 RESUMO DOS TESTES")
    print(f"{'Teste':<30} {'Status':<10}")
    print("-" * 40)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("-" * 40)
    print(f"Total: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("\n🎉 Todos os testes passaram! API pronta para produção!")
    else:
        print(f"\n⚠️  {len(results) - passed} teste(s) falharam. Verifique os logs acima.")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
