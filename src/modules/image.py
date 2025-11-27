import logging
import cv2  # pyright: ignore[reportMissingImports]
import logging
# import requests 
import joblib  # pyright: ignore[reportMissingImports]
from pathlib import Path

import numpy as np  # pyright: ignore[reportMissingImports]


logger = logging.getLogger(__name__)


def load_classifier():
    try:
        model_path = Path('models/svm/svm_model_complete.pkl')
        scaler_path = Path('models/svm/scaler_complete.pkl')

        if not model_path.exists() or not scaler_path.exists():
            logger.error(f"❌ Arquivos do modelo não encontrados!")
            logger.error(f"   - Procurando em: {model_path.absolute()}")
            logger.error(f"   - Procurando em: {scaler_path.absolute()}")
            return None, None

        model = joblib.load(str(model_path))
        scaler = joblib.load(str(scaler_path))
        logger.info("✅ Modelo SVM carregado com sucesso!")
        return model, scaler
    except Exception as e:
        logger.error(f"❌ Erro ao carregar modelo: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# Carregar modelo na inicialização
logger.info("Inicializando classificador...")
MODEL, SCALER = load_classifier()


def extract_color_features(image):
    try:
        logger.debug(f"🔍 extract_color_features iniciada. Image type: {type(image)}, shape: {image.shape if hasattr(image, 'shape') else 'N/A'}")
        
        if not isinstance(image, np.ndarray):
            logger.error(f"❌ Imagem não é numpy array! Tipo: {type(image)}")
            return None
        
        # Verificar cv2
        if 'cv2' not in globals():
            logger.error("❌ cv2 não está em globals()")
            return None
            
        image = cv2.resize(image, (128, 128))
        logger.debug(f"✅ Imagem redimensionada para 128x128")

        # Extrair apenas 8 features para match com modelo
        features = []

        # 1-3: Mean, Std, Median do canal B
        b_channel = cv2.split(image)[0]
        features.extend([
            np.mean(b_channel),
            np.std(b_channel),
            np.median(b_channel)
        ])

        # 4-6: Mean, Std, Median do canal G
        g_channel = cv2.split(image)[1]
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


def classify_image(image, is_debug_mode=False):
    if image is None or MODEL is None or SCALER is None:
        logger.error(f"⚠️ Prerequisitos faltando: image={image is not None}, MODEL={MODEL is not None}, SCALER={SCALER is not None}")
        return None, None, None, "ERRO"

    try:
        logger.info(f"📸 Iniciando classificação. Imagem shape: {image.shape if image is not None else 'None'}")
        
        # Verificar se cv2 está disponível
        if not hasattr(cv2, 'cvtColor'):
            logger.error("❌ ERRO CRÍTICO: cv2 módulo não está completo!")
            return None, None, None, "ERRO"
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        logger.info(f"✅ HSV convertido. Saturação: {saturation:.1f}")

        features = extract_color_features(image)
        if features is None or np.isnan(features).any():
            logger.error("❌ Erro ao extrair features")
            return None, None, saturation, "ERRO"
        
        logger.info(f"✅ Features extraídas. Shape: {features.shape}")

        features_scaled = SCALER.transform([features])

        svm_pred = MODEL.predict(features_scaled)[0]
        svm_conf = MODEL.decision_function(features_scaled)[0]
        svm_prob = 1 / (1 + np.exp(-svm_conf))

        logger.info(f"🔍 SVM: pred={svm_pred}, conf={svm_conf:.2f}, prob={svm_prob:.2f}, sat={saturation:.1f}")

        # Em modo debug, aceitar tampinha com confiança alta
        if is_debug_mode and saturation > 50:
            logger.info("🐛 MODO DEBUG: Aceitando como tampinha")
            return 1, 0.95, saturation, "DEBUG_MODE"

        if saturation > 120:
            confidence = 0.95 if svm_pred == 1 else 0.90
            return 1, confidence, saturation, "SAT_HIGH"
        elif saturation < 30:
            confidence = 0.95
            return 0, confidence, saturation, "SAT_VERY_LOW"
        else:
            if saturation > 100:
                if svm_pred == 1:
                    return 1, 0.75, saturation, "MID_HIGH_SAT"
                else:
                    return 1, 0.70, saturation, "ACCEPT_MID_SAT"  # Aceitar tampinhas com sat media
            elif saturation < 50:
                return 1, 0.75, saturation, "LOW_SAT_FORCE_TAMPINHA"
            else:
                # Saturação entre 50-100: aceitar como tampinha
                return 1, 0.80, saturation, "NORMAL_SAT_TAMPINHA"

    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        return None, None, None, "ERRO"