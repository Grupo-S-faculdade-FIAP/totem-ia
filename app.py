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
import sqlite3
import time

# Importar agents e prompts
from prompts.agents_config import get_agent

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuração ESP32
ESP32_IP = os.getenv('ESP32_IP', '192.168.1.101')  # IP do ESP32 na rede local

# Rota para servir imagem de teste (para simulador ESP32)
@app.route('/test_tampinha.jpg')
def serve_test_image():
    """Serve a imagem de teste para o simulador ESP32"""
    test_image_path = Path('test_tampinha.jpg')
    if test_image_path.exists():
        return send_file(str(test_image_path), mimetype='image/jpeg')
    else:
        return jsonify({'error': 'Imagem de teste não encontrada'}), 404

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

@app.route('/esp32_simulator.html')
def esp32_simulator():
    return render_template('esp32_simulator.html', v=1)

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

@app.route('/test')
def test_page():
    """Página de teste para debug de JavaScript"""
    return render_template('test.html')

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
        import traceback
        logger.error(f"Erro no endpoint /classify: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'status': 'erro', 'traceback': traceback.format_exc()}, 500)

# ==============================================================================
# NOVA ROTA: Validação Completa (Software + Mecânica)
@app.route('/api/validate_mechanical', methods=['POST'])
def validate_mechanical():
    """Validação completa: Software (ML) + Mecânica (ESP32)"""
    try:
        # 1. Receber imagem
        if 'image' not in request.files:
            return jsonify({
                'error': 'Imagem não fornecida',
                'validation': 'FAIL'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'Nenhum arquivo selecionado',
                'validation': 'FAIL'
            }), 400
        
        # 2. Processar e classificar imagem
        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                'error': 'Erro ao processar imagem',
                'validation': 'FAIL'
            }), 400
        
        # 3. Classificar com SVM
        pred, conf, sat, method = classify_image(image)
        
        if pred is None:
            return jsonify({
                'error': 'Erro ao analisar a imagem',
                'validation': 'FAIL'
            }), 500
        
        is_tampinha = pred == 1
        
        # Se não é tampinha, rejeitar
        if not is_tampinha:
            return jsonify({
                'status': 'Objeto não é tampinha',
                'validation': 'FAIL',
                'confidence': float(conf),
                'message': 'Por favor, deposite apenas tampinhas!'
            }), 400
        
        # 4. Se ML OK, obter dados de verificação mecânica
        # Tenta conectar ao ESP32 real, se falhar, simula resposta
        try:
            logger.info(f"📡 Sinalizando ESP32 em {ESP32_IP} para verificação mecânica...")
            
            esp32_response = requests.post(
                f'http://{ESP32_IP}/check_mechanical',
                json={'validation': 'OK'},
                timeout=5
            )
            
            esp32_data = esp32_response.json()
            logger.info(f"✅ Resposta ESP32 Real: {esp32_data}")
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            # Se ESP32 não está disponível, simular resposta (modo de desenvolvimento)
            logger.warning(f"⚠️ ESP32 não acessível, usando simulação de sensores")
            esp32_data = {
                'presence_detected': True,  # Simular presença detectada
                'weight_ok': True,          # Simular peso OK
                'weight_value': 2500,       # Simular valor de peso
                'timestamp': int(time.time()),
                'simulated': True
            }
            logger.info(f"✅ Resposta ESP32 Simulada: {esp32_data}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao comunicar com ESP32: {str(e)}")
            return jsonify({
                'error': f'Erro ao comunicar com ESP32: {str(e)}',
                'validation': 'OK',
                'mechanical': 'UNKNOWN',
                'confidence': float(conf),
                'message': 'Erro na verificação mecânica. Tente novamente.'
            }), 500
        
        # 5. Verificar resultado mecânico
        presence = esp32_data.get('presence_detected', esp32_data.get('presence', False))
        weight_ok = esp32_data.get('weight_ok', False)
        
        if presence and weight_ok:
            # Salvar depósito bem-sucedido no banco
            save_deposit_data(conf, presence, weight_ok, esp32_data.get('weight_value', 0))
            
            impact = calculate_environmental_impact()
            
            return jsonify({
                'status': 'Depósito autorizado!',
                'validation': 'OK',
                'mechanical': 'OK',
                'confidence': float(conf),
                'impacto': impact,
                'message': '✅ Tampinha depositada com sucesso!',
                'presence': presence,
                'weight_ok': weight_ok,
                'color': 'green'
            }), 200
        else:
            # Falha na verificação mecânica
            logger.warning(f"❌ Verificação mecânica falhou: presença={presence}, peso={weight_ok}")
            
            return jsonify({
                'status': 'Erro na verificação mecânica',
                'validation': 'OK',
                'mechanical': 'FAIL',
                'confidence': float(conf),
                'presence': presence,
                'weight_ok': weight_ok,
                'message': 'Falha ao detectar tampinha no depósito. Tente novamente.',
                'color': 'red'
            }), 400

    except Exception as outer_error:
        logger.error(f"❌ Erro no endpoint /validate_mechanical: {outer_error}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(outer_error),
            'validation': 'FAIL',
            'traceback': traceback.format_exc()
        }), 500

# ==============================================================================
# FUNÇÕES AUXILIARES PARA VALIDAÇÃO MECÂNICA

def save_deposit_data(ml_confidence, presence_detected, weight_ok, weight_value):
    """Salva dados da interação no banco SQLite"""
    try:
        conn = sqlite3.connect('totem_data.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            ml_confidence REAL,
            presence_detected BOOLEAN,
            weight_value INTEGER,
            weight_ok BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        c.execute('''INSERT INTO deposits 
                     (timestamp, ml_confidence, presence_detected, weight_value, weight_ok) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (time.time(), ml_confidence, presence_detected, weight_value, weight_ok))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Depósito salvo no banco de dados")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar depósito: {e}")

def calculate_environmental_impact():
    """Calcula e retorna impacto ambiental por tampinha"""
    return {
        'plastico_reciclado_g': 0.5,
        'co2_evitado_g': 2.3,
        'agua_economizada_ml': 15,
        'arvores_preservadas_cm2': 8
    }

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
    
    # Arquivo único de áudio pré-gerado com o script completo (~55 segundos)
    audio_file = audio_dir / 'sustainability_speech.wav'
    
    # Se arquivo existe, usar ele
    if audio_file.exists():
        logger.info("✅ Usando áudio pré-gerado completo (55s)")
        return str(audio_file)
    
    # Se não existe, criar placeholder
    if not audio_file.exists():
        logger.warning("⚠️ Nenhum áudio pré-gerado encontrado!")
        logger.info("💡 Áudio esperado em: static/audio/sustainability_speech.wav")
        
        # Criar arquivo silencioso como fallback
        try:
            import wave
            import struct
            logger.warning("⚠️ Criando arquivo WAV de silêncio como placeholder...")
            sample_rate = 16000
            duration = 2
            num_samples = sample_rate * duration
            
            with wave.open(str(audio_file), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))
        except Exception as e:
            logger.error(f"❌ Erro ao criar placeholder: {e}")
            return None
    
    return str(audio_file)

@app.route('/api/speech/sustainability', methods=['GET'])
def get_sustainability_speech():
    """
    Retorna o arquivo de áudio sobre sustentabilidade
    """
    try:
        logger.debug(f"🎵 Requisição de áudio recebida. Cache: {request.args.get('t', 'N/A')}")
        
        # Usar cache quando disponível
        audio_file = generate_sustainability_speech(use_cache=True)
        
        if audio_file and Path(audio_file).exists():
            file_path = Path(audio_file)
            file_size = file_path.stat().st_size
            
            logger.info(f"📤 Servindo áudio: {audio_file} ({file_size} bytes)")
            
            # Determinar tipo MIME
            file_ext = file_path.suffix.lower()
            if file_ext == '.wav':
                mimetype = 'audio/wav'
            elif file_ext == '.mp3':
                mimetype = 'audio/mpeg'
            else:
                mimetype = 'audio/wav'  # padrão
            
            # Usar send_file com range support
            response = send_file(
                str(file_path),
                mimetype=mimetype,
                as_attachment=False,
                download_name='sustainability_speech.wav'
            )
            
            # Adicionar headers para streaming
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['Access-Control-Allow-Origin'] = '*'
            
            logger.info(f"✅ Áudio servido com sucesso")
            return response
        else:
            logger.error(f"❌ Arquivo de áudio não encontrado: {audio_file}")
            return jsonify({'error': 'Arquivo de áudio não disponível'}), 500
            
    except Exception as e:
        logger.error(f"❌ Erro ao servir áudio: {e}", exc_info=True)
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