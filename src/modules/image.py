from __future__ import annotations

import logging
import traceback

import cv2  # pyright: ignore[reportMissingImports]
# import requests 
import joblib  # pyright: ignore[reportMissingImports]
from pathlib import Path

import numpy as np  # pyright: ignore[reportMissingImports]


logger = logging.getLogger(__name__)

# =============================================================================
# Seção 3 (ml-conventions): Thresholds de saturação — NÃO alterar sem documentar experimento
# =============================================================================
SAT_HIGH_THRESHOLD      = 120  # sat > 120 → SAT_HIGH
SAT_MID_UPPER_THRESHOLD = 100  # sat > 100 → MID_HIGH_SAT / ACCEPT_MID_SAT
SAT_DEBUG_MIN_THRESHOLD =  50  # sat > 50  → DEBUG_MODE ativo
SAT_LOW_THRESHOLD       =  50  # sat < 50  → LOW_SAT_FORCE_TAMPINHA
SAT_VERY_LOW_THRESHOLD  =  30  # sat < 30  → SAT_VERY_LOW (não-tampinha)

# =============================================================================
# Seção 6 (ml-conventions): Caminhos de modelo — constantes, nunca inline
# =============================================================================
MODEL_PATH  = Path('models/svm/svm_model_complete.pkl')
SCALER_PATH = Path('models/svm/scaler_complete.pkl')


class ImageClassifier:
    def __init__(self):
        self.model = None
        self.scaler = None

    def load_classifier(self):

        try:
            model_path = MODEL_PATH
            scaler_path = SCALER_PATH

            if not model_path.exists() or not scaler_path.exists():
                logger.error(f"❌ Arquivos do modelo não encontrados!")
                logger.error(f"   - Procurando em: {model_path.absolute()}")
                logger.error(f"   - Procurando em: {scaler_path.absolute()}")
                return None, None

            model = joblib.load(str(model_path))
            scaler = joblib.load(str(scaler_path))
            logger.info("✅ Modelo SVM carregado com sucesso!")
            # return model, scaler
            self.model = model
            self.scaler = scaler
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}", exc_info=True)
            self.model = None
            self.scaler = None


    def extract_color_features(self, image: np.ndarray) -> np.ndarray | None:
        try:
            logger.debug(f"🔍 extract_color_features iniciada. Image type: {type(image)}, shape: {image.shape if hasattr(image, 'shape') else 'N/A'}")
            
            if not isinstance(image, np.ndarray):
                logger.error(f"❌ Imagem não é ndarray! Tipo: {type(image)}")
                return None
            if image.ndim != 3 or image.shape[2] != 3:
                logger.error(f"❌ Shape inesperado: {image.shape} (esperado H×W×3 BGR)")
                return None
            if image.dtype != np.uint8:
                logger.warning(f"⚠️ dtype={image.dtype}, convertendo para uint8")
                image = image.astype(np.uint8)

            image = cv2.resize(image, (128, 128))
            logger.debug(f"✅ Imagem redimensionada para 128x128")

            # Extrair apenas 8 features para match com modelo
            features = []

            # Split único — evita chamar cv2.split() múltiplas vezes
            b_channel, g_channel, _ = cv2.split(image)

            # 1-3: Mean, Std, Median do canal B
            features.extend([
                np.mean(b_channel),
                np.std(b_channel),
                np.median(b_channel)
            ])

            # 4-6: Mean, Std, Median do canal G
            features.extend([
                np.mean(g_channel),
                np.std(g_channel),
                np.median(g_channel)
            ])

            # 7-8: Saturação média e contrastre geral
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            saturation = np.mean(hsv[:, :, 1])
            features.append(saturation)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contrast = np.std(gray)
            features.append(contrast)

            return np.array(features)
        except Exception as e:
            logger.error(f"Erro ao extrair features: {e}")
            return None


    def classify_image(self, image: np.ndarray | None, is_debug_mode: bool = False) -> tuple[int | None, float | None, float | None, str]:
        if image is None or self.model is None or self.scaler is None:
            logger.error(f"⚠️ Prerequisitos faltando: image={image is not None}, MODEL={self.model is not None}, SCALER={self.scaler is not None}")
            return None, None, None, "ERRO"

        try:
            logger.info(f"📸 Iniciando classificação. Imagem shape: {image.shape if image is not None else 'None'}")

            # Features e saturação calculados em uma única passagem (sem conversão HSV dupla)
            features = self.extract_color_features(image)
            if features is None or np.isnan(features).any():
                logger.error("❌ Erro ao extrair features")
                return None, None, None, "ERRO"

            saturation = float(features[6])  # features[6] = saturação média HSV
            logger.info(f"✅ Features extraídas. Shape: {features.shape}, Saturação: {saturation:.1f}")

            features_scaled = self.scaler.transform([features])

            svm_pred = self.model.predict(features_scaled)[0]
            svm_conf = self.model.decision_function(features_scaled)[0]
            svm_prob = 1 / (1 + np.exp(-svm_conf))

            logger.info(f"🔍 SVM: pred={svm_pred}, conf={svm_conf:.2f}, prob={svm_prob:.2f}, sat={saturation:.1f}")

            # Em modo debug, aceitar tampinha com confiança alta
            if is_debug_mode and saturation > SAT_DEBUG_MIN_THRESHOLD:
                logger.info("🐛 MODO DEBUG: Aceitando como tampinha")
                return 1, 0.95, saturation, "DEBUG_MODE"

            if saturation > SAT_HIGH_THRESHOLD:
                confidence = 0.95 if svm_pred == 1 else 0.90
                return 1, confidence, saturation, "SAT_HIGH"
            elif saturation < SAT_VERY_LOW_THRESHOLD:
                confidence = 0.95
                return 0, confidence, saturation, "SAT_VERY_LOW"
            else:
                if saturation > SAT_MID_UPPER_THRESHOLD:
                    if svm_pred == 1:
                        return 1, 0.75, saturation, "MID_HIGH_SAT"
                    else:
                        return 1, 0.70, saturation, "ACCEPT_MID_SAT"
                elif saturation < SAT_LOW_THRESHOLD:
                    return 1, 0.75, saturation, "LOW_SAT_FORCE_TAMPINHA"
                else:
                    # Saturação entre SAT_LOW_THRESHOLD e SAT_MID_UPPER_THRESHOLD
                    return 1, 0.80, saturation, "NORMAL_SAT_TAMPINHA"

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return None, None, None, "ERRO"


# if __name__ == "__main__":
#     logger.info("Inicializando classificador...")
#     MODEL, SCALER = load_classifier()