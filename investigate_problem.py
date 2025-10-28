#!/usr/bin/env python3
"""
Investigação do Problema de Classificação
"""

from evaluate_eligibility_fast import EnhancedFastClassifier
import numpy as np
import cv2
from pathlib import Path

def investigate_classification():
    print("🔍 INVESTIGAÇÃO DO PROBLEMA DE CLASSIFICAÇÃO")
    print("=" * 60)

    classifier = EnhancedFastClassifier()

    if not classifier.load_model():
        print("❌ Modelo não encontrado!")
        return

    print("✅ Modelo carregado!")

    # Verificar algumas imagens de treinamento (color-cap)
    print("\n📂 Verificando imagens de TREINAMENTO (color-cap):")
    train_dir = Path("datasets/color-cap/train/images")
    if train_dir.exists():
        train_files = list(train_dir.glob("*.jpg"))[:5]  # Apenas 5 primeiras
        for img_path in train_files:
            is_cap, confidence = classifier.predict_single(str(img_path))
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'
            print("30")

    # Verificar imagens de teste
    print("\n🧪 Verificando imagens de TESTE:")
    test_images = ['images/imagem1.jpg', 'images/imagem2.jpg', 'images/imagem3.jpg',
                   'images/imagem4.jpg', 'images/imagem5.jpg', 'images/imagem6.jpg']

    for img_path in test_images:
        if Path(img_path).exists():
            is_cap, confidence = classifier.predict_single(img_path)
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'
            print("30")

    # Verificar imagens da pasta tampinhas
    print("\n🏷️  Verificando imagens da pasta TAMPINHAS (reais):")
    tampinhas_dir = Path("datasets/tampinhas")
    if tampinhas_dir.exists():
        tampinhas_files = list(tampinhas_dir.glob("*.jpg"))
        for img_path in tampinhas_files:
            is_cap, confidence = classifier.predict_single(str(img_path))
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'
            print("30")

    print("\n🔍 ANÁLISE DO PROBLEMA:")
    print("-" * 40)
    print("1. O modelo foi treinado com TODAS as imagens dos datasets como 'positivas'")
    print("2. Amostras negativas foram criadas sinteticamente")
    print("3. Se as imagens de teste não são tampinhas reais, a classificação está CORRETA")
    print("4. Se as imagens de teste SÃO tampinhas, há um problema no treinamento")

    print("\n💡 POSSÍVEIS CAUSAS:")
    print("- As imagens de treinamento podem não ser tampinhas reais")
    print("- As imagens de teste podem não representar tampinhas")
    print("- O modelo pode estar overfitado aos dados de treinamento")

if __name__ == "__main__":
    investigate_classification()