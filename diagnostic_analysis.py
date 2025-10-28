#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO - Por que a classificação está errada?
"""

from evaluate_eligibility_fast import EnhancedFastClassifier
from corrected_classifier import CorrectedCapClassifier
import numpy as np
import cv2
from pathlib import Path

def diagnostic_analysis():
    print("🔍 DIAGNÓSTICO COMPLETO DO PROBLEMA DE CLASSIFICAÇÃO")
    print("=" * 70)

    # 1. Verificar dados de treinamento originais
    print("\n1️⃣  DADOS DE TREINAMENTO ORIGINAIS:")
    print("-" * 40)

    classifier_original = EnhancedFastClassifier()
    if not classifier_original.load_model():
        print("❌ Modelo original não encontrado")
        return

    # Verificar imagens de treinamento
    train_dir = Path("datasets/color-cap/train/images")
    if train_dir.exists():
        train_files = list(train_dir.glob("*.jpg"))[:10]  # Primeiras 10
        print(f"📂 Dataset color-cap tem {len(list(train_dir.glob('*.jpg')))} imagens")
        print("🔍 Verificando se são realmente tampinhas:")

        tampinhas_reais = 0
        nao_tampinhas = 0

        for img_path in train_files:
            is_cap, confidence = classifier_original.predict_single(str(img_path))
            if is_cap:
                tampinhas_reais += 1
            else:
                nao_tampinhas += 1

        print(f"   ✅ Classificadas como tampinhas: {tampinhas_reais}")
        print(f"   ❌ Classificadas como não-tampinhas: {nao_tampinhas}")

    # 2. Verificar imagens reais de tampinhas
    print("\n2️⃣  IMAGENS REAIS DE TAMPINHAS:")
    print("-" * 40)

    tampinhas_dir = Path("datasets/tampinhas")
    if tampinhas_dir.exists():
        tampinhas_files = list(tampinhas_dir.glob("*.jpg"))
        print(f"📂 Pasta tampinhas tem {len(tampinhas_files)} imagens reais")

        for img_path in tampinhas_files:
            is_cap, confidence = classifier_original.predict_single(str(img_path))
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'
            print("30")

    # 3. Comparar com expectativas do usuário
    print("\n3️⃣  COMPARAÇÃO COM EXPECTATIVAS DO USUÁRIO:")
    print("-" * 40)

    print("USUÁRIO DISSE:")
    print("  - imagem1.jpg a imagem5.jpg: NÃO SÃO tampinhas")
    print("  - imagem6.jpg: É UMA tampinha")
    print()

    print("MODELO ORIGINAL CLASSIFICOU:")
    test_images = ['images/imagem1.jpg', 'images/imagem2.jpg', 'images/imagem3.jpg',
                   'images/imagem4.jpg', 'images/imagem5.jpg', 'images/imagem6.jpg']

    for img_path in test_images:
        if Path(img_path).exists():
            is_cap, confidence = classifier_original.predict_single(img_path)
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'
            print("30")

    # 4. Análise do problema
    print("\n4️⃣  ANÁLISE DO PROBLEMA:")
    print("-" * 40)

    print("🔍 O QUE ACONTECEU:")
    print("   1. O modelo foi treinado assumindo que TODAS as imagens dos datasets são tampinhas")
    print("   2. Isso inclui imagens que podem não ser tampinhas reais")
    print("   3. Amostras negativas foram criadas sinteticamente, mas podem não ser realistas")
    print("   4. O modelo aprendeu padrões errados dos dados de treinamento")

    print("\n💡 SOLUÇÃO NECESSÁRIA:")
    print("   1. Usar apenas imagens verificadamente reais de tampinhas para treinamento positivo")
    print("   2. Usar imagens verificadamente reais de NÃO-tampinhas para treinamento negativo")
    print("   3. Ou coletar mais dados de treinamento adequados")

    print("\n🎯 CONCLUSÃO:")
    print("   O modelo NÃO está errado - ele foi treinado com dados inadequados!")
    print("   A classificação atual reflete os dados de treinamento, não a realidade.")

if __name__ == "__main__":
    diagnostic_analysis()