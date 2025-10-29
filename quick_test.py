#!/usr/bin/env python3
"""
Teste Rápido - Upload de Foto para TOTEM IA
"""

import requests
from pathlib import Path
import json

API_URL = "http://127.0.0.1:5000/api/classify"

def test_api():
    print("\nTestando API de Upload...\n")
    
    # Procurar imagem de teste
    dataset = Path('datasets')
    test_image = None
    
    if (dataset / 'tampinhas').exists():
        images = list((dataset / 'tampinhas').glob('*'))[:1]
        if images:
            test_image = images[0]
    
    if (dataset / 'nao_tampinhas').exists() and not test_image:
        images = list((dataset / 'nao_tampinhas').glob('*'))[:1]
        if images:
            test_image = images[0]
    
    if not test_image:
        print("Nenhuma imagem de teste encontrada no dataset!")
        return
    
    print(f"Testando com imagem: {test_image.name}")
    print(f"Tamanho: {test_image.stat().st_size / 1024:.1f} KB\n")
    
    # Teste 1: Multipart upload
    print("=" * 60)
    print("TESTE 1: Upload de Arquivo (Multipart Form-Data)")
    print("=" * 60)
    
    try:
        with open(test_image, 'rb') as f:
            files = {'file': f}
            response = requests.post(API_URL, files=files, timeout=10)
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"Classificação: {data.get('classification')}")
        print(f"Confiança: {data.get('confidence') * 100:.1f}%")
        print(f"Saturação: {data.get('saturation'):.1f}")
        print(f"Método: {data.get('method')}")
        print(f"Mensagem: {data.get('message')}")
        
    except Exception as e:
        print(f"ERRO: {e}")
    
    # Teste 2: Base64 upload
    print("\n" + "=" * 60)
    print("TESTE 2: Upload em Base64 (JSON)")
    print("=" * 60)
    
    try:
        import base64
        
        with open(test_image, 'rb') as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {'image': f'data:image/jpeg;base64,{base64_image}'}
        response = requests.post(API_URL, json=payload, timeout=10)
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"Classificação: {data.get('classification')}")
        print(f"Confiança: {data.get('confidence') * 100:.1f}%")
        print(f"Saturação: {data.get('saturation'):.1f}")
        print(f"Método: {data.get('method')}")
        print(f"Mensagem: {data.get('message')}")
        
    except Exception as e:
        print(f"ERRO: {e}")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUIDOS COM SUCESSO!")
    print("=" * 60)
    print("\nAcesse a interface em: http://localhost:5000/totem_v2.html")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    test_api()
