#!/usr/bin/env python3
"""
TOTEM IA - API Flask para Classificação de Tampinhas
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
import joblib
from pathlib import Path
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import openai
import requests

# Importar agents e prompts
from prompts.agents_config import get_agent

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configurar OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
hf_token = os.getenv('HUGGINGFACE_TOKEN')

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

# ==============================================================================
# FUNÇÃO DE EXTRAÇÃO DE FEATURES
def extract_color_features(image):
    try:
        image = cv2.resize(image, (128, 128))

        features = []

        for channel in cv2.split(image):
            features.extend([
                np.mean(channel),
                np.std(channel),
                np.median(channel)
            ])

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        for channel in cv2.split(hsv):
            features.extend([
                np.mean(channel),
                np.std(channel),
                np.median(channel)
            ])

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

def classify_image(image):
    if image is None or MODEL is None or SCALER is None:
        return None, None, None, "ERRO"

    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])

        features = extract_color_features(image)
        if features is None or np.isnan(features).any():
            return None, None, saturation, "ERRO"

        features_scaled = SCALER.transform([features])

        svm_pred = MODEL.predict(features_scaled)[0]
        svm_conf = MODEL.decision_function(features_scaled)[0]
        svm_prob = 1 / (1 + np.exp(-svm_conf))

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
                    return 0, 0.65, saturation, "NOT_TAMPINHA"
            elif saturation < 50:
                return 1, 0.75, saturation, "LOW_SAT_FORCE_TAMPINHA"
            else:
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
    return render_template('totem_intro.html', v=1)

@app.route('/totem_intro.html')
def totem_intro():
    return render_template('totem_intro.html', v=1)

@app.route('/totem_v2.html')
def totem_v2():
    return render_template('totem_v2.html', v=1)

@app.route('/processing')
def processing():
    """Tela de processamento e confirmação de tampinha"""
    return render_template('processing.html', v=99)  # Aumentar v força reload

@app.route('/finalization')
def finalization():
    """Tela de finalização com agradecimento e impacto ambiental"""
    return render_template('finalization.html', v=1)

@app.route('/rewards')
def rewards():
    """Dashboard de recompensas e pontos (legado - redireciona para finalization)"""
    return render_template('finalization.html', v=1)

@app.route('/api/classify', methods=['POST'])
def api_classify():
    try:
        image = None

        if request.is_json:
            data = request.get_json()

            if not data or 'image' not in data:
                return jsonify({'error': 'Nenhuma imagem fornecida'}), 400

            image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        elif 'file' in request.files:
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
            if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({'error': 'Tipo de arquivo nao permitido. Use: PNG, JPG, JPEG, GIF, BMP'}), 400
            
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > 10 * 1024 * 1024:
                return jsonify({'error': 'Arquivo muito grande. Maximo 10MB'}), 400
            
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': 'Envie uma imagem em base64 ou como arquivo'}), 400

        if image is None:
            return jsonify({'error': 'Erro ao processar imagem'}), 400

        pred, conf, sat, method = classify_image(image)

        if pred is None:
            return jsonify({
                'status': 'erro',
                'message': 'Erro ao analisar a imagem. Tente novamente.',
                'timestamp': datetime.now().isoformat()
            }), 500

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
    model_loaded = MODEL is not None and SCALER is not None
    return jsonify({
        'status': 'ok' if model_loaded else 'erro',
        'model_loaded': model_loaded,
        'timestamp': datetime.now().isoformat()
    })

# ==============================================================================
# TEXT-TO-SPEECH - SUSTENTABILIDADE
# ==============================================================================

def generate_sustainability_speech(use_cache=True):
    """
    Retorna arquivo de áudio sobre sustentabilidade (pré-gerado)
    """
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivo final pré-gerado com o script completo (~55 segundos)
    final_audio = audio_dir / 'sustainability_speech_final.wav'
    cache_audio = audio_dir / 'sustainability_speech.wav'
    
    # Se arquivo final pré-gerado existe, usar ele
    if final_audio.exists():
        logger.info("✅ Usando áudio pré-gerado completo (55s)")
        # SEMPRE copiar o arquivo final (garante que está atualizado)
        import shutil
        shutil.copy(str(final_audio), str(cache_audio))
        return str(cache_audio)
    
    # Se cache existe, usar
    if use_cache and cache_audio.exists():
        logger.info("✅ Usando áudio em cache")
        return str(cache_audio)
    
    logger.warning("⚠️ Nenhum áudio pré-gerado encontrado!")
    logger.info("💡 Execute: python3 generate_final_audio.py")
    
    # Fallback: retornar arquivo placeholder/silêncio
    try:
        import wave
        import struct
        logger.warning("⚠️ Criando arquivo WAV de silêncio como placeholder...")
        sample_rate = 16000
        duration = 2
        num_samples = sample_rate * duration
        
        with wave.open(str(cache_audio), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for _ in range(num_samples):
                wav_file.writeframes(struct.pack('<h', 0))
        
        return str(cache_audio)
    except Exception as e:
        logger.error(f"❌ Erro ao criar placeholder: {e}")
        return None

@app.route('/api/speech/sustainability', methods=['GET'])
def get_sustainability_speech():
    """
    Retorna o arquivo de áudio sobre sustentabilidade
    """
    try:
        # Sempre regenerar para garantir conteúdo atualizado
        audio_file = generate_sustainability_speech(use_cache=False)
        
        if audio_file and Path(audio_file).exists():
            file_ext = Path(audio_file).suffix.lower()
            
            # Detectar tipo MIME baseado na extensão
            if file_ext == '.wav':
                mimetype = 'audio/wav'
            elif file_ext == '.mp3':
                mimetype = 'audio/mpeg'
            else:
                mimetype = 'audio/mpeg'  # padrão
            
            return send_file(
                audio_file,
                mimetype=mimetype,
                as_attachment=False
            )
        else:
            return jsonify({'error': 'Arquivo de áudio não disponível'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao servir áudio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speech/info', methods=['GET'])
def get_speech_info():
    """
    Retorna informações sobre o áudio de sustentabilidade
    """
    try:
        audio_file = Path('static/audio/sustainability_speech.wav')
        
        info = {
            'available': audio_file.exists(),
            'size': audio_file.stat().st_size if audio_file.exists() else 0,
            'url': '/api/speech/sustainability'
        }
        
        return jsonify(info)
    except Exception as e:
        logger.error(f"Erro ao obter informações do áudio: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*80)
    print("TOTEM IA - API FLASK")
    print("   Sistema de Deposito Inteligente de Tampinhas")
    print("="*80)
    print()
    
    if MODEL is None or SCALER is None:
        print("AVISO: Modelo nao carregado!")
        print("   O servidor ira retornar erros ao tentar classificar.")
        print("   Verifique se os arquivos existem:")
        print("   - models/svm/svm_model_complete.pkl")
        print("   - models/svm/scaler_complete.pkl")
        print()
    
    print("Servidor iniciando em http://0.0.0.0:5003")
    print("   Acesse http://localhost:5003 no navegador")
    print()
    print("="*80)
    print()

    try:
        app.run(host='0.0.0.0', port=5005, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuario.")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()