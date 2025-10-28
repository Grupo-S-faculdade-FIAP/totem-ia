#!/usr/bin/env python3
"""
TOTEM IA - API Flask para Classificação de Tampinhas
=====================================================

Interface backend para o totem inteligente de deposito de tampinhas.
Integra o classificador híbrido v2 com endpoints REST.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
import joblib
from pathlib import Path
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ==============================================================================
# CARREGAMENTO DO MODELO
# ==============================================================================

def load_classifier():
    """Carrega o modelo SVM treinado"""
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

# ==============================================================================
# FUNÇÃO DE EXTRAÇÃO DE FEATURES
# ==============================================================================

def extract_color_features(image):
    """Extrai 24 features da imagem (numpy array)"""
    try:
        # Redimensionar
        image = cv2.resize(image, (128, 128))

        features = []

        # RGB stats (9)
        for channel in cv2.split(image):
            features.extend([
                np.mean(channel),
                np.std(channel),
                np.median(channel)
            ])

        # HSV stats (9)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for channel in cv2.split(hsv):
            features.extend([
                np.mean(channel),
                np.std(channel),
                np.median(channel)
            ])

        # Shape features (6)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)

            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = float(w) / h if h > 0 else 0

            hull = cv2.convexHull(largest_contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0

            features.extend([
                area/10000,
                perimeter/1000,
                circularity,
                aspect_ratio,
                solidity,
                hull_area/10000
            ])
        else:
            features.extend([0, 0, 0, 0, 0, 0])

        return np.array(features)
    except Exception as e:
        logger.error(f"Erro ao extrair features: {e}")
        return None

# ==============================================================================
# FUNÇÃO DE CLASSIFICAÇÃO HÍBRIDA
# ==============================================================================

def classify_image(image):
    """Classifica imagem usando o método híbrido v2"""
    if image is None or MODEL is None or SCALER is None:
        return None, None, None, "ERRO"

    try:
        # Análise de saturação HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])

        # Extrair features SVM
        features = extract_color_features(image)
        if features is None or np.isnan(features).any():
            return None, None, saturation, "ERRO"

        features_scaled = SCALER.transform([features])

        # Predição SVM
        svm_pred = MODEL.predict(features_scaled)[0]
        svm_conf = MODEL.decision_function(features_scaled)[0]
        svm_prob = 1 / (1 + np.exp(-svm_conf))

        # Regra Híbrida AJUSTADA
        if saturation > 120:  # Tampinhas com saturação alta
            confidence = 0.95 if svm_pred == 1 else 0.90
            return 1, confidence, saturation, "SAT_HIGH"
        elif saturation < 30:  # Saturação muito baixa = NÃO-TAMPINHA
            confidence = 0.95
            return 0, confidence, saturation, "SAT_VERY_LOW"
        else:  # Zona intermediária
            if saturation > 100:  # 100-120
                if svm_pred == 1:
                    return 1, 0.75, saturation, "MID_HIGH_SAT"
                else:
                    return 0, 0.65, saturation, "NOT_TAMPINHA"
            elif saturation < 50:  # 30-50: FORÇAR TAMPINHA
                return 1, 0.75, saturation, "LOW_SAT_FORCE_TAMPINHA"
            else:  # 50-100
                if svm_pred == 1 and svm_prob > 0.8:
                    return 1, svm_prob, saturation, "SVM_HIGH_CONF"
                else:
                    return 0, max(0.7, 1-svm_prob), saturation, "NOT_TAMPINHA"

    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        return None, None, None, "ERRO"

# ==============================================================================
# ROTAS HTTP
# ==============================================================================

@app.route('/')
def index():
    """Página principal do totem"""
    return render_template('totem.html')

@app.route('/api/classify', methods=['POST'])
def api_classify():
    """
    Endpoint para classificar imagem
    
    Recebe: POST com imagem em base64
    Retorna: JSON com classificação e detalhes
    """
    try:
        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'Nenhuma imagem fornecida'}), 400

        # Decodificar imagem base64
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': 'Erro ao processar imagem'}), 400

        # Classificar
        pred, conf, sat, method = classify_image(image)

        if pred is None:
            return jsonify({
                'status': 'erro',
                'message': 'Erro ao analisar a imagem. Tente novamente.',
                'timestamp': datetime.now().isoformat()
            }), 500

        # Preparar resposta
        is_tampinha = pred == 1

        response = {
            'status': 'sucesso' if is_tampinha else 'rejeitado',
            'is_tampinha': is_tampinha,
            'classification': 'TAMPINHA ACEITA!' if is_tampinha else 'NAO E TAMPINHA',
            'confidence': float(conf),
            'saturation': float(sat),
            'method': method,
            'timestamp': datetime.now().isoformat()
        }

        if is_tampinha:
            response['message'] = 'Tampinha aceita! Deposite na esteira.'
            response['color'] = 'green'
            response['icon'] = 'check'
        else:
            response['message'] = 'Item rejeitado. Por favor, deposite apenas tampinhas!'
            response['color'] = 'red'
            response['icon'] = 'times'

        logger.info(f"Classificação: {response['classification']} (conf: {conf:.2f}, sat: {sat:.1f})")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Erro no endpoint /classify: {e}")
        return jsonify({'error': str(e), 'status': 'erro'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check do servidor"""
    model_loaded = MODEL is not None and SCALER is not None
    return jsonify({
        'status': 'ok' if model_loaded else 'erro',
        'model_loaded': model_loaded,
        'timestamp': datetime.now().isoformat()
    })

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print("="*80)
    print("🏆 TOTEM IA - API FLASK")
    print("   Sistema de Deposito Inteligente de Tampinhas")
    print("="*80)
    print()
    
    if MODEL is None or SCALER is None:
        print("⚠️  AVISO: Modelo não carregado!")
        print("   O servidor irá retornar erros ao tentar classificar.")
        print("   Verifique se os arquivos existem:")
        print("   - models/svm/svm_model_complete.pkl")
        print("   - models/svm/scaler_complete.pkl")
        print()
    
    print("✅ Servidor iniciando em http://0.0.0.0:5000")
    print("   Acesse http://localhost:5000 no navegador")
    print()
    print("="*80)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)