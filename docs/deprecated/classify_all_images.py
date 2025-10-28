#!/usr/bin/env python3
"""
Classificação Completa das Imagens - É TAMPINHA OU NÃO?
"""

from evaluate_eligibility_fast import EnhancedFastClassifier
import os
from pathlib import Path

def main():
    print("🔍 CLASSIFICANDO TODAS AS IMAGENS - É TAMPINHA OU NÃO?")
    print("=" * 60)

    classifier = EnhancedFastClassifier()

    if classifier.load_model():
        print('✅ Modelo Ensemble carregado com sucesso!')
        print()

        # Pasta com imagens
        images_dir = Path("images")
        image_files = list(images_dir.glob("*.jpg"))

        print(f"📁 Encontradas {len(image_files)} imagens para classificar:")
        print("-" * 50)

        tampinhas_count = 0
        nao_tampinhas_count = 0
        results = []

        for img_path in sorted(image_files):
            if img_path.exists():
                is_cap, confidence = classifier.predict_single(str(img_path))
                result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'

                if is_cap:
                    tampinhas_count += 1
                else:
                    nao_tampinhas_count += 1

                results.append((img_path.name, result, confidence))
                print(f"{img_path.name}: {result} (confiança: {confidence:.2f})")
            else:
                print(f"{img_path.name}: ❌ ARQUIVO NÃO ENCONTRADO")

        print()
        print("📊 RESULTADO FINAL:")
        print("-" * 30)
        print(f"✅ Tampinhas detectadas: {tampinhas_count}")
        print(f"❌ Não são tampinhas: {nao_tampinhas_count}")
        print(f"📁 Total de imagens: {len(image_files)}")

        if tampinhas_count > nao_tampinhas_count:
            print("\n🎉 MAIORIA DAS IMAGENS SÃO TAMPINHAS!")
        elif nao_tampinhas_count > tampinhas_count:
            print("\n⚠️  MAIORIA DAS IMAGENS NÃO SÃO TAMPINHAS!")
        else:
            print("\n⚖️  METADE SÃO TAMPINHAS, METADE NÃO!")

        print("\n📋 DETALHES POR IMAGEM:")
        print("-" * 40)
        for img_name, result, confidence in results:
            print(f"{img_name}: {result} (confiança: {confidence:.2f})")

    else:
        print('❌ Erro ao carregar modelo')

if __name__ == "__main__":
    main()