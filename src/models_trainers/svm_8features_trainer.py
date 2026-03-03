#!/usr/bin/env python3
from __future__ import annotations

import logging
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from tqdm import tqdm


logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


MODEL_PATH = Path("models/svm/svm_model_complete.pkl")
SCALER_PATH = Path("models/svm/scaler_complete.pkl")

POSITIVE_DIRS = [
    Path("datasets/color-cap/train/images"),
    Path("datasets/color-cap/valid/images"),
    Path("src/tampinhas"),
]

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def extract_8_features(image: np.ndarray | None) -> np.ndarray | None:
    """Extrai o vetor de 8 features idêntico ao de produção."""
    if image is None or not isinstance(image, np.ndarray):
        return None
    if image.ndim != 3 or image.shape[2] != 3:
        return None
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    image = cv2.resize(image, (128, 128))

    b_channel, g_channel, _ = cv2.split(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    features = np.array([
        np.mean(b_channel), np.std(b_channel), np.median(b_channel),
        np.mean(g_channel), np.std(g_channel), np.median(g_channel),
        np.mean(hsv[:, :, 1]),
        np.std(gray),
    ], dtype=np.float64)
    return features


def load_positive_features() -> list[np.ndarray]:
    """Carrega features positivas a partir das pastas configuradas."""
    positive_features: list[np.ndarray] = []

    for directory in POSITIVE_DIRS:
        if not directory.exists():
            logger.warning(f"⚠️ Pasta positiva não encontrada: {directory}")
            continue

        files = sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS])
        logger.info(f"📂 Lendo positivos de {directory} ({len(files)} arquivos)")

        for file in tqdm(files, desc=f"Positivos {directory.name}", leave=False):
            image = cv2.imread(str(file))
            features = extract_8_features(image)
            if features is not None and not np.isnan(features).any():
                positive_features.append(features)

    return positive_features


def generate_synthetic_negative_features(num_samples: int) -> list[np.ndarray]:
    """Gera negativos sintéticos em 8 features para balancear o treino."""
    negatives: list[np.ndarray] = []
    rng = np.random.default_rng(42)

    for _ in tqdm(range(num_samples), desc="Negativos sintéticos", leave=False):
        # Gera imagem HSV com saturação baixa a média para simular não-tampinha
        hsv = np.zeros((128, 128, 3), dtype=np.uint8)
        hsv[:, :, 0] = rng.integers(0, 180, size=(128, 128), dtype=np.uint8)
        hsv[:, :, 1] = rng.integers(0, 70, size=(128, 128), dtype=np.uint8)
        hsv[:, :, 2] = rng.integers(30, 255, size=(128, 128), dtype=np.uint8)
        image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        features = extract_8_features(image)
        if features is not None and not np.isnan(features).any():
            negatives.append(features)

    return negatives


def train_and_save() -> None:
    """Treina SVM com 8 features e salva modelo/scaler para produção."""
    logger.info("🚀 Iniciando treinamento SVM (8 features)...")

    positives = load_positive_features()
    if not positives:
        raise RuntimeError("Nenhum dado positivo encontrado para treino.")

    negatives = generate_synthetic_negative_features(len(positives))
    if not negatives:
        raise RuntimeError("Falha ao gerar dados negativos sintéticos.")

    x = np.array(positives + negatives, dtype=np.float64)
    y = np.array([1] * len(positives) + [0] * len(negatives), dtype=np.int32)

    logger.info(f"✅ Dataset montado: {len(x)} amostras | positivos={len(positives)} negativos={len(negatives)}")
    logger.info(f"📏 Shape de features: {x.shape}")

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    model = SVC(
        kernel="rbf",
        C=1.0,
        gamma="scale",
        class_weight="balanced",
        probability=False,
        random_state=42,
    )
    model.fit(x_scaled, y)

    cv_scores = cross_val_score(
        model,
        x_scaled,
        y,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring="accuracy",
    )
    logger.info(f"📊 CV accuracy: mean={cv_scores.mean():.4f} std={cv_scores.std():.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"💾 Modelo salvo em: {MODEL_PATH}")
    logger.info(f"💾 Scaler salvo em: {SCALER_PATH}")


if __name__ == "__main__":
    train_and_save()
