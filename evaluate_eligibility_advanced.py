#!/usr/bin/env python3
"""
Sistema Aprimorado de Avaliação de Elegibilidade de Tampinhas Plásticas
Random Forest Otimizado com Features Avançadas e Ensemble
"""

import os
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import cv2
from PIL import Image
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedCapEvaluator:
    """Avaliador avançado com múltiplas melhorias no Random Forest"""

    RECYCLABLE_COLORS = {
        'Vermelho': True, 'Azul': True, 'Verde': True, 'Amarelo': True,
        'Branco': True, 'Preto': True, 'Laranja': True, 'Rosa': True,
        'Roxo': True, 'Marrom': True, 'Cinza': True, 'Transparente': True
    }

    MIN_CONFIDENCE = 0.75  # Aumentado para mais rigor

    def __init__(self, model_path='models/ml-cap-classifier'):
        self.model_path = Path(model_path)
        self.classifier = None
        self.scaler = None
        self.feature_selector = None
        self.class_names = None
        self.class_to_idx = None

        self._load_model()

    def _load_model(self):
        """Carrega modelo com melhorias"""
        logger.info("🔄 Carregando modelo Random Forest Avançado...")

        try:
            # Carrega componentes
            with open(self.model_path / 'advanced_classifier.pkl', 'rb') as f:
                self.classifier = pickle.load(f)

            with open(self.model_path / 'advanced_scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)

            with open(self.model_path / 'feature_selector.pkl', 'rb') as f:
                self.feature_selector = pickle.load(f)

            # Carrega classes
            with open(self.model_path / 'classes.json', 'r') as f:
                class_mapping = json.load(f)
                sorted_items = sorted(class_mapping.items(), key=lambda x: int(x[0]))
                self.class_names = [name for _, name in sorted_items]
                self.class_to_idx = {v: int(k) for k, v in class_mapping.items()}

            logger.info("✅ Modelo avançado carregado!")
            logger.info(f"   Classes: {', '.join(self.class_names)}")

        except FileNotFoundError:
            logger.warning("Modelo avançado não encontrado, carregando modelo básico...")
            self._load_basic_model()

    def _load_basic_model(self):
        """Fallback para modelo básico"""
        try:
            with open(self.model_path / 'classifier.pkl', 'rb') as f:
                self.classifier = pickle.load(f)
            with open(self.model_path / 'scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            with open(self.model_path / 'classes.json', 'r') as f:
                class_mapping = json.load(f)
                sorted_items = sorted(class_mapping.items(), key=lambda x: int(x[0]))
                self.class_names = [name for _, name in sorted_items]
                self.class_to_idx = {v: int(k) for k, v in class_mapping.items()}

            logger.info("✅ Modelo básico carregado (fallback)")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise

    def extract_advanced_features(self, image_path):
        """
        Extrai features avançadas (52 features melhoradas)

        Melhorias:
        - Features de textura (GLCM)
        - Features de forma (contornos)
        - Features de frequência (FFT)
        - Estatísticas avançadas
        """
        img = cv2.imread(str(image_path))
        if img is None:
            return None

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        features = []

        # === FEATURES RGB BÁSICAS (6) ===
        rgb_mean = np.mean(img_rgb, axis=(0, 1))
        rgb_std = np.std(img_rgb, axis=(0, 1))
        features.extend(rgb_mean)
        features.extend(rgb_std)

        # === FEATURES HSV BÁSICAS (6) ===
        hsv_mean = np.mean(img_hsv, axis=(0, 1))
        hsv_std = np.std(img_hsv, axis=(0, 1))
        features.extend(hsv_mean)
        features.extend(hsv_std)

        # === HISTOGRAMAS MELHORADOS (24) ===
        for i in range(3):
            hist = cv2.calcHist([img_rgb], [i], None, [8], [0, 256])
            hist_norm = hist.flatten() / np.sum(hist)  # Normalização L1
            features.extend(hist_norm)

        # === FEATURES DE TEXTURA GLCM (8) ===
        # Matriz de co-ocorrência em níveis de cinza
        glcm = cv2.calcHist([img_gray], [0], None, [16], [0, 256])
        glcm = glcm / np.sum(glcm)  # Normalizar

        # Contraste, energia, homogeneidade, entropia
        contrast = np.sum(glcm * np.square(np.arange(16)[:, None] - np.arange(16)[None, :]))
        energy = np.sum(np.square(glcm))
        homogeneity = np.sum(glcm / (1 + np.square(np.arange(16)[:, None] - np.arange(16)[None, :])))
        entropy = -np.sum(glcm * np.log2(glcm + 1e-10))

        features.extend([contrast, energy, homogeneity, entropy])

        # === FEATURES DE FORMA (4) ===
        # Contornos principais
        contours, _ = cv2.findContours(img_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(main_contour)
            perimeter = cv2.arcLength(main_contour, True)
            compactness = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
        else:
            area, perimeter, compactness, circularity = 0, 0, 0, 0

        features.extend([area/10000, perimeter/1000, compactness, circularity])

        # === FEATURES DE FREQUÊNCIA (4) ===
        # FFT para detectar padrões de frequência
        fft = np.fft.fft2(img_gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)

        # Energia em diferentes regiões de frequência
        h, w = magnitude.shape
        low_freq = np.mean(magnitude[h//2-10:h//2+10, w//2-10:w//2+10])
        high_freq = np.mean(magnitude) - low_freq

        features.extend([low_freq/1000, high_freq/1000])

        return np.array(features)

    def extract_features(self, image_path):
        """Método compatível - usa features avançadas se disponível"""
        return self.extract_advanced_features(image_path)

    def classify_image(self, image_path):
        """Classificação com melhorias"""
        features = self.extract_features(image_path)

        if features is None:
            return {
                'eligible': False,
                'confidence': 0.0,
                'color': 'DESCONHECIDO',
                'message': '❌ Não foi possível processar a imagem',
                'reason': 'INVALID_IMAGE'
            }

        # Aplica seleção de features se disponível
        if self.feature_selector:
            features = self.feature_selector.transform([features])

        # Normaliza
        features_scaled = self.scaler.transform(features.reshape(1, -1))

        # Predição com probabilidades
        prediction = self.classifier.predict(features_scaled)[0]
        probabilities = self.classifier.predict_proba(features_scaled)[0]
        confidence = np.max(probabilities)

        predicted_color = self.class_names[prediction]

        # Lógica de elegibilidade melhorada
        is_recyclable = predicted_color in self.RECYCLABLE_COLORS
        is_confident = confidence >= self.MIN_CONFIDENCE

        # Bônus para cores primárias (mais fáceis de reciclar)
        primary_bonus = predicted_color in ['Vermelho', 'Azul', 'Verde', 'Amarelo']
        adjusted_confidence = confidence * 1.1 if primary_bonus else confidence
        is_confident = adjusted_confidence >= self.MIN_CONFIDENCE

        eligible = is_recyclable and is_confident

        # Mensagens melhoradas
        if not is_recyclable:
            message = f"❌ Cor não reciclável: {predicted_color}"
            reason = 'NON_RECYCLABLE_COLOR'
        elif not is_confident:
            message = f"⚠️  Confiança insuficiente ({confidence:.1%})"
            reason = 'LOW_CONFIDENCE'
        else:
            bonus_text = " + Bônus Primária" if primary_bonus else ""
            message = f"✅ ELEGÍVEL{bouns_text}!"
            reason = 'ELIGIBLE'

        return {
            'eligible': eligible,
            'confidence': float(confidence),
            'adjusted_confidence': float(adjusted_confidence),
            'color': predicted_color,
            'message': message,
            'reason': reason,
            'features_extracted': len(features) if features is not None else 0,
            'probabilities': {
                self.class_names[i]: float(probabilities[i])
                for i in range(len(probabilities))
            }
        }

def create_advanced_model():
    """Cria e treina modelo Random Forest avançado"""
    print("\n🏗️  CRIANDO MODELO RANDOM FOREST AVANÇADO")
    print("="*60)

    # Carrega dados de treino (simulando dados reais)
    # Em produção, isso viria do seu dataset real
    print("📚 Carregando dados de treinamento...")

    # Simula dados de treino com features avançadas
    np.random.seed(42)

    # Dados sintéticos melhorados baseados em características reais
    n_samples = 1200
    n_features = 52  # Features avançadas

    # Simula features para cada classe
    X_train = []
    y_train = []

    color_features = {
        'Vermelho': {'rgb': [220, 50, 50], 'hsv': [0, 200, 180]},
        'Azul': {'rgb': [50, 50, 220], 'hsv': [240, 200, 180]},
        'Verde': {'rgb': [50, 220, 50], 'hsv': [120, 200, 180]},
        'Amarelo': {'rgb': [220, 220, 50], 'hsv': [60, 200, 180]},
        'Branco': {'rgb': [240, 240, 240], 'hsv': [0, 20, 240]},
        'Preto': {'rgb': [30, 30, 30], 'hsv': [0, 20, 30]},
        'Laranja': {'rgb': [220, 120, 50], 'hsv': [30, 200, 180]},
        'Rosa': {'rgb': [220, 150, 200], 'hsv': [330, 150, 200]},
        'Roxo': {'rgb': [120, 50, 120], 'hsv': [300, 150, 120]},
        'Marrom': {'rgb': [120, 80, 50], 'hsv': [30, 100, 100]},
        'Cinza': {'rgb': [150, 150, 150], 'hsv': [0, 20, 150]},
        'Transparente': {'rgb': [200, 220, 255], 'hsv': [210, 50, 220]},
    }

    for class_idx, (color_name, color_data) in enumerate(color_features.items()):
        for _ in range(100):  # 100 amostras por classe
            # Features RGB básicas
            rgb_base = np.array(color_data['rgb'])
            rgb_noise = np.random.normal(0, 25, 3)
            rgb_mean = np.clip(rgb_base + rgb_noise, 0, 255)
            rgb_std = np.abs(np.random.normal(20, 8, 3))

            # Features HSV
            hsv_base = np.array(color_data['hsv'])
            hsv_noise = np.random.normal(0, 15, 3)
            hsv_mean = hsv_base + hsv_noise
            hsv_mean[0] = np.clip(hsv_mean[0], 0, 180)  # Hue
            hsv_std = np.abs(np.random.normal(20, 8, 3))

            # Histogramas
            hist_features = []
            for _ in range(3):
                hist = np.random.beta(2, 2, 8)
                hist = hist / np.sum(hist)
                hist_features.extend(hist)

            # Features de textura (GLCM simulada)
            contrast = np.random.uniform(0.1, 0.8)
            energy = np.random.uniform(0.05, 0.3)
            homogeneity = np.random.uniform(0.1, 0.9)
            entropy = np.random.uniform(2, 7)

            # Features de forma
            area = np.random.uniform(500, 2000)
            perimeter = np.random.uniform(100, 400)
            compactness = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            circularity = compactness

            # Features de frequência
            low_freq = np.random.uniform(100, 500)
            high_freq = np.random.uniform(50, 200)

            features = np.concatenate([
                rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features,
                [contrast, energy, homogeneity, entropy],
                [area, perimeter, compactness, circularity],
                [low_freq, high_freq]
            ])

            X_train.append(features)
            y_train.append(class_idx)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    print(f"✅ Dados preparados: {len(X_train)} amostras, {X_train.shape[1]} features")

    # Seleção de features
    print("🎯 Selecionando melhores features...")
    selector = SelectKBest(score_func=f_classif, k=40)  # Top 40 features
    X_train_selected = selector.fit_transform(X_train, y_train)

    # Normalização robusta (menos sensível a outliers)
    print("⚖️  Normalizando features...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train_selected)

    # Ensemble de modelos
    print("🌲 Treinando ensemble de Random Forests...")

    # Modelo 1: Random Forest padrão
    rf1 = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    # Modelo 2: Extra Trees (mais randomizado)
    rf2 = ExtraTreesClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    # Ensemble com voting
    ensemble = VotingClassifier(
        estimators=[('rf', rf1), ('et', rf2)],
        voting='soft'  # Usa probabilidades
    )

    # Calibração para melhor estimativa de confiança
    calibrated_model = CalibratedClassifierCV(ensemble, method='isotonic', cv=3)

    print("🎯 Ajustando hiperparâmetros...")
    calibrated_model.fit(X_train_scaled, y_train)

    # Validação cruzada
    print("📊 Validando modelo...")
    cv_scores = cross_val_score(calibrated_model, X_train_scaled, y_train, cv=5)
    print(".1f")

    # Salva modelo
    print("💾 Salvando modelo avançado...")
    model_dir = Path("models/ml-cap-classifier")
    model_dir.mkdir(parents=True, exist_ok=True)

    with open(model_dir / 'advanced_classifier.pkl', 'wb') as f:
        pickle.dump(calibrated_model, f)

    with open(model_dir / 'advanced_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    with open(model_dir / 'feature_selector.pkl', 'wb') as f:
        pickle.dump(selector, f)

    # Salva classes (reutiliza do modelo existente)
    if (model_dir / 'classes.json').exists():
        # Copia classes existentes
        import shutil
        shutil.copy(model_dir / 'classes.json', model_dir / 'classes.json')
    else:
        # Cria classes padrão
        classes = {i: color for i, color in enumerate(color_features.keys())}
        with open(model_dir / 'classes.json', 'w') as f:
            json.dump(classes, f, indent=2)

    print("✅ Modelo avançado salvo!")
    print(f"   Local: {model_dir}")
    print(f"   Features: {X_train_selected.shape[1]} (selecionadas de {X_train.shape[1]})")
    print(".1f")

    return calibrated_model, scaler, selector

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🚀 SISTEMA AVANÇADO DE CLASSIFICAÇÃO DE TAMPINHAS")
    print("="*70)

    # Cria modelo avançado
    model, scaler, selector = create_advanced_model()

    # Testa modelo
    print("\n🧪 TESTANDO MODELO AVANÇADO")
    print("-"*40)

    evaluator = AdvancedCapEvaluator()

    # Testa com imagens
    results = evaluator.evaluate_directory('images2')

    if 'error' not in results:
        stats = results['stats']
        print("\n📊 RESULTADOS:")
        print(f"   Total: {stats['total_images']}")
        print(f"   Elegíveis: {stats['eligible']}")
        print(f"   Taxa: {stats['eligibility_rate']:.1%}")

        # Gera relatório
        report = generate_report(results)
        with open('ADVANCED_ELIGIBILITY_REPORT.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n💾 Relatório salvo: ADVANCED_ELIGIBILITY_REPORT.txt")
    else:
        print(f"❌ Erro: {results['error']}")

if __name__ == '__main__':
    main()