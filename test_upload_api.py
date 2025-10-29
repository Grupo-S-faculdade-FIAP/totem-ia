#!/usr/bin/env python3
"""
Script de Teste para Upload de Fotos - TOTEM IA
================================================

Testa a API de upload de imagens para classificação.
Funciona com ambos os métodos: base64 e multipart/form-data.
"""

import requests
import base64
from pathlib import Path
import json
import time

API_URL = "http://127.0.0.1:5000/api/classify"
HEALTH_URL = "http://127.0.0.1:5000/api/health"

def test_health():
    """Testa se o servidor está respondendo"""
    print("\n" + "="*70)
    print("TESTE 1: Health Check")
    print("="*70)
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Modelo carregado: {data.get('model_loaded')}")
        print(f"Timestamp: {data.get('timestamp')}")
        return data.get('status') == 'ok'
    except Exception as e:
        print(f"ERRO: {e}")
        return False

def classify_with_file(image_path):
    """Classifica imagem usando upload de arquivo (multipart/form-data)"""
    print("\n" + "="*70)
    print("TESTE 2: Upload de Arquivo (multipart/form-data)")
    print("="*70)
    
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"ERRO: Arquivo nao encontrado: {image_path}")
        return False
    
    try:
        print(f"Enviando arquivo: {image_path.name}")
        print(f"Tamanho: {image_path.stat().st_size / 1024:.1f} KB")
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            start = time.time()
            response = requests.post(API_URL, files=files, timeout=10)
            elapsed = time.time() - start
        
        print(f"Tempo de resposta: {elapsed:.2f}s")
        print(f"Status HTTP: {response.status_code}")
        
        data = response.json()
        
        if response.ok:
            print(f"\nResultado:")
            print(f"  Status: {data.get('status')}")
            print(f"  Classificacao: {data.get('classification')}")
            print(f"  Confianca: {data.get('confidence')*100:.1f}%")
            print(f"  Saturacao: {data.get('saturation'):.1f}")
            print(f"  Metodo: {data.get('method')}")
            print(f"  Mensagem: {data.get('message')}")
            return True
        else:
            print(f"ERRO: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"ERRO: {e}")
        return False

def classify_with_base64(image_path):
    """Classifica imagem usando base64 (JSON)"""
    print("\n" + "="*70)
    print("TESTE 3: Upload em Base64 (JSON)")
    print("="*70)
    
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"ERRO: Arquivo nao encontrado: {image_path}")
        return False
    
    try:
        print(f"Codificando arquivo: {image_path.name}")
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        print(f"Tamanho original: {len(image_bytes) / 1024:.1f} KB")
        print(f"Tamanho em base64: {len(base64_image) / 1024:.1f} KB")
        
        payload = {
            'image': f'data:image/jpeg;base64,{base64_image}'
        }
        
        print(f"Enviando requisicao...")
        start = time.time()
        response = requests.post(
            API_URL,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        elapsed = time.time() - start
        
        print(f"Tempo de resposta: {elapsed:.2f}s")
        print(f"Status HTTP: {response.status_code}")
        
        data = response.json()
        
        if response.ok:
            print(f"\nResultado:")
            print(f"  Status: {data.get('status')}")
            print(f"  Classificacao: {data.get('classification')}")
            print(f"  Confianca: {data.get('confidence')*100:.1f}%")
            print(f"  Saturacao: {data.get('saturation'):.1f}")
            print(f"  Metodo: {data.get('method')}")
            print(f"  Mensagem: {data.get('message')}")
            return True
        else:
            print(f"ERRO: {data.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"ERRO: {e}")
        return False

def batch_classify(folder_path):
    """Classifica todas as imagens em uma pasta"""
    print("\n" + "="*70)
    print("TESTE 4: Classificacao em Lote")
    print("="*70)
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"ERRO: Pasta nao encontrada: {folder_path}")
        return False
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = [f for f in folder.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"Nenhuma imagem encontrada em: {folder_path}")
        return False
    
    print(f"Encontradas {len(image_files)} imagens")
    
    results = {
        'sucesso': 0,
        'erro': 0,
        'detalhes': []
    }
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processando: {image_file.name}")
        
        try:
            with open(image_file, 'rb') as f:
                files = {'file': f}
                start = time.time()
                response = requests.post(API_URL, files=files, timeout=10)
                elapsed = time.time() - start
            
            if response.ok:
                data = response.json()
                print(f"  ✓ {data.get('classification')} (confianca: {data.get('confidence')*100:.1f}%)")
                results['sucesso'] += 1
                results['detalhes'].append({
                    'arquivo': image_file.name,
                    'resultado': data.get('classification'),
                    'confianca': data.get('confidence'),
                    'tempo': elapsed
                })
            else:
                print(f"  ✗ Erro: {response.json().get('error')}")
                results['erro'] += 1
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            results['erro'] += 1
    
    print("\n" + "="*70)
    print("RESUMO DO LOTE")
    print("="*70)
    print(f"Total processado: {len(image_files)}")
    print(f"Sucessos: {results['sucesso']}")
    print(f"Erros: {results['erro']}")
    
    if results['detalhes']:
        print(f"\nTempo medio: {sum(d['tempo'] for d in results['detalhes']) / len(results['detalhes']):.2f}s")

def main():
    print("\n" + "="*70)
    print("TESTE DE API - TOTEM IA")
    print("Sistema de Deposito Inteligente de Tampinhas")
    print("="*70)
    
    # Test 1: Health Check
    if not test_health():
        print("\nERRO: Servidor nao esta respondendo!")
        print("Certifique-se de que o Flask esta rodando:")
        print("  python app.py")
        return
    
    # Procurar imagens de teste
    dataset_path = Path('datasets')
    test_images = []
    
    if dataset_path.exists():
        tampinhas = list(dataset_path.glob('tampinhas/*'))[:2]
        nao_tampinhas = list(dataset_path.glob('nao_tampinhas/*'))[:2]
        test_images = tampinhas + nao_tampinhas
    
    if not test_images:
        print("\nAVISO: Nenhuma imagem de teste encontrada em 'datasets/'")
        print("Criando imagem de teste simples...")
        
        import cv2
        import numpy as np
        
        # Criar imagem de teste
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[:, :] = (120, 150, 100)  # Cor similar a tampinha
        cv2.imwrite('test_image.jpg', test_img)
        test_images = [Path('test_image.jpg')]
    
    # Test 2: Upload com arquivo
    if test_images:
        classify_with_file(test_images[0])
    
    # Test 3: Upload com base64
    if test_images:
        classify_with_base64(test_images[0])
    
    # Test 4: Batch processing
    if dataset_path.exists():
        batch_classify(dataset_path / 'tampinhas')
    
    print("\n" + "="*70)
    print("TESTES CONCLUIDOS")
    print("="*70)

if __name__ == '__main__':
    main()
