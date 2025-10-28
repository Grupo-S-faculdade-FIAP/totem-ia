#!/usr/bin/env python3
"""
Teste do Modelo Ensemble Melhorado
"""

from evaluate_eligibility_fast import EnhancedFastClassifier
import os

def main():
    print("🔍 Testando Modelo Ensemble Melhorado")
    print("=" * 50)

    classifier = EnhancedFastClassifier()

    if classifier.load_model():
        print('✅ Modelo carregado com sucesso!')

        # Testar algumas imagens
        test_images = ['images/imagem1.jpg', 'images/imagem2.jpg', 'images/imagem3.jpg']

        print("\n🖼️  Testando imagens:")
        print("-" * 30)

        for img_path in test_images:
            if os.path.exists(img_path):
                is_cap, confidence = classifier.predict_single(img_path)
                result = 'TAMPINHA' if is_cap else 'NÃO É TAMPINHA'
                print(f'{img_path}: {result} (confiança: {confidence:.3f})')
            else:
                print(f'{img_path}: Arquivo não encontrado')

        print("\n✅ Teste concluído!")
    else:
        print('❌ Erro ao carregar modelo')

if __name__ == "__main__":
    main()