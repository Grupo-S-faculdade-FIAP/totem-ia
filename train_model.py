#!/usr/bin/env python3
"""
Script de Treinamento - SVM Classifier para TOTEM IA
Gera dados dummy se as imagens não estiverem disponíveis
"""

import os
import numpy as np
from pathlib import Path
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class TotemSVMTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = Path("models/svm")
        self.model_path.mkdir(parents=True, exist_ok=True)

    def generate_synthetic_data(self, n_samples=500):
        """Gera dados sintéticos para treinamento"""
        logger.info("🤖 Gerando dados sintéticos para treinamento...")
        
        X_train = []
        y_train = []
        
        # Tampinhas (classe 1) - features com padrão típico
        logger.info("   Gerando 300 amostras de TAMPINHAS...")
        for _ in range(300):
            # Features: RGB stats (9) + HSV stats (9) + Shape (6)
            features = []
            
            # RGB com saturação (típico de tampinhas coloridas)
            for _ in range(3):
                features.extend([
                    np.random.uniform(50, 200),      # mean
                    np.random.uniform(30, 100),      # std
                    np.random.uniform(50, 180)       # median
                ])
            
            # HSV com alta saturação
            features.extend([
                np.random.uniform(0, 180),          # hue mean
                np.random.uniform(40, 120),         # hue std
                np.random.uniform(30, 150),         # hue median
                np.random.uniform(150, 255),        # saturation mean (alto)
                np.random.uniform(30, 80),          # saturation std
                np.random.uniform(140, 255),        # saturation median
                np.random.uniform(80, 200),         # value mean
                np.random.uniform(20, 70),          # value std
                np.random.uniform(90, 190)          # value median
            ])
            
            # Shape features
            features.extend([
                np.random.uniform(2, 5),            # area normalizado
                np.random.uniform(0.3, 0.8),        # perimeter normalizado
                np.random.uniform(0.6, 1.0),        # circularity (tampinhas são redondas)
                np.random.uniform(0.8, 1.2),        # aspect ratio
                np.random.uniform(0.7, 1.0),        # solidity (solid shapes)
                np.random.uniform(2, 5.2)           # hull area
            ])
            
            X_train.append(features)
            y_train.append(1)  # Tampinha
        
        # Não-Tampinhas (classe 0)
        logger.info("   Gerando 200 amostras de NÃO-TAMPINHAS...")
        for _ in range(200):
            features = []
            
            # RGB mais variado
            for _ in range(3):
                features.extend([
                    np.random.uniform(50, 220),
                    np.random.uniform(40, 120),
                    np.random.uniform(40, 210)
                ])
            
            # HSV com saturação baixa ou média
            features.extend([
                np.random.uniform(0, 180),
                np.random.uniform(30, 150),
                np.random.uniform(20, 180),
                np.random.uniform(20, 150),         # saturation lower
                np.random.uniform(30, 100),
                np.random.uniform(10, 150),
                np.random.uniform(60, 210),
                np.random.uniform(20, 100),
                np.random.uniform(50, 200)
            ])
            
            # Shape features - mais variados
            features.extend([
                np.random.uniform(1, 8),
                np.random.uniform(0.2, 1.2),
                np.random.uniform(0.3, 0.95),       # menos circular
                np.random.uniform(0.5, 2.0),        # aspect ratio variado
                np.random.uniform(0.4, 1.0),
                np.random.uniform(1, 9)
            ])
            
            X_train.append(features)
            y_train.append(0)  # Não-Tampinha
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        logger.info(f"   ✅ {len(X_train)} amostras geradas")
        logger.info(f"      - Tampinhas: {np.sum(y_train == 1)}")
        logger.info(f"      - Não-Tampinhas: {np.sum(y_train == 0)}")
        
        return X_train, y_train

    def train_model(self, X_train, y_train):
        """Treina o modelo SVM"""
        logger.info("🧠 Treinando modelo SVM...")
        
        # Normalizar dados
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Criar e treinar modelo
        self.model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            class_weight='balanced',
            probability=True,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Avaliar no conjunto de treino
        train_acc = self.model.score(X_train_scaled, y_train)
        logger.info(f"   ✅ Acurácia Treino: {train_acc:.4f}")
        
        return self.model, self.scaler

    def save_model(self):
        """Salva o modelo e scaler"""
        try:
            joblib.dump(self.model, self.model_path / "svm_model_complete.pkl")
            joblib.dump(self.scaler, self.model_path / "scaler_complete.pkl")
            logger.info(f"💾 Modelo salvo em {self.model_path}")
            logger.info(f"   - svm_model_complete.pkl")
            logger.info(f"   - scaler_complete.pkl")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar modelo: {e}")
            return False

    def run(self):
        """Executa pipeline completo de treinamento"""
        print("=" * 70)
        print("🧠 TOTEM IA - TREINADOR DO MODELO SVM")
        print("=" * 70)
        print()
        
        # Verificar se modelo já existe
        model_file = self.model_path / "svm_model_complete.pkl"
        if model_file.exists():
            logger.info("✅ Modelo já existe em models/svm/")
            response = input("Deseja retreinar? (s/n): ").strip().lower()
            if response != 's':
                logger.info("Usando modelo existente.")
                return True
        
        # Gerar dados sintéticos
        X_train, y_train = self.generate_synthetic_data()
        
        # Treinar modelo
        self.train_model(X_train, y_train)
        
        # Salvar modelo
        success = self.save_model()
        
        print()
        if success:
            print("✅ Modelo treinado e salvo com sucesso!")
        else:
            print("❌ Erro ao treinar o modelo")
        
        print("=" * 70)
        return success

if __name__ == '__main__':
    trainer = TotemSVMTrainer()
    trainer.run()
