#!/usr/bin/env python3
"""
SVM Classifier - Classificação de Tampinhas
Sistema de Classificação: É TAMPINHA? SIM ou NÃO

Modelo: Support Vector Machine com RBF Kernel
Otimizado para dataset pequeno (4 tampinhas + 14 não-tampinhas)
"""

import os
import cv2
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import joblib
import logging
from tqdm import tqdm
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class SVMCapClassifier:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = Path("models/svm")
        self.model_path.mkdir(parents=True, exist_ok=True)

    def extract_color_features(self, image_path):
        """
        Extrai 24 features otimizadas para classificação de tampinhas
        Focado em cor, forma e textura
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return None

            image = cv2.resize(image, (128, 128))

            features = []

            # ========== ESTATÍSTICAS RGB (9 features) ==========
            for channel in cv2.split(image):
                features.extend([
                    np.mean(channel),
                    np.std(channel),
                    np.median(channel)
                ])

            # ========== ESTATÍSTICAS HSV (9 features) ==========
            # HSV é mais robusto para cores
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            for channel in cv2.split(hsv):
                features.extend([
                    np.mean(channel),
                    np.std(channel),
                    np.median(channel)
                ])

            # ========== FORMA (6 features) ==========
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                
                # Circularidade (tampinhas são circulares!)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                
                # Razão de aspecto
                x, y, w, h = cv2.boundingRect(largest_contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Solidez
                hull = cv2.convexHull(largest_contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                features.extend([
                    area/10000,
                    perimeter/1000,
                    circularity,
                    aspect_ratio,
                    solidity,
                    hull_area/10000
                ])
            else:
                features.extend([0, 0, 0, 0, 0, 0])

            return np.array(features)

        except Exception as e:
            logger.warning(f"Erro ao extrair features de {image_path}: {e}")
            return None

    def load_dataset(self):
        """Carrega dataset com data augmentation sintético"""
        logger.info("Carregando dataset para SVM...")

        all_features = []
        all_labels = []

        # ========== 1. POSITIVAS: Tampinhas reais ==========
        tampinhas_dir = Path("datasets/tampinhas")
        if tampinhas_dir.exists():
            tampinhas_files = list(tampinhas_dir.glob("*"))
            logger.info(f"Encontradas {len(tampinhas_files)} tampinhas reais")

            for img_path in tqdm(tampinhas_files, desc="Tampinhas reais"):
                features = self.extract_color_features(img_path)
                if features is not None:
                    all_features.append(features)
                    all_labels.append(1)  # TAMPINHA

            # Data augmentation sintético para tampinhas
            if all_features:
                logger.info("Gerando variações sintéticas de tampinhas...")
                positive_features = all_features.copy()
                
                for _ in range(50):  # 50 variações por imagem original
                    base = positive_features[np.random.randint(len(positive_features))]
                    
                    # Adicionar ruído pequeno para simular variações
                    noise = np.random.normal(0, 0.08, len(base))
                    varied = base + noise
                    varied = np.clip(varied, 0, 255)
                    
                    all_features.append(varied)
                    all_labels.append(1)

        # ========== 2. NEGATIVAS: Não-tampinhas ==========
        nao_tampinhas_dir = Path("datasets/nao-tampinhas")
        if nao_tampinhas_dir.exists():
            nao_tampinhas_files = list(nao_tampinhas_dir.glob("*"))
            logger.info(f"Encontradas {len(nao_tampinhas_files)} não-tampinhas")

            negative_features = []
            for img_path in tqdm(nao_tampinhas_files, desc="Não-tampinhas"):
                features = self.extract_color_features(img_path)
                if features is not None:
                    all_features.append(features)
                    all_labels.append(0)  # NÃO TAMPINHA
                    negative_features.append(features)

            # Data augmentation sintético para não-tampinhas
            if negative_features:
                logger.info("Gerando variações sintéticas de não-tampinhas...")
                
                for _ in range(30):  # 30 variações por imagem original
                    base = negative_features[np.random.randint(len(negative_features))]
                    
                    noise = np.random.normal(0, 0.08, len(base))
                    varied = base + noise
                    varied = np.clip(varied, 0, 255)
                    
                    all_features.append(varied)
                    all_labels.append(0)

        X = np.array(all_features)
        y = np.array(all_labels)

        logger.info(f"✅ Dataset carregado: {X.shape[0]} amostras, {X.shape[1]} features")
        logger.info(f"   Tampinhas: {np.sum(y == 1)}, Não-tampinhas: {np.sum(y == 0)}")

        return X, y

    def train_model(self, X_train, y_train):
        """Treina o SVM com validação cruzada"""
        logger.info("Iniciando treinamento do SVM...")

        # Normalizar features
        logger.info("Normalizando features...")
        X_scaled = self.scaler.fit_transform(X_train)

        # Criar SVM com RBF Kernel (melhor para dados pequenos)
        self.model = SVC(
            kernel='rbf',           # RBF kernel para decisões não-lineares
            C=100,                  # Regularização (maior = menos regularização)
            gamma='scale',          # Kernel coefficient
            class_weight='balanced',  # Balanceia classes desiguais
            probability=True,       # Habilita predict_proba
            random_state=42
        )

        # Treinar modelo
        logger.info("Treinando SVM com RBF kernel...")
        self.model.fit(X_scaled, y_train)

        # Validação cruzada
        logger.info("Executando validação cruzada (5-Fold)...")
        cv_scores = cross_val_score(
            self.model,
            X_scaled,
            y_train,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring='accuracy'
        )

        logger.info(f"✅ Acurácia CV: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

        return cv_scores

    def evaluate_model(self, X_test, y_test):
        """Avalia o modelo no conjunto de teste"""
        logger.info("Avaliando modelo...")

        X_scaled = self.scaler.transform(X_test)

        # Predições
        y_pred = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)[:, 1]

        # Métricas
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DE AVALIAÇÃO")
        print("=" * 60)

        print("\nRelatório de Classificação:")
        print(classification_report(y_test, y_pred, target_names=['NÃO TAMPINHA', 'TAMPINHA']))

        print("Matriz de Confusão:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"  NÃO-TAMPINHA: {cm[0]} (Acertos: {cm[0, 0]}, Erros: {cm[0, 1]})")
        print(f"  TAMPINHA:     {cm[1]} (Acertos: {cm[1, 1]}, Erros: {cm[1, 0]})")

        # ROC-AUC
        try:
            roc_auc = roc_auc_score(y_test, y_proba)
            print(f"\nROC-AUC Score: {roc_auc:.3f}")
        except:
            pass

    def save_model(self):
        """Salva o modelo e scaler"""
        model_file = self.model_path / 'svm_model.pkl'
        scaler_file = self.model_path / 'scaler.pkl'

        joblib.dump(self.model, str(model_file))
        joblib.dump(self.scaler, str(scaler_file))

        logger.info(f"✅ Modelo salvo em: {model_file}")
        logger.info(f"✅ Scaler salvo em: {scaler_file}")

    def load_model(self):
        """Carrega modelo e scaler salvos"""
        model_file = self.model_path / 'svm_model.pkl'
        scaler_file = self.model_path / 'scaler.pkl'

        if model_file.exists() and scaler_file.exists():
            self.model = joblib.load(str(model_file))
            self.scaler = joblib.load(str(scaler_file))
            logger.info("✅ Modelo SVM carregado com sucesso!")
            return True
        return False

    def predict_single(self, image_path):
        """Classifica uma única imagem"""
        features = self.extract_color_features(image_path)
        if features is None:
            return False, 0.0

        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]
        confidence = self.model.predict_proba(features_scaled)[0][1]

        return bool(prediction), float(confidence)


def main():
    print("\n" + "=" * 70)
    print("🎯 SVM CLASSIFIER - CLASSIFICAÇÃO DE TAMPINHAS")
    print("Sistema de Classificação: É TAMPINHA? SIM ou NÃO")
    print("=" * 70)

    classifier = SVMCapClassifier()

    if classifier.load_model():
        print("✅ Modelo SVM carregado com sucesso!")
    else:
        print("🔄 Treinando novo modelo SVM...")

        # Carregar dados
        print("\n📂 Carregando dados de treino...")
        X, y = classifier.load_dataset()

        # Treinar
        print("\n🚀 Treinando SVM...")
        cv_scores = classifier.train_model(X, y)

        # Salvar
        print("\n💾 Salvando modelo...")
        classifier.save_model()

        # Avaliação
        print("\n📊 Avaliação no conjunto de treino:")
        classifier.evaluate_model(X, y)

    print("\n" + "=" * 70)
    print("✅ Pronto para classificar imagens!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
