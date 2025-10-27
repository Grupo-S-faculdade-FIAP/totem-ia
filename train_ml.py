"""
Treinamento do Random Forest para Tampinhas Plásticas
Script de ML para comparação com ViT
"""

import os
import json
import logging
import time
import pickle
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import cv2
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_features(image_path: str) -> np.ndarray:
    """
    Extrai features de cor da imagem.
    
    Features:
    - RGB mean/std (6 features)
    - HSV mean/std (6 features)
    - Histogramas (24 features)
    Total: 36 features
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Não conseguiu ler: {image_path}")
            return np.zeros(36)
        
        # RGB features (B, G, R em OpenCV)
        rgb_mean = img.mean(axis=(0, 1))  # shape: (3,)
        rgb_std = img.std(axis=(0, 1))    # shape: (3,)
        
        # HSV features
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv_mean = hsv.mean(axis=(0, 1))  # shape: (3,)
        hsv_std = hsv.std(axis=(0, 1))    # shape: (3,)
        
        # Histogramas (8 bins por canal)
        hist_features = []
        for channel in range(3):
            hist = cv2.calcHist([img], [channel], None, [8], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            hist_features.extend(hist)
        hist_features = np.array(hist_features)  # shape: (24,)
        
        # Concatenar features
        features = np.concatenate([rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features])
        
        return features
        
    except Exception as e:
        logger.error(f"Erro ao extrair features de {image_path}: {e}")
        return np.zeros(36)


def load_data(dataset_path: str, split: str = "train") -> tuple:
    """
    Carrega imagens e labels de um split do dataset.
    
    Args:
        dataset_path: Caminho base do dataset
        split: "train", "valid", ou "test"
    
    Returns:
        (X, y) - Features e labels
    """
    X, y = [], []
    
    # Mapeamento de cores para indices
    color_mapping = {
        "Vermelho": 0, "Azul": 1, "Verde": 2, "Amarelo": 3,
        "Branco": 4, "Preto": 5, "Laranja": 6, "Rosa": 7,
        "Roxo": 8, "Marrom": 9, "Cinza": 10, "Transparente": 11
    }
    
    split_path = os.path.join(dataset_path, split, "images")
    
    if not os.path.exists(split_path):
        logger.warning(f"Path não existe: {split_path}")
        return np.array([]), np.array([])
    
    image_files = sorted(list(Path(split_path).glob("*.jpg")) + 
                        list(Path(split_path).glob("*.jpeg")) + 
                        list(Path(split_path).glob("*.png")))
    
    logger.info(f"📊 Carregando {len(image_files)} imagens de {split}")
    
    for img_path in tqdm(image_files, desc=f"Carregando {split}"):
        try:
            features = extract_features(str(img_path))
            
            # Extrair label do nome do arquivo (ex: "Vermelho_0.jpg")
            filename = img_path.stem
            color_name = filename.rsplit('_', 1)[0]
            label = color_mapping.get(color_name, 0)
            
            X.append(features)
            y.append(label)
        except Exception as e:
            logger.error(f"Erro ao processar {img_path}: {e}")
    
    return np.array(X), np.array(y)


class MLCapClassifier:
    """Classifier usando Random Forest."""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 20):
        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_time = 0
        
        self.class_names = {
            0: "Vermelho", 1: "Azul", 2: "Verde", 3: "Amarelo",
            4: "Branco", 5: "Preto", 6: "Laranja", 7: "Rosa",
            8: "Roxo", 9: "Marrom", 10: "Cinza", 11: "Transparente"
        }
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Treina o classificador."""
        logger.info("🎯 Treinando Random Forest...")
        
        start_time = time.time()
        
        # Normalizar
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Treinar
        self.classifier.fit(X_scaled, y_train)
        
        self.training_time = time.time() - start_time
        self.is_trained = True
        
        logger.info(f"✓ Treinamento concluído em {self.training_time:.2f}s")
        logger.info(f"  Amostras: {len(X_train)}")
        logger.info(f"  Acurácia no treino: {self.classifier.score(X_scaled, y_train):.4f}")
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Avalia o classificador."""
        if not self.is_trained:
            logger.error("Classificador não foi treinado")
            return {}
        
        X_scaled = self.scaler.transform(X_test)
        y_pred = self.classifier.predict(X_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "test_samples": len(X_test),
            "training_time": self.training_time
        }
        
        logger.info(f"📊 Métricas de Teste:")
        logger.info(f"   Acurácia:  {accuracy:.4f}")
        logger.info(f"   Precisão:  {precision:.4f}")
        logger.info(f"   Recall:    {recall:.4f}")
        logger.info(f"   F1-Score:  {f1:.4f}")
        
        return metrics
    
    def save(self, output_dir: str):
        """Salva modelo e scaler."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Salvar modelo
        with open(os.path.join(output_dir, "classifier.pkl"), 'wb') as f:
            pickle.dump(self.classifier, f)
        
        # Salvar scaler
        with open(os.path.join(output_dir, "scaler.pkl"), 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Salvar classes
        with open(os.path.join(output_dir, "classes.json"), 'w') as f:
            json.dump({str(k): v for k, v in self.class_names.items()}, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Modelo salvo em: {output_dir}")


def main():
    """Main function para treinar Random Forest."""
    logger.info("🎨 Random Forest para Tampinhas Plásticas")
    logger.info("=" * 60)
    
    dataset_base = "datasets/color-cap"
    output_dir = "models/ml-cap-classifier"
    
    # Carregar dados
    logger.info("\n📂 Carregando datasets...")
    X_train, y_train = load_data(dataset_base, "train")
    X_valid, y_valid = load_data(dataset_base, "valid")
    X_test, y_test = load_data(dataset_base, "test")
    
    if len(X_train) == 0:
        logger.error("Nenhuma imagem de treino encontrada!")
        return
    
    logger.info(f"✓ Treino: {len(X_train)} imagens")
    logger.info(f"✓ Validação: {len(X_valid)} imagens")
    logger.info(f"✓ Teste: {len(X_test)} imagens")
    
    # Inicializar e treinar
    classifier = MLCapClassifier()
    classifier.train(X_train, y_train)
    
    # Avaliar em validação
    logger.info("\n📊 Avaliando em Validação...")
    val_metrics = classifier.evaluate(X_valid, y_valid)
    
    # Avaliar em teste
    logger.info("\n📊 Avaliando em Teste...")
    test_metrics = classifier.evaluate(X_test, y_test)
    
    # Salvar modelo
    classifier.save(output_dir)
    
    # Salvar métricas
    metrics_file = os.path.join(output_dir, "metrics.json")
    all_metrics = {
        "validation": val_metrics,
        "test": test_metrics,
        "model_info": {
            "type": "Random Forest",
            "n_estimators": 100,
            "max_depth": 20,
            "features": 36,
            "n_classes": 12
        }
    }
    
    with open(metrics_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"✅ Treinamento do Random Forest concluído!")
    logger.info(f"   Tempo total: {classifier.training_time:.2f} segundos")
    logger.info(f"   Métricas salvas em: {metrics_file}")


if __name__ == "__main__":
    main()
