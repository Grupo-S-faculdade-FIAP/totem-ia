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
SVM_MIN_MARGIN          =  0.50  # |decision_function| mínimo calibrado para reduzir FN sem aumentar FP
SVM_MIN_MARGIN_HIGH_SAT =  0.80  # margem para SAT_HIGH calibrada por benchmark balanceado

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

            # 7-8: Saturação média e contraste geral
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            saturation = np.mean(hsv[:, :, 1])
            features.append(saturation)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contrast = np.std(gray)
            features.append(contrast)

            # 9-12: Features de borda e forma (Canny + contornos)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = float(np.count_nonzero(edges)) / (128 * 128)
            features.append(edge_density)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = float(len(contours))
            features.append(contour_count)

            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                perim = cv2.arcLength(largest, True)
                circularity = (4 * np.pi * area / (perim ** 2)) if perim > 0 else 0.0
                area_ratio = area / (128 * 128)
            else:
                circularity = 0.0
                area_ratio = 0.0

            features.append(float(circularity))
            features.append(float(area_ratio))

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
            svm_margin = abs(float(svm_conf))

            logger.info(
                f"🔍 SVM: pred={svm_pred}, conf={svm_conf:.2f}, prob={svm_prob:.2f}, "
                f"margin={svm_margin:.2f}, sat={saturation:.1f}"
            )

            # Em modo debug, aceitar tampinha com confiança alta
            if is_debug_mode and saturation > SAT_DEBUG_MIN_THRESHOLD:
                logger.info("🐛 MODO DEBUG: Aceitando como tampinha")
                return 1, 0.95, saturation, "DEBUG_MODE"

            # ────────────────────────────────────────────────────────────────
            # ESTRATÉGIA: Ser mais tolerante com saturação como proxy
            # (porque o SVM está muito rigoroso com 12 features)
            # ────────────────────────────────────────────────────────────────

            if saturation > SAT_HIGH_THRESHOLD:
                # Alta saturação → muito provável que seja tampinha
                logger.info(f"⚠️ SAT_HIGH ({saturation:.1f}) → aceita mesmo se SVM rejeita (proxy)")
                return 1, 0.85, saturation, "SAT_HIGH"
            elif saturation < SAT_VERY_LOW_THRESHOLD:
                confidence = 0.95
                return 0, confidence, saturation, "SAT_VERY_LOW"
            else:
                if saturation > SAT_MID_UPPER_THRESHOLD:
                    # Zona intermediária alta: aceitar com ligeira restrição
                    logger.info(f"⚠️ MID_HIGH_SAT ({saturation:.1f}) → aceita se SVM ≥ 50%")
                    if svm_pred == 1 or svm_margin >= 0.3:  # Muito mais tolerante
                        return 1, 0.70, saturation, "MID_HIGH_SAT"
                    else:
                        return 0, 0.65, saturation, "ACCEPT_MID_SAT"
                elif saturation < SAT_LOW_THRESHOLD:
                    # Faixa de baixa saturação: rejeitar a menos que SVM tenha alta confiança
                    logger.info(f"⚠️ LOW_SAT ({saturation:.1f})")
                    if svm_pred == 1 and svm_margin >= 1.0:
                        return 1, 0.65, saturation, "LOW_SAT_FORCE_TAMPINHA"
                    return 0, 0.70, saturation, "LOW_SAT_FORCE_TAMPINHA"
                else:
                    # Saturação média (50-100): confiar na saturação como proxy
                    logger.info(f"⚠️ NORMAL_SAT ({saturation:.1f}) → aceita como proxy de cor")
                    return 1, 0.75, saturation, "NORMAL_SAT_TAMPINHA"

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return None, None, None, "ERRO"


# if __name__ == "__main__":
#     logger.info("Inicializando classificador...")
#     MODEL, SCALER = load_classifier()