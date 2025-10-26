"""
Classificador de Tampinhas Plásticas
Usando Vision Transformer (ViT) fine-tuned com dataset do Kaggle
Dataset: color-cap (2100 imagens de treino + 200 validação + 100 teste)
"""

import torch
import torch.nn as nn
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import numpy as np
from pathlib import Path
import json
import logging
from typing import Dict, List, Tuple, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapClassifier:
    """
    Classificador de tampinhas plásticas usando Vision Transformer.
    Detecta cores e características de tampinhas plásticas.
    """
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        Inicializa o classificador.
        
        Args:
            model_path: Caminho para modelo fine-tuned. Se None, usa modelo pré-treinado.
            device: 'cuda' ou 'cpu'. Auto-detecta se None.
        """
        # Detectar dispositivo
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        logger.info(f"✓ Usando dispositivo: {self.device}")
        
        # Carregar processador e modelo base
        self.model_name = "google/vit-base-patch16-224"
        self.processor = ViTImageProcessor.from_pretrained(self.model_name)
        
        # Carregar modelo pré-treinado ou fine-tuned
        if model_path and os.path.exists(model_path):
            logger.info(f"✓ Carregando modelo fine-tuned: {model_path}")
            self.model = ViTForImageClassification.from_pretrained(model_path)
            # Carregar mapeamento de classes
            config_path = os.path.join(model_path, 'classes.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.classes = json.load(f)
            else:
                self.classes = self._get_default_classes()
        else:
            logger.info("✓ Usando modelo base ViT pré-treinado ImageNet")
            self.model = ViTForImageClassification.from_pretrained(
                self.model_name,
                num_labels=len(self._get_default_classes())
            )
            self.classes = self._get_default_classes()
        
        self.model.to(self.device)
        self.model.eval()
        
    @staticmethod
    def _get_default_classes() -> Dict[int, str]:
        """Retorna classes padrão de tampinhas plásticas."""
        return {
            0: "Vermelho",
            1: "Azul",
            2: "Verde",
            3: "Amarelo",
            4: "Branco",
            5: "Preto",
            6: "Laranja",
            7: "Rosa",
            8: "Roxo",
            9: "Marrom",
            10: "Cinza",
            11: "Transparente"
        }
    
    def classify_image(self, image_path: str) -> Dict:
        """
        Classifica uma imagem de tampinha.
        
        Args:
            image_path: Caminho para a imagem
            
        Returns:
            Dict com resultados da classificação
        """
        try:
            # Carregar e processar imagem
            image = Image.open(image_path).convert('RGB')
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            # Realizar inferência
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                confidence, predicted_class = torch.max(probabilities, dim=1)
                
            predicted_idx = predicted_class.item()
            confidence_score = confidence.item()
            predicted_label = self.classes.get(predicted_idx, "Desconhecido")
            
            # Obter top-3 predições
            top3_probs, top3_indices = torch.topk(probabilities, k=3, dim=1)
            top3_results = [
                {
                    "classe": self.classes.get(idx.item(), "Desconhecido"),
                    "confianca": prob.item()
                }
                for prob, idx in zip(top3_probs[0], top3_indices[0])
            ]
            
            return {
                "status": "sucesso",
                "imagem": Path(image_path).name,
                "classe_predita": predicted_label,
                "confianca": round(confidence_score * 100, 2),
                "top3": top3_results,
                "dispositivo": self.device
            }
            
        except Exception as e:
            logger.error(f"Erro ao classificar {image_path}: {str(e)}")
            return {
                "status": "erro",
                "mensagem": str(e)
            }
    
    def classify_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Classifica múltiplas imagens.
        
        Args:
            image_paths: Lista de caminhos de imagens
            
        Returns:
            Lista de resultados
        """
        results = []
        for image_path in image_paths:
            result = self.classify_image(image_path)
            results.append(result)
        return results
    
    def evaluate_dataset(self, dataset_path: str) -> Dict:
        """
        Avalia o modelo em um dataset.
        
        Args:
            dataset_path: Caminho para diretório com imagens
            
        Returns:
            Estatísticas de avaliação
        """
        logger.info(f"🔍 Avaliando dataset em: {dataset_path}")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
        image_paths = [
            str(p) for p in Path(dataset_path).rglob('*')
            if p.suffix.lower() in image_extensions
        ]
        
        if not image_paths:
            logger.warning(f"Nenhuma imagem encontrada em {dataset_path}")
            return {"status": "erro", "mensagem": "Nenhuma imagem encontrada"}
        
        logger.info(f"📊 Processando {len(image_paths)} imagens...")
        results = self.classify_batch(image_paths)
        
        # Compilar estatísticas
        successful = [r for r in results if r["status"] == "sucesso"]
        failed = [r for r in results if r["status"] == "erro"]
        
        class_distribution = {}
        confidence_scores = []
        
        for result in successful:
            classe = result["classe_predita"]
            class_distribution[classe] = class_distribution.get(classe, 0) + 1
            confidence_scores.append(result["confianca"])
        
        stats = {
            "total_imagens": len(image_paths),
            "processadas": len(successful),
            "erros": len(failed),
            "distribuicao_classes": class_distribution,
            "confianca_media": round(np.mean(confidence_scores), 2) if confidence_scores else 0,
            "confianca_min": round(min(confidence_scores), 2) if confidence_scores else 0,
            "confianca_max": round(max(confidence_scores), 2) if confidence_scores else 0
        }
        
        return stats


# Exemplo de uso
if __name__ == "__main__":
    # Inicializar classificador
    classifier = CapClassifier()
    
    # Exemplo com uma imagem
    dataset_base = "datasets/color-cap"
    
    if os.path.exists(dataset_base):
        # Avaliar dataset de teste
        test_path = os.path.join(dataset_base, "test/images")
        if os.path.exists(test_path):
            logger.info("📸 Avaliando dataset de teste...")
            stats = classifier.evaluate_dataset(test_path)
            logger.info(f"Resultados: {json.dumps(stats, indent=2, ensure_ascii=False)}")
