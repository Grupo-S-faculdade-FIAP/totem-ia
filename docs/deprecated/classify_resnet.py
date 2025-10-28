#!/usr/bin/env python3
"""
Classificação de Imagens - ResNet50 Classifier
Testa o modelo ResNet50 em todas as imagens da pasta /images
"""

from resnet_classifier import ResNetCapClassifier
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("\n" + "=" * 70)
    print("🔍 CLASSIFICANDO IMAGENS COM RESNET50")
    print("Sistema: É TAMPINHA? SIM ou NÃO")
    print("=" * 70)

    classifier = ResNetCapClassifier()

    if not classifier.load_model():
        print("❌ Erro: Modelo não encontrado. Execute 'python resnet_classifier.py' primeiro!")
        return

    print("✅ Modelo ResNet50 carregado com sucesso!\n")

    # Classificar imagens
    images_dir = Path("images")
    image_files = sorted(list(images_dir.glob("*.jpg")))

    if not image_files:
        print("❌ Nenhuma imagem encontrada em /images/")
        return

    print(f"📁 Encontradas {len(image_files)} imagens para classificar:")
    print("-" * 70)

    tampinhas_count = 0
    nao_tampinhas_count = 0
    results = []

    for img_path in image_files:
        if img_path.exists():
            is_cap, confidence = classifier.predict_single(str(img_path))
            
            if is_cap:
                result = '✅ TAMPINHA'
                tampinhas_count += 1
            else:
                result = '❌ NÃO É TAMPINHA'
                nao_tampinhas_count += 1

            results.append((img_path.name, result, confidence))
            print(f"{img_path.name:<15} {result:<20} (confiança: {confidence:.2f})")

    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL:")
    print("-" * 70)
    print(f"✅ Tampinhas detectadas: {tampinhas_count}")
    print(f"❌ Não são tampinhas: {nao_tampinhas_count}")
    print(f"📁 Total de imagens: {len(image_files)}")

    if tampinhas_count > nao_tampinhas_count:
        print("\n🎉 MAIORIA DAS IMAGENS SÃO TAMPINHAS!")
    elif nao_tampinhas_count > tampinhas_count:
        print("\n⚠️  MAIORIA DAS IMAGENS NÃO SÃO TAMPINHAS!")
    else:
        print("\n⚖️  METADE SÃO TAMPINHAS, METADE NÃO!")

    # Detalhes
    print("\n" + "=" * 70)
    print("📋 DETALHES POR IMAGEM:")
    print("-" * 70)
    for img_name, result, confidence in results:
        print(f"{img_name:<15} {result:<20} (confiança: {confidence:.2f})")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
