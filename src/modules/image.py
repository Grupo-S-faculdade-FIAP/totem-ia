from __future__ import annotations

import logging
import os
import traceback

import cv2  # pyright: ignore[reportMissingImports]
# import requests 
import joblib  # pyright: ignore[reportMissingImports]
from pathlib import Path
from skimage.feature import hog  # pyright: ignore[reportMissingImports]

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
SVM_SOFT_THRESHOLD      = -0.50  # decision_function > -0.5 → aceita (sem pista CV)
SVM_SOFT_THRESHOLD_HOUGH = -1.00  # quando Hough+contorno consistentes: aceita até conf > -1.0

# =============================================================================
# Validações de Visão Computacional (CV pre-screening)
# =============================================================================
CV_MIN_CIRCULARITY      = 0.78  # Tampinha: 0.90-0.98 | Rosto: 0.70-0.85 (bem relaxado)
CV_MIN_ASPECT_RATIO     = 0.78  # Bounding box ≈ quadrado | Rosto: 0.60-0.80
CV_MIN_ELLIPSE_ASPECT   = 0.78  # Elipse: tampinha≈1.0, rosto≈0.65-0.80
CV_MIN_CONTOUR_AREA     = 150   # pixels² — filtra olhos/botões pequenos
CV_MAX_CONTOUR_AREA     = 8500  # pixels² — rosto ≈ 9000-12000, tampinha r=50 ≈ 8300

# =============================================================================
# Seção 6 (ml-conventions): Caminhos de modelo — constantes, nunca inline
# =============================================================================
MODEL_PATH  = Path('models/svm/svm_model_complete.pkl')
SCALER_PATH = Path('models/svm/scaler_complete.pkl')

# ROI central: classifica apenas a area do circulo de verificacao (como bancos)
# 0.75 = 75% do centro - area maior para capturar tampinha inteira
ROI_CENTER_RATIO = 0.75

# HOG: paridade com trainer (8 cor + 324 HOG = 332 features)
HOG_ORIENTATIONS = 9
HOG_PIXELS_PER_CELL = (16, 16)
HOG_CELLS_PER_BLOCK = (2, 2)
HOG_SIZE = (64, 64)
# USE_ROI=false desativa o crop para teste (ver se aceitação melhora sem ROI)
USE_ROI = os.getenv("USE_ROI", "true").lower() in ("true", "1", "yes")

# Haar cascade para pré-filtro de rosto (rejeita antes do SVM)
_FACE_CASCADE: cv2.CascadeClassifier | None = None


def _get_face_cascade() -> cv2.CascadeClassifier | None:
    """Carrega Haar cascade de rosto uma vez (lazy)."""
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        try:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            _FACE_CASCADE = cv2.CascadeClassifier(path)
            if _FACE_CASCADE.empty():
                logger.warning("⚠️ Haar cascade de rosto não carregou")
                _FACE_CASCADE = None
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar face cascade: {e}")
            _FACE_CASCADE = None
    return _FACE_CASCADE


class ImageClassifier:
    def __init__(self):
        self.model = None
        self.scaler = None
        self._last_circularity = 0.0
        self._last_contour_count = 0.0
        self._last_aspect_ratio = 0.0
        self._last_ellipse_aspect = 0.0
        self._last_contour_area = 0.0
        self._last_hough_count = 0
        self._last_hough_consistent = False

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

    def _crop_to_roi_center(self, image: np.ndarray) -> np.ndarray:
        """Extrai regiao central (ROI) - area do circulo de verificacao. Ignora bordas."""
        h, w = image.shape[:2]
        size = int(min(h, w) * ROI_CENTER_RATIO)
        if size < 32:
            return image
        x = (w - size) // 2
        y = (h - size) // 2
        return image[y : y + size, x : x + size].copy()

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

            # HOG: features de forma (tampinha circular vs rosto oval)
            # Só inclui se o modelo esperar 332 features (8+HOG); modelo legado usa 8
            expected_n = getattr(self.scaler, "n_features_in_", None) if self.scaler is not None else 332
            if expected_n != 8:
                gray_hog = cv2.resize(gray, HOG_SIZE)
                hog_feats = hog(
                    gray_hog,
                    orientations=HOG_ORIENTATIONS,
                    pixels_per_cell=HOG_PIXELS_PER_CELL,
                    cells_per_block=HOG_CELLS_PER_BLOCK,
                    visualize=False,
                    channel_axis=None,
                )
                features.extend(hog_feats.astype(float).tolist())

            # CV metrics para pre-screening — não entram no vetor SVM
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Canny + contornos: circularidade e aspect ratio do maior contorno
            edges = cv2.Canny(blurred, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = float(len(contours))

            circularity = 0.0
            aspect_ratio = 0.0
            ellipse_aspect = 0.0
            contour_area = 0.0
            if contours:
                largest = max(contours, key=cv2.contourArea)
                contour_area = float(cv2.contourArea(largest))
                perim = cv2.arcLength(largest, True)
                circularity = (4 * np.pi * contour_area / (perim ** 2)) if perim > 0 else 0.0
                x, y, w, h = cv2.boundingRect(largest)
                aspect_ratio = float(min(w, h)) / float(max(w, h)) if max(w, h) > 0 else 0.0
                # Elipse ajustada: rosto é alongado (ellipse_aspect ~0.65), tampinha é redonda (~1.0)
                if len(largest) >= 5:
                    try:
                        (_, _), (ma, mb), _ = cv2.fitEllipse(largest)
                        ellipse_aspect = float(min(ma, mb)) / float(max(ma, mb)) if max(ma, mb) > 0 else 0.0
                    except cv2.error:
                        ellipse_aspect = aspect_ratio

            # HoughCircles: detecta círculos com borda bem definida (aro da tampinha).
            # param2=28 exige borda circular forte.
            hough_circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT,
                dp=1.2, minDist=30,
                param1=60, param2=28,
                minRadius=15, maxRadius=45
            )

            # Valida consistência Hough × contorno:
            # Se Hough detectou um círculo pequeno (olho, óculos) mas o maior contorno é grande
            # (rosto inteiro), o ratio de área será muito alto → rejeita.
            # Tampinha: contorno_area ≈ π × hough_r² → ratio ≈ 1.0.
            hough_count = 0
            hough_contour_consistent = False
            if hough_circles is not None:
                best_hough_r = float(max(hough_circles[0], key=lambda c: c[2])[2])
                hough_expected_area = np.pi * best_hough_r ** 2
                if contour_area > 0 and hough_expected_area > 0:
                    area_ratio_hough = contour_area / hough_expected_area
                    hough_contour_consistent = 0.4 <= area_ratio_hough <= 3.0
                else:
                    hough_contour_consistent = True  # sem contorno → confiar no Hough
                hough_count = int(len(hough_circles[0]))

            # Guardar CV metrics para pre-screening (não incluir no vetor SVM)
            self._last_circularity = float(circularity)
            self._last_contour_count = contour_count
            self._last_aspect_ratio = float(aspect_ratio)
            self._last_ellipse_aspect = float(ellipse_aspect)
            self._last_contour_area = float(contour_area)
            self._last_hough_count = hough_count
            self._last_hough_consistent = hough_contour_consistent

            # Vetor: 8 cor (+ HOG se modelo novo)
            return np.array(features, dtype=np.float64)
        except Exception as e:
            logger.error(f"Erro ao extrair features: {e}")
            return None


    def classify_image(self, image: np.ndarray | None, is_debug_mode: bool = False) -> tuple[int | None, float | None, float | None, str]:
        if image is None or self.model is None or self.scaler is None:
            logger.error(f"⚠️ Prerequisitos faltando: image={image is not None}, MODEL={self.model is not None}, SCALER={self.scaler is not None}")
            return None, None, None, "ERRO"

        try:
            logger.info(f"📸 Iniciando classificação. Imagem shape: {image.shape if image is not None else 'None'}")

            # ROI: classificar apenas area central (circulo de verificacao, como bancos)
            # USE_ROI=false usa imagem inteira para teste (Opção 2 do plano)
            image_for_features = self._crop_to_roi_center(image) if USE_ROI else image
            if USE_ROI:
                logger.info(f"📐 ROI central: {image_for_features.shape[1]}x{image_for_features.shape[0]} (ratio={ROI_CENTER_RATIO})")
            else:
                logger.info("📐 ROI desativado (USE_ROI=false) — usando imagem inteira")

            # Features e saturação calculados em uma única passagem (sem conversão HSV dupla)
            features = self.extract_color_features(image_for_features)
            if features is None or np.isnan(features).any():
                logger.error("❌ Erro ao extrair features")
                return None, None, None, "ERRO"

            saturation = float(features[6])  # features[6] = saturação média HSV
            circularity = self._last_circularity
            contour_count = self._last_contour_count
            aspect_ratio = self._last_aspect_ratio
            hough_count = self._last_hough_count
            hough_consistent = self._last_hough_consistent
            contour_area = self._last_contour_area
            ellipse_aspect = self._last_ellipse_aspect

            logger.info(f"✅ Features extraídas. Shape: {features.shape}, Saturação: {saturation:.1f}")
            logger.info(
                f"🔍 CV Metrics: hough={hough_count}, circ={circularity:.2f}, "
                f"aspect={aspect_ratio:.2f}, contornos={contour_count:.0f}"
            )

            # ========== PRÉ-FILTRO: DETECÇÃO DE ROSTO ==========
            # Rejeita imediatamente se rosto detectado (evita aceitar rosto como tampinha)
            face_cascade = _get_face_cascade()
            if face_cascade is not None:
                gray_roi = cv2.cvtColor(image_for_features, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray_roi, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
                )
                if len(faces) > 0:
                    logger.info(f"🚫 Rosto detectado ({len(faces)} região(ões)) → REJEITAR")
                    return 0, 0.95, saturation, "FACE_DETECTED"

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
                is_round_ellipse = ellipse_aspect >= CV_MIN_ELLIPSE_ASPECT or ellipse_aspect == 0
                is_size_ok = CV_MIN_CONTOUR_AREA <= contour_area <= CV_MAX_CONTOUR_AREA
                if not is_circular or not is_square_bbox or not is_round_ellipse or not is_size_ok:
                    reason = []
                    if not is_circular:
                        reason.append(f"circ={circularity:.2f}<{CV_MIN_CIRCULARITY}")
                    if not is_square_bbox:
                        reason.append(f"aspect={aspect_ratio:.2f}<{CV_MIN_ASPECT_RATIO}")
                    if not is_round_ellipse and ellipse_aspect > 0:
                        reason.append(f"ellipse={ellipse_aspect:.2f}<{CV_MIN_ELLIPSE_ASPECT}")
                    if not is_size_ok:
                        if contour_area > CV_MAX_CONTOUR_AREA:
                            reason.append(f"area={contour_area:.0f}>{CV_MAX_CONTOUR_AREA}(face?)")
                        else:
                            reason.append(f"area={contour_area:.0f}<{CV_MIN_CONTOUR_AREA}")
                    logger.warning(f"❌ CV Rejection: {', '.join(reason)}")
                    return 0, 0.90, saturation, f"CV_REJECT ({', '.join(reason)})"
                logger.info(f"✅ CV: contorno circular (circ={circularity:.2f}, aspect={aspect_ratio:.2f}, ellipse={ellipse_aspect:.2f}, area={contour_area:.0f})")
            else:
                logger.info("⚠️ CV: sem contornos detectados — SVM vai decidir")

            # ========== CLASSIFICAÇÃO SVM ==========
            features_scaled = self.scaler.transform([features])

            svm_pred = self.model.predict(features_scaled)[0]
            svm_conf = self.model.decision_function(features_scaled)[0]
            svm_prob = 1 / (1 + np.exp(-svm_conf))
            svm_margin = abs(float(svm_conf))

            # cv_confirmed_circle: CV confirma com SEGURANÇA que o objeto é circular.
            # OBRIGATÓRIO: contour_count > 0 — sem contorno detectado NUNCA aceitar.
            # (Hough sozinho aceita óculos/íris no rosto; contorno valida o objeto inteiro)
            area_ok = CV_MIN_CONTOUR_AREA <= contour_area <= CV_MAX_CONTOUR_AREA
            shape_ok = (
                circularity >= CV_MIN_CIRCULARITY
                and aspect_ratio >= CV_MIN_ASPECT_RATIO
                and (ellipse_aspect >= CV_MIN_ELLIPSE_ASPECT or ellipse_aspect == 0)
                and area_ok
            )
            hough_with_valid_shape = (
                contour_count > 0
                and hough_count > 0
                and hough_consistent
                and shape_ok
            )
            contour_circular = (
                contour_count > 0
                and shape_ok
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
                logger.info(f"✅ CV confirmou círculo → TAMPINHA")
                return 1, 0.85, saturation, "CV_CIRCLE_CONFIRMED"

            # SVM decide: threshold mais suave só quando Hough+contorno consistentes
            threshold = (
                SVM_SOFT_THRESHOLD_HOUGH
                if (hough_count > 0 and hough_consistent)
                else SVM_SOFT_THRESHOLD
            )
            svm_accept = svm_conf > threshold
            if svm_accept and saturation >= SAT_VERY_LOW_THRESHOLD:
                logger.info(f"✅ SVM aceita (conf={svm_conf:.2f}, threshold={threshold}, hough={hough_count})")
                return 1, 0.78, saturation, "SVM_ACCEPT"

            logger.info(f"❌ Rejeitado (conf={svm_conf:.2f}, pred={svm_pred}, threshold={threshold})")
            return 0, 0.90, saturation, "CV_NO_CIRCLE"

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return None, None, None, "ERRO"


# if __name__ == "__main__":
#     logger.info("Inicializando classificador...")
#     MODEL, SCALER = load_classifier()