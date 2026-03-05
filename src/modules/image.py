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
# Validações de Visão Computacional (CV pre-screening)
# =============================================================================
CV_MIN_CIRCULARITY      = 0.72  # Tampinha real: 0.80-0.95 | Rosto: 0.50-0.70 | invariante a escala
CV_MIN_ASPECT_RATIO     = 0.82  # Bounding box da tampinha ≈ quadrado (w/h ≈ 1.0) | Rosto: 0.60-0.78

# =============================================================================
# Seção 6 (ml-conventions): Caminhos de modelo — constantes, nunca inline
# =============================================================================
MODEL_PATH  = Path('models/svm/svm_model_complete.pkl')
SCALER_PATH = Path('models/svm/scaler_complete.pkl')


class ImageClassifier:
    def __init__(self):
        self.model = None
        self.scaler = None
        self._last_circularity = 0.0
        self._last_contour_count = 0.0
        self._last_aspect_ratio = 0.0
        self._last_hough_count = 0

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

            # CV metrics para pre-screening — não entram no vetor SVM
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # HoughCircles: detecta círculos reais (tampinha tem borda circular forte)
            # Rosto não tem borda circular bem definida → HoughCircles não detecta
            hough_circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT,
                dp=1.2, minDist=30,
                param1=60, param2=22,
                minRadius=8, maxRadius=60
            )
            hough_count = int(len(hough_circles[0])) if hough_circles is not None else 0

            # Canny + contornos: circularidade e aspect ratio do maior contorno
            edges = cv2.Canny(blurred, 40, 120)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = float(len(contours))

            circularity = 0.0
            aspect_ratio = 0.0
            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                perim = cv2.arcLength(largest, True)
                circularity = (4 * np.pi * area / (perim ** 2)) if perim > 0 else 0.0
                x, y, w, h = cv2.boundingRect(largest)
                aspect_ratio = float(min(w, h)) / float(max(w, h)) if max(w, h) > 0 else 0.0

            # Guardar CV metrics para pre-screening (não incluir no vetor SVM)
            self._last_circularity = float(circularity)
            self._last_contour_count = contour_count
            self._last_aspect_ratio = float(aspect_ratio)
            self._last_hough_count = hough_count

            # Não incluir features de borda no output (modelo foi treinado com 8 features apenas)
            return np.array(features[:8])
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
            circularity = self._last_circularity
            contour_count = self._last_contour_count
            aspect_ratio = self._last_aspect_ratio
            hough_count = self._last_hough_count

            logger.info(f"✅ Features extraídas. Shape: {features.shape}, Saturação: {saturation:.1f}")
            logger.info(
                f"🔍 CV Metrics: hough={hough_count}, circ={circularity:.2f}, "
                f"aspect={aspect_ratio:.2f}, contornos={contour_count:.0f}"
            )

            # ========== PRÉ-SCREENING: VALIDAÇÃO CV ==========
            # Estratégia em cascata:
            # 1. HoughCircles detectou círculo → APROVADO (mais confiável)
            # 2. Sem HoughCircles mas contorno circular → verificar circ + aspect_ratio
            # 3. Sem contornos → SVM decide (tampinha sem contraste suficiente)
            if hough_count > 0:
                logger.info(f"✅ CV: HoughCircles detectou {hough_count} círculo(s) → APROVADO")
            elif contour_count > 0:
                is_circular = circularity >= CV_MIN_CIRCULARITY
                is_square_bbox = aspect_ratio >= CV_MIN_ASPECT_RATIO
                if not is_circular or not is_square_bbox:
                    reason = []
                    if not is_circular:
                        reason.append(f"circ={circularity:.2f}<{CV_MIN_CIRCULARITY}")
                    if not is_square_bbox:
                        reason.append(f"aspect={aspect_ratio:.2f}<{CV_MIN_ASPECT_RATIO}")
                    logger.warning(f"❌ CV Rejection: {', '.join(reason)}")
                    return 0, 0.90, saturation, f"CV_REJECT ({', '.join(reason)})"
                logger.info(f"✅ CV: contorno circular (circ={circularity:.2f}, aspect={aspect_ratio:.2f})")
            else:
                logger.info("⚠️ CV: sem contornos detectados — SVM vai decidir")

            # ========== CLASSIFICAÇÃO SVM ==========
            features_scaled = self.scaler.transform([features])

            svm_pred = self.model.predict(features_scaled)[0]
            svm_conf = self.model.decision_function(features_scaled)[0]
            svm_prob = 1 / (1 + np.exp(-svm_conf))
            svm_margin = abs(float(svm_conf))

            # cv_confirmed_circle: CV confirma com SEGURANÇA que o objeto é circular.
            # HoughCircles sozinho não basta — um oval pode ter Hough detectado.
            # Exige que: Hough detectado E (sem contornos OU aspect_ratio válido no contorno)
            hough_with_valid_shape = (
                hough_count > 0
                and (contour_count == 0 or aspect_ratio >= CV_MIN_ASPECT_RATIO)
            )
            contour_circular = (
                contour_count > 0
                and circularity >= CV_MIN_CIRCULARITY
                and aspect_ratio >= CV_MIN_ASPECT_RATIO
            )
            cv_confirmed_circle = hough_with_valid_shape or contour_circular

            logger.info(
                f"🔍 SVM: pred={svm_pred}, conf={svm_conf:.2f}, prob={svm_prob:.2f}, "
                f"margin={svm_margin:.2f}, sat={saturation:.1f}, cv_circle={cv_confirmed_circle}"
            )

            # Em modo debug, aceitar tampinha com confiança alta
            if is_debug_mode and saturation > SAT_DEBUG_MIN_THRESHOLD:
                logger.info("🐛 MODO DEBUG: Aceitando como tampinha")
                return 1, 0.95, saturation, "DEBUG_MODE"

            # ────────────────────────────────────────────────────────────────
            # ESTRATÉGIA: CV confirma forma circular → SVM precisa de menos margem
            # Se CV NÃO confirmou → SVM decide sozinho com margens calibradas
            # ────────────────────────────────────────────────────────────────

            if cv_confirmed_circle and saturation >= SAT_VERY_LOW_THRESHOLD:
                # CV confirmou círculo via HoughCircles/contorno + saturação mínima.
                # O SVM é ignorado aqui porque foi treinado em imagens de dataset e sofre
                # training-serving skew quando aplicado a frames de câmera com fundo variável.
                # A forma circular (HoughCircles) é critério mais confiável neste cenário.
                logger.info(f"✅ CV confirmou círculo + sat≥{SAT_VERY_LOW_THRESHOLD} → TAMPINHA (CV é autoridade)")
                return 1, 0.85, saturation, "CV_CIRCLE_CONFIRMED"

            # Sem confirmação CV → SVM decide com margens calibradas
            if saturation > SAT_HIGH_THRESHOLD:
                if svm_pred == 1 and svm_margin >= SVM_MIN_MARGIN_HIGH_SAT:
                    return 1, 0.90, saturation, "SAT_HIGH"
                return 0, 0.90, saturation, "SAT_HIGH"
            elif saturation < SAT_VERY_LOW_THRESHOLD:
                return 0, 0.95, saturation, "SAT_VERY_LOW"
            else:
                if saturation > SAT_MID_UPPER_THRESHOLD:
                    if svm_pred == 1 and svm_margin >= SVM_MIN_MARGIN:
                        return 1, 0.75, saturation, "MID_HIGH_SAT"
                    return 0, 0.70, saturation, "ACCEPT_MID_SAT"
                elif saturation < SAT_LOW_THRESHOLD:
                    if svm_pred == 1 and svm_margin >= 1.2:
                        return 1, 0.65, saturation, "LOW_SAT_FORCE_TAMPINHA"
                    return 0, 0.70, saturation, "LOW_SAT_FORCE_TAMPINHA"
                else:
                    if svm_pred == 1 and svm_margin >= SVM_MIN_MARGIN:
                        return 1, 0.80, saturation, "NORMAL_SAT_TAMPINHA"
                    return 0, 0.80, saturation, "NORMAL_SAT_TAMPINHA"

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return None, None, None, "ERRO"


# if __name__ == "__main__":
#     logger.info("Inicializando classificador...")
#     MODEL, SCALER = load_classifier()