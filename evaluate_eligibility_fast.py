#!/usr/bin/env python3
"""
Random Forest Melhorado - Classificação Binária Rápida
Sistema de Classificação de Tampinhas: É TAMPINHA? SIM ou NÃO

Dataset: 2100 imagens de treino, 200 validação, 100 teste
Features: 24 features otimizadas (mais rápidas que 46)
Modelo: Random Forest otimizado para velocidade
"""

import os
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import logging
from tqdm import tqdm
import time
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class FastCapClassifier:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_selector = SelectKBest(score_func=f_classif, k=20)
        self.model_path = Path("models/fast-cap-classifier")
        self.model_path.mkdir(parents=True, exist_ok=True)

    def extract_fast_features(self, image_path):
        """Extrai 24 features otimizadas para velocidade"""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return None

            image = cv2.resize(image, (128, 128))

            features = []

            # Estatísticas básicas RGB (9 features)
            for channel in cv2.split(image):
                features.extend([
                    np.mean(channel),
                    np.std(channel),
                    np.median(channel)
                ])

            # Estatísticas HSV (9 features)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            for channel in cv2.split(hsv):
                features.extend([
                    np.mean(channel),
                    np.std(channel),
                    np.median(channel)
                ])

            # Forma básica (3 features)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                features.extend([area/10000, perimeter/1000, circularity])
            else:
                features.extend([0, 0, 0])

            # Contraste básico (3 features)
            features.extend([
                np.mean(gray),
                np.std(gray),
                np.max(gray) - np.min(gray)
            ])

            return np.array(features)

        except Exception as e:
            logger.warning(f"Erro ao extrair features de {image_path}: {e}")
            return None

    def load_dataset(self, data_path):
        """Carrega dataset YOLO e extrai features"""
        logger.info(f"Carregando dataset de {data_path}")

        images_dir = Path(data_path) / "images"
        image_files = list(images_dir.glob("*.jpg"))
        logger.info(f"Encontradas {len(image_files)} imagens")

        features_list = []
        valid_labels = []

        for img_path in tqdm(image_files, desc="Extraindo features"):
            features = self.extract_fast_features(img_path)
            if features is not None:
                features_list.append(features)
                valid_labels.append(1)  # Todas são tampinhas válidas

        X = np.array(features_list)
        y = np.array(valid_labels)

        logger.info(f"Dataset carregado: {X.shape[0]} amostras, {X.shape[1]} features")
        return X, y

    def create_negative_samples(self, X_positive, num_negative=500):
        """Cria amostras negativas (não tampinhas)"""
        logger.info(f"Criando {num_negative} amostras negativas")

        np.random.seed(42)
        X_negative = []

        for _ in range(num_negative):
            base_sample = X_positive[np.random.randint(len(X_positive))]
            noise = np.random.normal(0, 0.5, len(base_sample))
            negative_sample = base_sample + noise

            negative_sample[0:3] = np.random.uniform(50, 200, 3)
            negative_sample[9:12] = np.random.uniform(0, 50, 3)
            negative_sample[21:24] = np.random.uniform(20, 100, 3)

            X_negative.append(negative_sample)

        X_negative = np.array(X_negative)
        y_negative = np.zeros(num_negative)

        return X_negative, y_negative

    def train_model(self, X_train, y_train):
        """Treina o modelo Random Forest otimizado"""
        logger.info("Iniciando treinamento do modelo...")

        # Feature selection
        logger.info("Selecionando melhores features...")
        X_selected = self.feature_selector.fit_transform(X_train, y_train)

        # Scaling
        logger.info("Normalizando features...")
        X_scaled = self.scaler.fit_transform(X_selected)

        # Modelo Random Forest otimizado para velocidade
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )

        # Treinamento
        start_time = time.time()
        self.model.fit(X_scaled, y_train)
        train_time = time.time() - start_time

        logger.info(f"Treinamento concluído em {train_time:.2f}s")

        # Cross-validation
        logger.info("Executando validação cruzada...")
        cv_scores = cross_val_score(self.model, X_scaled, y_train, cv=5, scoring='accuracy')
        logger.info(f"Acurácia CV: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

        return cv_scores

    def save_model(self):
        """Salva o modelo treinado"""
        logger.info("Salvando modelo...")

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'feature_names': [f'feature_{i}' for i in range(20)]
        }

        joblib.dump(model_data, self.model_path / "fast_cap_classifier.pkl")
        logger.info(f"Modelo salvo em {self.model_path}")

    def load_model(self):
        """Carrega modelo salvo"""
        model_file = self.model_path / "fast_cap_classifier.pkl"
        if model_file.exists():
            logger.info("Carregando modelo salvo...")
            model_data = joblib.load(model_file)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_selector = model_data['feature_selector']
            return True
        return False

    def predict_single(self, image_path):
        """Classifica uma única imagem"""
        features = self.extract_fast_features(image_path)
        if features is None:
            return False, 0.0

        features_selected = self.feature_selector.transform([features])
        features_scaled = self.scaler.transform(features_selected)

        prediction = self.model.predict(features_scaled)[0]
        confidence = self.model.predict_proba(features_scaled)[0][1]

        return bool(prediction), float(confidence)

def main():
    print("=" * 60)
    print("RANDOM FOREST MELHORADO - CLASSIFICAÇÃO BINÁRIA RÁPIDA")
    print("Sistema de Classificação: É TAMPINHA? SIM ou NÃO")
    print("=" * 60)

    classifier = FastCapClassifier()

    if classifier.load_model():
        print("✅ Modelo carregado com sucesso!")
    else:
        print("🔄 Treinando novo modelo...")

        # Carregar dados de treino
        print("\n📂 Carregando dados de treino...")
        X_train, y_train = classifier.load_dataset("datasets/color-cap/train")

        # Criar amostras negativas
        X_negative, y_negative = classifier.create_negative_samples(X_train, num_negative=500)

        # Combinar dados
        X_combined = np.vstack([X_train, X_negative])
        y_combined = np.hstack([y_train, y_negative])

        print(f"Dataset final: {X_combined.shape[0]} amostras ({X_combined.shape[1]} features)")
        print(f"Positivas: {np.sum(y_combined == 1)}, Negativas: {np.sum(y_combined == 0)}")

        # Treinar modelo
        cv_scores = classifier.train_model(X_combined, y_combined)

        # Salvar modelo
        classifier.save_model()

    # Teste com dados de validação
    print("\n🧪 Testando com dados de validação...")
    X_valid, y_valid = classifier.load_dataset("datasets/color-cap/valid")

    if len(X_valid) > 0:
        X_valid_selected = classifier.feature_selector.transform(X_valid)
        X_valid_scaled = classifier.scaler.transform(X_valid_selected)

        y_pred = classifier.model.predict(X_valid_scaled)
        confidence_scores = classifier.model.predict_proba(X_valid_scaled)[:, 1]

        print("\n📊 RESULTADOS NA VALIDAÇÃO:")
        # Verificar se há ambas as classes
        unique_preds = np.unique(y_pred)
        if len(unique_preds) == 1:
            target_names = ['TAMPINHA'] if unique_preds[0] == 1 else ['NÃO TAMPINHA']
        else:
            target_names = ['NÃO TAMPINHA', 'TAMPINHA']

        print(classification_report(y_valid, y_pred, target_names=target_names))

        cm = confusion_matrix(y_valid, y_pred)
        print("Matriz de Confusão:")
        if cm.shape[0] == 1:
            print(f"  Apenas uma classe detectada: {cm[0][0]} amostras")
        else:
            print(f"  Previsto NÃO: {cm[0]}")
            print(f"  Previsto SIM: {cm[1]}")

        print(f"Confiança média: {np.mean(confidence_scores):.3f}")

    # Teste com imagens do diretório images2/
    print("\n🖼️  Testando com imagens do diretório images2/...")
    test_dir = Path("images2")
    if test_dir.exists():
        image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
        print(f"Encontradas {len(image_files)} imagens para teste")

        results = []
        for img_path in tqdm(image_files, desc="Classificando"):
            is_cap, confidence = classifier.predict_single(img_path)
            results.append((img_path.name, is_cap, confidence))

        caps_found = sum(1 for _, is_cap, _ in results if is_cap)
        print("\n📊 RESULTADOS FINAIS:")
        print(f"   Total de imagens: {len(results)}")
        print(f"   Tampinhas encontradas: {caps_found}")
        print(f"   Taxa de sucesso: {caps_found/len(results)*100:.1f}%")

        print("\n🔍 DETALHES POR IMAGEM:")
        for name, is_cap, conf in results:
            status = "✅ TAMPINHA" if is_cap else "❌ NÃO TAMPINHA"
            print(f"{name:30} | {status} | Confiança: {conf:.3f}")

    print("\n💾 Modelo salvo em:")
    print(f"   {classifier.model_path}")

if __name__ == "__main__":
    main()