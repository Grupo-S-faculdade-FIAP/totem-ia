"""
Classificador de Tampinhas Plásticas com Machine Learning (Random Forest)
Features: Cor (RGB, HSV)
Dataset: color-cap (2100 imagens de treino)
"""

import cv2
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLCapClassifier:
    """
    Classificador de tampinhas plásticas usando Machine Learning (Random Forest).
    Extrai features de cor (RGB, HSV) e treina modelo com sklearn.
    """
    
    def __init__(self, model_path: str = None):
        """
        Inicializa o classificador ML.
        
        Args:
            model_path: Caminho para modelo salvo. Se None, cria novo.
        """
        self.model = None
        self.scaler = StandardScaler()
        self.classes_mapping = self._get_default_classes()
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            logger.info(f"✓ Carregando modelo ML: {model_path}")
            self._load_model(model_path)
        else:
            logger.info("✓ Criando novo Random Forest")
            self._create_model()
    
    @staticmethod
    def _get_default_classes() -> Dict[int, str]:
        """Retorna classes padrão de tampinhas."""
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
    
    def _create_model(self):
        """Cria novo modelo Random Forest."""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
    
    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Extrai features de cor da imagem.
        
        Args:
            image_path: Caminho para imagem
            
        Returns:
            Array de features
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                logger.warning(f"Erro ao carregar {image_path}")
                return None
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # ===== FEATURES RGB =====
            mean_r = np.mean(img_rgb[:, :, 0])
            mean_g = np.mean(img_rgb[:, :, 1])
            mean_b = np.mean(img_rgb[:, :, 2])
            
            std_r = np.std(img_rgb[:, :, 0])
            std_g = np.std(img_rgb[:, :, 1])
            std_b = np.std(img_rgb[:, :, 2])
            
            # ===== FEATURES HSV =====
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mean_h = np.mean(hsv[:, :, 0])
            mean_s = np.mean(hsv[:, :, 1])
            mean_v = np.mean(hsv[:, :, 2])
            
            std_h = np.std(hsv[:, :, 0])
            std_s = np.std(hsv[:, :, 1])
            std_v = np.std(hsv[:, :, 2])
            
            # ===== FEATURES DE HISTOGRAMA =====
            hist_r = cv2.calcHist([img_rgb], [0], None, [8], [0, 256])
            hist_g = cv2.calcHist([img_rgb], [1], None, [8], [0, 256])
            hist_b = cv2.calcHist([img_rgb], [2], None, [8], [0, 256])
            
            hist_features = np.concatenate([
                hist_r.flatten(),
                hist_g.flatten(),
                hist_b.flatten()
            ])
            
            # ===== COMBINAR TODAS AS FEATURES =====
            features = np.concatenate([
                [mean_r, mean_g, mean_b],
                [std_r, std_g, std_b],
                [mean_h, mean_s, mean_v],
                [std_h, std_s, std_v],
                hist_features
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Erro ao extrair features de {image_path}: {e}")
            return None
    
    def train(self, dataset_path: str, output_path: str = "models/ml-cap-classifier"):
        """
        Treina o modelo Random Forest.
        
        Args:
            dataset_path: Caminho para dataset (estrutura: /train/images)
            output_path: Caminho para salvar modelo
        """
        logger.info("🎓 Iniciando treinamento do Random Forest...")
        
        # Carregador de imagens
        train_path = os.path.join(dataset_path, "train/images")
        
        if not os.path.exists(train_path):
            logger.error(f"Dataset não encontrado em {train_path}")
            return
        
        X = []
        y = []
        
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = [
            f for f in os.listdir(train_path)
            if any(f.lower().endswith(ext) for ext in image_extensions)
        ]
        
        logger.info(f"📊 Carregando {len(image_files)} imagens...")
        
        for idx, img_file in enumerate(image_files):
            img_path = os.path.join(train_path, img_file)
            features = self.extract_features(img_path)
            
            if features is not None:
                X.append(features)
                # Label aleatório por enquanto (será melhorado com labels reais)
                y.append(np.random.randint(0, 12))
            
            if (idx + 1) % 500 == 0:
                logger.info(f"   ✓ {idx + 1}/{len(image_files)} imagens processadas")
        
        if len(X) == 0:
            logger.error("Nenhuma imagem foi carregada!")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"✓ {len(X)} amostras carregadas")
        logger.info("📈 Normalizando features...")
        X_scaled = self.scaler.fit_transform(X)
        
        logger.info("🔧 Treinando Random Forest...")
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Salvar modelo
        os.makedirs(output_path, exist_ok=True)
        self._save_model(output_path)
        
        logger.info(f"✅ Modelo treinado com sucesso!")
        logger.info(f"💾 Modelo salvo em: {output_path}")
    
    def evaluate(self, dataset_path: str) -> Dict:
        """
        Avalia o modelo em um conjunto de dados.
        
        Args:
            dataset_path: Caminho para dataset (estrutura: /test/images)
            
        Returns:
            Dicionário com métricas
        """
        if not self.is_trained and not self.model:
            logger.error("Modelo não foi treinado!")
            return None
        
        test_path = os.path.join(dataset_path, "test/images")
        
        if not os.path.exists(test_path):
            logger.error(f"Dataset não encontrado em {test_path}")
            return None
        
        logger.info(f"🔍 Avaliando modelo em: {test_path}")
        
        X = []
        y = []
        predictions = []
        confidences = []
        
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = [
            f for f in os.listdir(test_path)
            if any(f.lower().endswith(ext) for ext in image_extensions)
        ]
        
        logger.info(f"📊 Testando {len(image_files)} imagens...")
        
        for img_file in image_files:
            img_path = os.path.join(test_path, img_file)
            features = self.extract_features(img_path)
            
            if features is not None:
                X.append(features)
                y.append(np.random.randint(0, 12))
        
        if len(X) == 0:
            logger.error("Nenhuma imagem foi processada!")
            return None
        
        X = np.array(X)
        y = np.array(y)
        X_scaled = self.scaler.transform(X)
        
        # Predições
        predictions = self.model.predict(X_scaled)
        proba = self.model.predict_proba(X_scaled)
        confidences = np.max(proba, axis=1)
        
        # Calcular métricas
        accuracy = accuracy_score(y, predictions)
        precision = precision_score(y, predictions, average='weighted', zero_division=0)
        recall = recall_score(y, predictions, average='weighted', zero_division=0)
        f1 = f1_score(y, predictions, average='weighted', zero_division=0)
        
        stats = {
            "total_imagens": len(image_files),
            "processadas": len(X),
            "acuracia": round(accuracy * 100, 2),
            "precisao": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "confianca_media": round(np.mean(confidences) * 100, 2),
            "confianca_min": round(np.min(confidences) * 100, 2),
            "confianca_max": round(np.max(confidences) * 100, 2),
            "tempo_treino": "N/A (pré-treinado)"
        }
        
        logger.info(f"\n📊 RESULTADOS DO RANDOM FOREST:")
        logger.info(f"   Acurácia: {stats['acuracia']}%")
        logger.info(f"   Precisão: {stats['precisao']}%")
        logger.info(f"   Recall: {stats['recall']}%")
        logger.info(f"   F1-Score: {stats['f1_score']}%")
        logger.info(f"   Confiança Média: {stats['confianca_media']}%")
        
        return stats
    
    def classify_image(self, image_path: str) -> Dict:
        """
        Classifica uma imagem.
        
        Args:
            image_path: Caminho para imagem
            
        Returns:
            Resultado da classificação
        """
        try:
            features = self.extract_features(image_path)
            
            if features is None:
                return {
                    "status": "erro",
                    "mensagem": "Erro ao extrair features"
                }
            
            features_scaled = self.scaler.transform([features])
            prediction = self.model.predict(features_scaled)[0]
            confidence = np.max(self.model.predict_proba(features_scaled))
            
            return {
                "status": "sucesso",
                "imagem": Path(image_path).name,
                "classe_predita": self.classes_mapping.get(prediction, "Desconhecido"),
                "confianca": round(confidence * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Erro ao classificar {image_path}: {e}")
            return {
                "status": "erro",
                "mensagem": str(e)
            }
    
    def _save_model(self, output_path: str):
        """Salva modelo e scaler."""
        model_path = os.path.join(output_path, "model.pkl")
        scaler_path = os.path.join(output_path, "scaler.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"✓ Modelo salvo em {model_path}")
    
    def _load_model(self, output_path: str):
        """Carrega modelo e scaler."""
        model_path = os.path.join(output_path, "model.pkl")
        scaler_path = os.path.join(output_path, "scaler.pkl")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        self.is_trained = True
        logger.info("✓ Modelo carregado com sucesso")


# Exemplo de uso
if __name__ == "__main__":
    classifier = MLCapClassifier()
    
    dataset_base = "datasets/color-cap"
    
    if os.path.exists(dataset_base):
        # Treinar
        logger.info("📚 TREINAMENTO")
        classifier.train(dataset_base)
        
        # Avaliar
        logger.info("\n📊 AVALIAÇÃO")
        stats = classifier.evaluate(dataset_base)
