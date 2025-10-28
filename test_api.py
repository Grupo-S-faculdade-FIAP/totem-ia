#!/usr/bin/env python3
"""
Script para testar a API do TOTEM IA
Classifica imagens da pasta /images sem abrir a interface web
"""

import requests
import base64
import json
import sys
from pathlib import Path
import time

BASE_URL = 'http://localhost:5000'

def test_health():
    """Testa se o servidor está rodando"""
    print('🔍 Testando conexão com o servidor...')
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Servidor OK - Modelo carregado: {data["model_loaded"]}')
            return True
        else:
            print(f'❌ Erro HTTP {response.status_code}')
            return False
    except requests.exceptions.ConnectionError:
        print(f'❌ Não foi possível conectar a {BASE_URL}')
        print('   Verifique se o servidor está rodando: python app.py')
        return False

def encode_image(image_path):
    """Codifica imagem em base64"""
    with open(image_path, 'rb') as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def classify_image(image_path):
    """Classifica uma imagem"""
    try:
        # Codificar imagem
        image_data = encode_image(image_path)
        
        # Preparar payload
        payload = {
            'image': f'data:image/jpeg;base64,{image_data}'
        }
        
        # Enviar requisição
        print(f'  📸 Enviando {Path(image_path).name}...', end=' ', flush=True)
        response = requests.post(
            f'{BASE_URL}/api/classify',
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Formatar resultado
            status = '✅ TAMPINHA' if result['is_tampinha'] else '❌ NÃO-TAMPINHA'
            print(f'{status}')
            
            # Detalhes
            print(f'     Confiança: {result["confidence"]*100:.0f}%')
            print(f'     Saturação: {result["saturation"]:.1f}')
            print(f'     Método: {result["method"]}')
            print()
            
            return result
        else:
            print(f'❌ Erro HTTP {response.status_code}')
            return None
            
    except Exception as e:
        print(f'❌ Erro: {e}')
        return None

def main():
    print('='*80)
    print('🏆 TOTEM IA - TESTE DE API')
    print('   Classificador de Tampinhas')
    print('='*80)
    print()

    # Verificar conexão
    if not test_health():
        sys.exit(1)
    
    print()
    print('🔍 Classificando imagens em /images...')
    print('-'*80)
    print()

    # Encontrar imagens
    image_dir = Path('images')
    if not image_dir.exists():
        print(f'❌ Pasta {image_dir} não encontrada!')
        sys.exit(1)

    image_files = sorted([
        f for f in image_dir.glob('*.jpg') if f.is_file()
    ] + [
        f for f in image_dir.glob('*.jpeg') if f.is_file()
    ] + [
        f for f in image_dir.glob('*.JPG') if f.is_file()
    ])

    if not image_files:
        print('❌ Nenhuma imagem encontrada em /images')
        sys.exit(1)

    print(f'Encontradas {len(image_files)} imagens\n')

    # Classificar cada imagem
    results = []
    tampinhas_count = 0
    nao_tampinhas_count = 0

    for img_path in image_files:
        result = classify_image(img_path)
        if result:
            results.append(result)
            if result['is_tampinha']:
                tampinhas_count += 1
            else:
                nao_tampinhas_count += 1
        time.sleep(0.5)  # Pequeno delay entre requisições

    # Estatísticas finais
    print('='*80)
    print('📊 RESUMO FINAL')
    print('-'*80)
    print(f'Total de imagens: {len(results)}')
    print(f'Tampinhas detectadas: {tampinhas_count}')
    print(f'Não-tampinhas: {nao_tampinhas_count}')
    
    if results:
        confianca_media = sum(r['confidence'] for r in results) / len(results)
        saturacao_media = sum(r['saturation'] for r in results) / len(results)
        print(f'Confiança média: {confianca_media*100:.1f}%')
        print(f'Saturação média: {saturacao_media:.1f}')
    
    print('='*80)

if __name__ == '__main__':
    main()