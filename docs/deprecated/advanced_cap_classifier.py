#!/usr/bin/env python3
"""
Modelo Avançado de Deep Learning - Classificação de Tampinhas
Sistema de Classificação: É TAMPINHA? SIM ou NÃO

Usa Transfer Learning com ResNet50 + Data Augmentation
Dataset: Tampinhas reais vs Não-tampinhas
"""

import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import logging
from tqdm import tqdm
import time
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class AdvancedCapClassifier:
    def __init__(self):
        self.model = None
        self.img_size = (224, 224)  # ResNet50 padrão
        self.batch_size = 16
        self.model_path = Path("models/advanced-cap-classifier")
        self.model_path.mkdir(parents=True, exist_ok=True)

    def load_dataset(self):
        """Carrega dataset com data augmentation avançado"""
        logger.info("Carregando dataset para deep learning...")

        X = []
        y = []

        # 1. POSITIVAS: Tampinhas reais
        tampinhas_dir = Path("datasets/tampinhas")
        if tampinhas_dir.exists():
            tampinhas_files = list(tampinhas_dir.glob("*"))
            logger.info(f"Encontradas {len(tampinhas_files)} tampinhas reais")

            for img_path in tqdm(tampinhas_files, desc="Carregando tampinhas"):
                img = self.load_and_preprocess_image(img_path)
                if img is not None:
                    X.append(img)
                    y.append(1)  # TAMPINHA

        # 2. NEGATIVAS: Não-tampinhas
        nao_tampinhas_dir = Path("datasets/nao-tampinhas")
        if nao_tampinhas_dir.exists():
            nao_tampinhas_files = list(nao_tampinhas_dir.glob("*"))
            logger.info(f"Encontradas {len(nao_tampinhas_files)} não-tampinhas")

            for img_path in tqdm(nao_tampinhas_files, desc="Carregando não-tampinhas"):
                img = self.load_and_preprocess_image(img_path)
                if img is not None:
                    X.append(img)
                    y.append(0)  # NÃO É TAMPINHA

        X = np.array(X)
        y = np.array(y)

        logger.info(f"Dataset final: {X.shape[0]} imagens, shape: {X.shape[1:]}")
        logger.info(f"Tampinhas: {np.sum(y == 1)}, Não-tampinhas: {np.sum(y == 0)}")

        return X, y

    def load_and_preprocess_image(self, image_path):
        """Carrega e pré-processa imagem para ResNet"""
        try:
            # Carregar imagem
            img = cv2.imread(str(image_path))
            if img is None:
                return None

            # Converter BGR para RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Resize para tamanho da ResNet
            img = cv2.resize(img, self.img_size)

            # Normalizar para [0,1]
            img = img.astype(np.float32) / 255.0

            return img

        except Exception as e:
            logger.warning(f"Erro ao carregar {image_path}: {e}")
            return None

    def create_data_augmentation(self):
        """Cria data augmentation avançado"""
        return ImageDataGenerator(
            rotation_range=30,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            vertical_flip=True,
            brightness_range=[0.8, 1.2],
            fill_mode='nearest'
        )

    def build_model(self):
        """Constrói modelo com Transfer Learning"""
        logger.info("Construindo modelo com Transfer Learning (ResNet50)...")

        # Base: ResNet50 pré-treinada no ImageNet
        base_model = ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.img_size, 3)
        )

        # Congelar camadas base inicialmente
        for layer in base_model.layers:
            layer.trainable = False

        # Adicionar camadas de classificação
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        predictions = Dense(1, activation='sigmoid')(x)

        # Modelo final
        self.model = Model(inputs=base_model.input, outputs=predictions)

        # Compilar
        self.model.compile(
            optimizer=Adam(learning_rate=1e-4),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )

        logger.info("Modelo construído com sucesso!")

    def train_model(self, X_train, y_train, X_val, y_val):
        """Treina o modelo com fine-tuning"""
        logger.info("Iniciando treinamento...")

        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_accuracy',
            patience=10,
            restore_best_weights=True
        )

        checkpoint = ModelCheckpoint(
            str(self.model_path / 'best_model.keras'),
            monitor='val_accuracy',
            save_best_only=True,
            mode='max'
        )

        # Data augmentation
        datagen = self.create_data_augmentation()

        # Treinamento inicial (só camadas superiores)
        logger.info("Fase 1: Treinando apenas camadas superiores...")
        history1 = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=self.batch_size),
            validation_data=(X_val, y_val),
            epochs=20,
            callbacks=[early_stopping, checkpoint],
            verbose=1
        )

        # Fine-tuning: descongelar algumas camadas da ResNet
        logger.info("Fase 2: Fine-tuning das últimas camadas da ResNet...")
        for layer in self.model.layers[-50:]:  # Últimas 50 camadas
            layer.trainable = True

        # Recompilar com learning rate menor
        self.model.compile(
            optimizer=Adam(learning_rate=1e-5),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )

        # Continuar treinamento
        history2 = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=self.batch_size),
            validation_data=(X_val, y_val),
            epochs=30,
            callbacks=[early_stopping, checkpoint],
            verbose=1
        )

        logger.info("Treinamento concluído!")

        return history1, history2

    def save_model(self):
        """Salva o modelo treinado"""
        model_file = self.model_path / 'final_model.keras'
        self.model.save(str(model_file))
        logger.info(f"Modelo salvo em: {model_file}")

    def load_model(self):
        """Carrega modelo salvo"""
        model_file = self.model_path / 'final_model.keras'
        if model_file.exists():
            self.model = tf.keras.models.load_model(str(model_file))
            logger.info("Modelo carregado com sucesso!")
            return True
        return False

    def predict_single(self, image_path):
        """Classifica uma única imagem"""
        img = self.load_and_preprocess_image(image_path)
        if img is None:
            return False, 0.0

        # Adicionar dimensão batch
        img = np.expand_dims(img, axis=0)

        # Predição
        prediction = self.model.predict(img, verbose=0)[0][0]
        confidence = float(prediction)

        # Threshold padrão 0.5
        is_cap = confidence > 0.5

        return is_cap, confidence

def main():
    print("=" * 70)
    print("🧠 MODELO AVANÇADO DE DEEP LEARNING - TAMPINHAS")
    print("Sistema de Classificação: É TAMPINHA? SIM ou NÃO")
    print("=" * 70)

    classifier = AdvancedCapClassifier()

    if classifier.load_model():
        print("✅ Modelo carregado com sucesso!")
    else:
        print("🔄 Treinando novo modelo de deep learning...")

        # Carregar dados
        print("\n📂 Carregando dados de treino...")
        X, y = classifier.load_dataset()

        # Dividir treino/validação
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"Treino: {X_train.shape[0]} imagens")
        print(f"Validação: {X_val.shape[0]} imagens")

        # Construir modelo
        classifier.build_model()

        # Treinar
        history1, history2 = classifier.train_model(X_train, y_train, X_val, y_val)

        # Salvar
        classifier.save_model()

        # Avaliação final
        print("\n📊 AVALIAÇÃO FINAL:")
        val_loss, val_acc, val_auc = classifier.model.evaluate(X_val, y_val, verbose=0)
        print(".3f"        print(".3f"
        # Predições para métricas detalhadas
        y_pred = (classifier.model.predict(X_val, verbose=0) > 0.5).astype(int).flatten()

        print("\nRelatório de Classificação:")
        print(classification_report(y_val, y_pred, target_names=['NÃO TAMPINHA', 'TAMPINHA']))

        print("Matriz de Confusão:")
        cm = confusion_matrix(y_val, y_pred)
        print(f"  Previsto NÃO: {cm[0]}")
        print(f"  Previsto SIM: {cm[1]}")

if __name__ == "__main__":
    main()