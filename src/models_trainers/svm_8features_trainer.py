#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import cv2
import joblib
import numpy as np
from skimage.feature import hog
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from tqdm import tqdm


logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


MODEL_PATH = Path("models/svm/svm_model_complete.pkl")
SCALER_PATH = Path("models/svm/scaler_complete.pkl")
METRICS_PATH = Path("models/svm/metrics_last.json")

# ROI central: paridade com produção (image.py)
ROI_CENTER_RATIO = 0.75
USE_ROI = os.getenv("USE_ROI", "true").lower() in ("true", "1", "yes")

# HOG: 64x64 grayscale, pixels_per_cell=(16,16) → 324 features
HOG_ORIENTATIONS = 9
HOG_PIXELS_PER_CELL = (16, 16)
HOG_CELLS_PER_BLOCK = (2, 2)
HOG_SIZE = (64, 64)  # resize gray para HOG (menor = menos features)

POSITIVE_DIRS = [
    Path("datasets/field-real/positive"),
    Path("datasets/color-cap/train/images"),
    Path("datasets/color-cap/valid/images"),
    Path("src/tampinhas"),
]

NEGATIVE_DIRS = [
    Path("datasets/field-real/negative"),
    Path("datasets/non-cap/train/images"),
    Path("datasets/non-cap/valid/images"),
    Path("datasets/negatives"),
]

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _crop_to_roi_center(image: np.ndarray) -> np.ndarray:
    """Extrai região central (ROI) — paridade com image.py."""
    if not USE_ROI:
        return image
    h, w = image.shape[:2]
    size = int(min(h, w) * ROI_CENTER_RATIO)
    if size < 32:
        return image
    x = (w - size) // 2
    y = (h - size) // 2
    return image[y : y + size, x : x + size].copy()


def extract_features(image: np.ndarray | None) -> np.ndarray | None:
    """Extrai vetor 8 (cor) + HOG — paridade com produção.
    
    Vetor: [mean_B, std_B, median_B, mean_G, std_G, median_G, sat_mean, contrast] + HOG(324)
    Total: 332 features.
    """
    if image is None or not isinstance(image, np.ndarray):
        return None
    if image.ndim != 3 or image.shape[2] != 3:
        return None
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    image = _crop_to_roi_center(image)
    image = cv2.resize(image, (128, 128))

    b_channel, g_channel, _ = cv2.split(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    color_features = np.array([
        np.mean(b_channel), np.std(b_channel), np.median(b_channel),
        np.mean(g_channel), np.std(g_channel), np.median(g_channel),
        np.mean(hsv[:, :, 1]),
        np.std(gray),
    ], dtype=np.float64)

    gray_hog = cv2.resize(gray, HOG_SIZE)
    hog_features = hog(
        gray_hog,
        orientations=HOG_ORIENTATIONS,
        pixels_per_cell=HOG_PIXELS_PER_CELL,
        cells_per_block=HOG_CELLS_PER_BLOCK,
        visualize=False,
        channel_axis=None,
    ).astype(np.float64)

    return np.concatenate([color_features, hog_features])


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
            features = extract_features(image)
            if features is not None and not np.isnan(features).any():
                positive_features.append(features)

    return positive_features


def load_negative_features() -> list[np.ndarray]:
    """Carrega features negativas reais a partir das pastas configuradas."""
    negative_features: list[np.ndarray] = []

    for directory in NEGATIVE_DIRS:
        if not directory.exists():
            logger.warning(f"⚠️ Pasta negativa não encontrada: {directory}")
            continue

        files = sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS])
        logger.info(f"📂 Lendo negativos de {directory} ({len(files)} arquivos)")

        for file in tqdm(files, desc=f"Negativos {directory.name}", leave=False):
            image = cv2.imread(str(file))
            features = extract_features(image)
            if features is not None and not np.isnan(features).any():
                negative_features.append(features)

    return negative_features


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

        features = extract_features(image)
        if features is not None and not np.isnan(features).any():
            negatives.append(features)

    return negatives


def train_and_save() -> None:
    """Treina SVM com 8 (cor) + HOG features e salva modelo/scaler para produção."""
    logger.info("🚀 Iniciando treinamento SVM (8 cor + HOG)...")

    positives = load_positive_features()
    if not positives:
        raise RuntimeError("Nenhum dado positivo encontrado para treino.")

    negatives = load_negative_features()
    use_synthetic_negatives = os.getenv("USE_SYNTHETIC_NEGATIVES", "0") == "1"
    if not negatives and use_synthetic_negatives:
        logger.warning("⚠️ Nenhum negativo real encontrado. Usando negativos sintéticos por fallback explícito.")
        negatives = generate_synthetic_negative_features(len(positives))
    elif not negatives:
        raise RuntimeError(
            "Nenhum dado negativo real encontrado. "
            "Adicione imagens em datasets/non-cap/* ou datasets/negatives "
            "ou rode com USE_SYNTHETIC_NEGATIVES=1 para fallback temporário."
        )

    if not negatives:
        raise RuntimeError("Falha ao gerar dados negativos sintéticos.")

    x = np.array(positives + negatives, dtype=np.float64)
    y = np.array([1] * len(positives) + [0] * len(negatives), dtype=np.int32)

    logger.info(f"✅ Dataset montado: {len(x)} amostras | positivos={len(positives)} negativos={len(negatives)}")
    logger.info(f"📏 Shape de features: {x.shape}")

    scaler = StandardScaler()
    x_train, x_val, y_train, y_val = train_test_split(
        x,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    x_train_scaled = scaler.fit_transform(x_train)
    x_val_scaled = scaler.transform(x_val)

    model = SVC(
        kernel="rbf",
        C=1.0,
        gamma="scale",
        class_weight="balanced",
        probability=False,
        random_state=42,
    )
    model.fit(x_train_scaled, y_train)

    y_val_pred = model.predict(x_val_scaled)
    precision = precision_score(y_val, y_val_pred, pos_label=1, zero_division=0)
    recall = recall_score(y_val, y_val_pred, pos_label=1, zero_division=0)
    cm = confusion_matrix(y_val, y_val_pred, labels=[0, 1])
    logger.info(f"📊 Validação holdout | precision_tampinha={precision:.4f} recall_tampinha={recall:.4f}")
    logger.info(f"📊 Matriz de confusão [linhas=real 0/1, colunas=pred 0/1]: {cm.tolist()}")

    report = classification_report(
        y_val, y_val_pred,
        target_names=["nao_tampinha", "tampinha"],
        digits=4,
        zero_division=0,
    )
    logger.info("📊 Classification Report (holdout):\n" + report)

    # Refit final com dataset completo para persistência do artefato
    x_scaled_full = scaler.fit_transform(x)
    model.fit(x_scaled_full, y)

    cv_scores = cross_val_score(
        model,
        x_scaled_full,
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

    # Persistir métricas em JSON para evidência e auditoria
    metrics = {
        "n_samples": len(x),
        "n_positives": len(positives),
        "n_negatives": len(negatives),
        "n_features": x.shape[1],
        "holdout": {
            "precision_tampinha": float(precision),
            "recall_tampinha": float(recall),
            "confusion_matrix": cm.tolist(),
        },
        "cv_accuracy": {
            "mean": float(cv_scores.mean()),
            "std": float(cv_scores.std()),
            "scores": [float(s) for s in cv_scores],
        },
        "classification_report": report,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"💾 Métricas salvas em: {METRICS_PATH}")


if __name__ == "__main__":
    train_and_save()
