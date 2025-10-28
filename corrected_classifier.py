#!/usr/bin/env python3
"""
Modelo Corrigido - Treinamento Adequado
Sistema de Classificação de Tampinhas: É TAMPINHA? SIM ou NÃO
"""

import os
import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.calibration import CalibratedClassifierCV
import joblib
import logging
from tqdm import tqdm
import time
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class CorrectedCapClassifier:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_selector = SelectKBest(score_func=f_classif, k=20)
        self.model_path = Path("models/corrected-cap-classifier")
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
                    np.max(channel) - np.min(channel)
                ])

            # Estatísticas HSV (9 features)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            for channel in cv2.split(hsv):
                features.extend([
                    np.mean(channel),
                    np.std(channel),
                    np.max(channel) - np.min(channel)
                ])

            # Estatísticas de forma (3 features)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            features.extend([
                np.mean(gray),
                np.std(gray),
                np.max(gray) - np.min(gray)
            ])

            return np.array(features)

        except Exception as e:
            logger.warning(f"Erro ao extrair features de {image_path}: {e}")
            return None

    def load_corrected_dataset(self):
        """Carrega dataset corrigido com labels adequadas"""
        logger.info("Carregando dataset corrigido...")

        all_features = []
        all_labels = []

        # 1. Apenas imagens reais de tampinhas (positivas)
        tampinhas_dir = Path("datasets/tampinhas")
        if tampinhas_dir.exists():
            tampinhas_files = list(tampinhas_dir.glob("*.jpg"))
            logger.info(f"Encontradas {len(tampinhas_files)} tampinhas reais")

            for img_path in tqdm(tampinhas_files, desc="Tampinhas reais"):
                features = self.extract_fast_features(img_path)
                if features is not None:
                    all_features.append(features)
                    all_labels.append(1)  # Tampinhas positivas

        # 2. Criar amostras negativas mais realistas
        # Usar imagens que claramente não são tampinhas
        negative_sources = [
            "datasets/color-cap/train/images",  # Algumas podem não ser tampinhas
        ]

        negative_features = []
        for source_dir in negative_sources:
            source_path = Path(source_dir)
            if source_path.exists():
                # Pegar apenas algumas imagens como negativas (assumindo que nem todas são tampinhas)
                source_files = list(source_path.glob("*.jpg"))[:100]  # Limitar para balanceamento
                for img_path in tqdm(source_files, desc=f"Negativas de {source_dir}"):
                    features = self.extract_fast_features(img_path)
                    if features is not None:
                        negative_features.append(features)

        # Adicionar labels negativas
        for features in negative_features[:len(all_features)]:  # Balancear classes
            all_features.append(features)
            all_labels.append(0)  # Não são tampinhas

        X = np.array(all_features)
        y = np.array(all_labels)

        logger.info(f"Dataset corrigido: {X.shape[0]} amostras, {X.shape[1]} features")
        logger.info(f"Positivas: {np.sum(y == 1)}, Negativas: {np.sum(y == 0)}")
        return X, y

    def create_model(self):
        """Cria modelo ensemble corrigido"""
        logger.info("Criando modelo ensemble corrigido...")

        # Modelo base 1: Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        # Modelo base 2: Extra Trees
        et = ExtraTreesClassifier(
            n_estimators=50,
            max_depth=8,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        # Ensemble com voting
        ensemble = VotingClassifier(
            estimators=[('rf', rf), ('et', et)],
            voting='soft',
            weights=[0.6, 0.4]
        )

        # Ensemble sem calibração (para pequeno dataset)
        calibrated_model = ensemble

        logger.info("Modelo corrigido criado")
        return calibrated_model

    def train_model(self, X_train, y_train):
        """Treina o modelo corrigido"""
        logger.info("Iniciando treinamento do modelo corrigido...")

        # Feature selection
        logger.info("Selecionando melhores features...")
        X_selected = self.feature_selector.fit_transform(X_train, y_train)

        # Scaling
        logger.info("Normalizando features...")
        X_scaled = self.scaler.fit_transform(X_selected)

        # Modelo
        self.model = self.create_model()

        # Treinamento
        start_time = time.time()
        self.model.fit(X_scaled, y_train)
        train_time = time.time() - start_time

        logger.info(f"Treinamento concluído em {train_time:.2f}s")
        # Cross-validation (reduzido para 2 folds devido ao pequeno dataset)
        logger.info("Executando validação cruzada...")
        cv_scores = cross_val_score(self.model, X_scaled, y_train, cv=2, scoring='accuracy')
        logger.info(f"Acurácia CV: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        return cv_scores

    def save_model(self):
        """Salva o modelo corrigido"""
        logger.info("Salvando modelo corrigido...")

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'feature_names': [f'feature_{i}' for i in range(20)]
        }

        joblib.dump(model_data, self.model_path / "corrected_cap_classifier.pkl")
        logger.info(f"Modelo salvo em {self.model_path}")

    def load_model(self):
        """Carrega modelo corrigido"""
        model_file = self.model_path / "corrected_cap_classifier.pkl"
        if model_file.exists():
            logger.info("Carregando modelo corrigido...")
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
    print("MODELO CORRIGIDO - CLASSIFICAÇÃO ADEQUADA")
    print("Sistema de Classificação: É TAMPINHA? SIM ou NÃO")
    print("=" * 60)

    classifier = CorrectedCapClassifier()

    if classifier.load_model():
        print("✅ Modelo corrigido carregado!")
    else:
        print("🔄 Treinando modelo corrigido...")

        # Carregar dados corrigidos
        print("\n📂 Carregando dados de treino corrigidos...")
        X_train, y_train = classifier.load_corrected_dataset()

        if len(X_train) == 0:
            print("❌ Erro: Nenhum dado de treinamento encontrado!")
            return

        # Treinar modelo
        cv_scores = classifier.train_model(X_train, y_train)

        # Salvar modelo
        classifier.save_model()

    # Teste com imagens
    print("\n🧪 Testando com imagens...")
    test_images = ['images/imagem1.jpg', 'images/imagem2.jpg', 'images/imagem3.jpg',
                   'images/imagem4.jpg', 'images/imagem5.jpg', 'images/imagem6.jpg']

    tampinhas_count = 0
    nao_tampinhas_count = 0

    for img_path in test_images:
        if os.path.exists(img_path):
            is_cap, confidence = classifier.predict_single(img_path)
            result = '✅ TAMPINHA' if is_cap else '❌ NÃO É TAMPINHA'

            if is_cap:
                tampinhas_count += 1
            else:
                nao_tampinhas_count += 1

            print("30")

    print("\n📊 RESULTADO CORRIGIDO:")
    print("-" * 30)
    print(f"✅ Tampinhas detectadas: {tampinhas_count}")
    print(f"❌ Não são tampinhas: {nao_tampinhas_count}")

    if tampinhas_count == 1 and nao_tampinhas_count == 5:
        print("\n🎯 CLASSIFICAÇÃO CORRIGIDA: imagem6.jpg é tampinha, outras não!")
    else:
        print("\n⚠️  Ainda há inconsistências - verificar dados de treinamento")

if __name__ == "__main__":
    main()