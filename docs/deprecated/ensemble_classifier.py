#!/usr/bin/env python3
"""
Ensemble Classifier - Combina SVM + ResNet50
Sistema de Classificação: É TAMPINHA? SIM ou NÃO

Estratégia: Voting Ensemble
- SVM: 40% de peso
- ResNet: 60% de peso
"""

import logging
from pathlib import Path
import numpy as np
from svm_classifier import SVMCapClassifier
from resnet_classifier import ResNetCapClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class EnsembleCapClassifier:
    def __init__(self):
        self.svm = SVMCapClassifier()
        self.resnet = ResNetCapClassifier()
        self.svm_loaded = False
        self.resnet_loaded = False

    def load_models(self):
        """Carrega ambos os modelos"""
        logger.info("Carregando modelos para Ensemble...")

        self.svm_loaded = self.svm.load_model()
        self.resnet_loaded = self.resnet.load_model()

        if self.svm_loaded:
            logger.info("✅ SVM carregado com sucesso!")
        else:
            logger.warning("⚠️  SVM não encontrado")

        if self.resnet_loaded:
            logger.info("✅ ResNet carregado com sucesso!")
        else:
            logger.warning("⚠️  ResNet não encontrado")

        return self.svm_loaded or self.resnet_loaded

    def predict_single(self, image_path):
        """
        Faz predição com Ensemble Voting
        Combina predições de SVM (40%) e ResNet (60%)
        """
        results = []
        confidences = []

        # Predição SVM (40% peso)
        if self.svm_loaded:
            is_cap_svm, conf_svm = self.svm.predict_single(image_path)
            results.append(int(is_cap_svm))
            confidences.append((conf_svm, 0.4))  # (confiança, peso)

        # Predição ResNet (60% peso)
        if self.resnet_loaded:
            is_cap_resnet, conf_resnet = self.resnet.predict_single(image_path)
            results.append(int(is_cap_resnet))
            confidences.append((conf_resnet, 0.6))  # (confiança, peso)

        if not results:
            return False, 0.0

        # Combinar predições com pesos
        weighted_score = 0.0
        for conf, weight in confidences:
            weighted_score += conf * weight

        # Predição final: média ponderada
        is_cap = weighted_score > 0.5

        return is_cap, float(weighted_score)

def main():
    print("\n" + "=" * 70)
    print("🔀 ENSEMBLE CLASSIFIER - SVM + RESNET50")
    print("Sistema de Classificação: É TAMPINHA? SIM ou NÃO")
    print("=" * 70)

    ensemble = EnsembleCapClassifier()

    if not ensemble.load_models():
        print("\n❌ Erro: Nenhum modelo encontrado!")
        print("\nExecute primeiro:")
        print("  python svm_classifier.py")
        print("  python resnet_classifier.py")
        return

    print("\n✅ Modelos carregados com sucesso!")
    print("   - SVM: 40% de peso")
    print("   - ResNet: 60% de peso\n")

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
            is_cap, confidence = ensemble.predict_single(str(img_path))
            
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
