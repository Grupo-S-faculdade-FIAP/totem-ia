#!/usr/bin/env python3
"""
Download Color-CAP Dataset from Kaggle
======================================

Este script baixa o dataset color-cap do Kaggle usando kagglehub.
O dataset contém imagens de tampinhas coloridas para treinamento de modelos de IA.
"""

import kagglehub
import os
import shutil
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def download_color_cap_dataset():
    """
    Baixa o dataset color-cap do Kaggle e organiza na estrutura esperada.
    """
    try:
        logger.info("📥 Baixando dataset color-cap do Kaggle...")

        # Download do dataset
        path = kagglehub.dataset_download("artemsmetanin/color-cap")

        logger.info(f"✅ Dataset baixado para: {path}")

        # Verificar conteúdo baixado
        downloaded_path = Path(path)
        if not downloaded_path.exists():
            logger.error(f"❌ Caminho baixado não existe: {path}")
            return False

        # Listar conteúdo
        logger.info("📂 Conteúdo baixado:")
        for item in downloaded_path.iterdir():
            if item.is_dir():
                file_count = len(list(item.glob("*")))
                logger.info(f"  📁 {item.name}/ ({file_count} arquivos)")
            else:
                logger.info(f"  📄 {item.name}")

        # Verificar se tem a estrutura esperada
        expected_dirs = ["train", "valid", "test"]
        found_dirs = [d for d in downloaded_path.iterdir() if d.is_dir() and d.name in expected_dirs]

        if found_dirs:
            logger.info("✅ Estrutura de diretórios encontrada!")

            # Mover para datasets/color-cap/
            target_path = Path("datasets/color-cap")
            target_path.mkdir(parents=True, exist_ok=True)

            for src_dir in found_dirs:
                dst_dir = target_path / src_dir.name
                if dst_dir.exists():
                    logger.warning(f"⚠️  Diretório já existe: {dst_dir}, pulando...")
                    continue

                logger.info(f"📋 Copiando {src_dir.name} para {dst_dir}")
                shutil.copytree(src_dir, dst_dir)

            logger.info("✅ Dataset organizado com sucesso!")
            logger.info(f"📍 Localização final: {target_path.absolute()}")

            # Verificar se tem imagens
            total_images = 0
            for split in ["train", "valid", "test"]:
                split_path = target_path / split / "images"
                if split_path.exists():
                    images = list(split_path.glob("*.jpg")) + list(split_path.glob("*.png"))
                    total_images += len(images)
                    logger.info(f"  {split}: {len(images)} imagens")

            logger.info(f"📊 Total de imagens encontradas: {total_images}")

            if total_images > 0:
                logger.info("🎉 Dataset pronto para uso!")
                return True
            else:
                logger.warning("⚠️  Nenhuma imagem encontrada. Verifique a estrutura do dataset.")
                return False

        else:
            logger.warning("⚠️  Estrutura esperada não encontrada. Dataset pode ter estrutura diferente.")
            logger.info("💡 Você pode mover manualmente os arquivos para datasets/color-cap/")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao baixar dataset: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎨 COLOR-CAP DATASET DOWNLOADER")
    print("   Download from Kaggle using kagglehub")
    print("=" * 60)

    success = download_color_cap_dataset()

    if success:
        print("\n✅ Dataset baixado e organizado com sucesso!")
        print("🚀 Agora você pode executar o treinamento:")
        print("   python src/models_trainers/svm_complete_classifier.py")
    else:
        print("\n❌ Problema no download. Verifique os logs acima.")
        print("💡 Possíveis soluções:")
        print("   1. Verifique sua conexão com a internet")
        print("   2. Certifique-se de ter permissões para escrever arquivos")
        print("   3. O dataset pode ter mudado de estrutura no Kaggle")