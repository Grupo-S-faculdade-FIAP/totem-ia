#!/usr/bin/env python3

import logging
import os
import base64
import time
import traceback
import random

import cv2
import joblib
import numpy as np
import openai
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

from datetime import datetime
from pathlib import Path

from src.database.db import DatabaseConnection

from dotenv import load_dotenv


# Importar agents e prompts
# from prompts.agents_config import get_agent

from src.modules.image import ImageClassifier

from src.hardware.esp32 import ESP32_API_URL, get_esp32_sensors, calculate_environmental_impact, check_esp32_mechanical, confirm_esp32_detection

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 🐛 Configurar pasta de imagens como estática
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
images_folder = os.path.join(os.path.dirname(__file__), 'images')
app.config['IMAGES_FOLDER'] = images_folder

# ============================================================================
# 🐛 MODO DEBUG - ATIVAR PARA AMBIENTE DE DESENVOLVIMENTO
# ============================================================================
# ⚠️  NUNCA ATIVAR EM PRODUÇÃO!
# Quando TRUE: Botão "Modo Debug Confirmar" aparecerá na interface
# Permite validar tampinha automaticamente sem usar modelo ML
# ============================================================================
MODO_DEBUG = os.getenv('MODO_DEBUG', 'False').lower() == 'true'

if MODO_DEBUG:
    logger.warning("🐛 ⚠️  MODO DEBUG ATIVADO! Botão de confirmação automática será exibido.")
    logger.warning("⚠️  NUNCA USE EM PRODUÇÃO!")
else:
    logger.info("✅ Modo Debug desativado (Produção)")


# ============================================================================
# CONSTANTES
# ============================================================================
PESO_MIN_TAMPINHA = 2400  # gramas
PESO_MAX_TAMPINHA = 2800  # gramas
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Configuração ESP32 LOCAL (para fallback)
ESP32_IP = os.getenv('ESP32_IP', '192.168.1.101')  # IP do ESP32 na rede local

image_classifier: ImageClassifier | None = None
db_connection: DatabaseConnection | None = None

# Rota para servir imagem de teste (para simulador ESP32)
@app.route('/test_tampinha.jpg')
def serve_test_image():
    """Serve a imagem de teste para o simulador ESP32"""
    test_image_path = Path('test_tampinha.jpg')
    if test_image_path.exists():
        return send_file(str(test_image_path), mimetype='image/jpeg')
    else:
        return jsonify({'error': 'Imagem de teste não encontrada'}), 404

openai.api_key = os.getenv('OPENAI_API_KEY')
hf_token = os.getenv('HUGGINGFACE_TOKEN')


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    return render_template('totem_intro.html', v=1)

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html', v=1)

@app.route('/admin')
def admin():
    return render_template('admin_login.html', v=1)

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', v=1)

@app.route('/totem_intro.html')
def totem_intro():
    return render_template('totem_intro.html', v=1)

@app.route('/totem_v2.html')
def totem_v2():
    # 🐛 Passar flag MODO_DEBUG para o template
    return render_template('totem_v2.html', v=1, modo_debug=MODO_DEBUG)

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


# 🐛 ROTA PARA SERVIR IMAGENS DO MODO DEBUG
@app.route('/debug-image/<filename>')
def serve_debug_image(filename):
    """Serve imagens da pasta /images para modo debug"""
    try:
        images_folder = app.config['IMAGES_FOLDER']
        file_path = os.path.join(images_folder, filename)
        
        # Validar que o arquivo existe e está dentro da pasta permitida
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            logger.warning(f"🐛 DEBUG: Arquivo não encontrado: {filename}")
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        logger.info(f"🐛 DEBUG: Servindo imagem: {filename}")
        return send_file(file_path, mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"❌ Erro ao servir imagem debug: {str(e)}")
        return jsonify({'error': str(e)}), 500


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
            
            allowed_extensions = ALLOWED_EXTENSIONS
            if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({'error': 'Tipo de arquivo nao permitido. Use: PNG, JPG, JPEG, GIF, BMP'}), 400
            
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE_BYTES:
                return jsonify({'error': 'Arquivo muito grande. Maximo 10MB'}), 400
            
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': 'Envie uma imagem em base64 ou como arquivo'}), 400

        if image is None:
            return jsonify({'error': 'Erro ao processar imagem'}), 400

        pred, conf, sat, method = image_classifier.classify_image(image, is_debug_mode=MODO_DEBUG) if image_classifier else (None, None, None, None)

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
            'confidence': float(conf) if conf is not None else None,
            'saturation': float(sat) if sat is not None else None,
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
        logger.error(f"Erro no endpoint /classify: {e}", exc_info=True)
        return jsonify({
            'error': 'Erro interno ao classificar imagem',
            'status': 'erro',
            'timestamp': datetime.now().isoformat()
        }), 500


# =============================================================================
# NOVA ROTA: Validação Mecânica (Presença + Peso para ESP32)
# =============================================================================
@app.route('/api/validate-mechanical', methods=['POST'])
def api_validate_mechanical():
    """
    Validação mecânica apenas - recebe presença e peso
    Valida e retorna resultado
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request deve ser JSON'}), 400
        
        data = request.get_json()
        presenca = data.get('presenca', True)
        peso = data.get('peso', 2600)
        
        logger.info(f"🔍 Validação Mecânica: presença={presenca}, peso={peso}")
        
        # Validar condições mecânicas
        is_valid = presenca and PESO_MIN_TAMPINHA <= peso <= PESO_MAX_TAMPINHA
        
        if is_valid:
            logger.info("✅ Validação Mecânica: APROVADO")
            return jsonify({
                'status': 'aprovado',
                'message': 'Validação mecânica aprovada',
                'presenca': presenca,
                'peso': peso,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            reason = []
            if not presenca:
                reason.append("Presença não detectada")
            if peso < PESO_MIN_TAMPINHA or peso > PESO_MAX_TAMPINHA:
                reason.append(f"Peso fora do intervalo (recebido: {peso}g)")
            
            logger.warning(f"❌ Validação Mecânica: REJEITADO - {', '.join(reason)}")
            return jsonify({
                'status': 'rejeitado',
                'message': ', '.join(reason),
                'presenca': presenca,
                'peso': peso,
                'timestamp': datetime.now().isoformat()
            }), 200
    
    except Exception as e:
        logger.error(f"Erro na validação mecânica: {e}", exc_info=True)
        return jsonify({
            'error': 'Erro interno na validação mecânica',
            'status': 'erro',
            'timestamp': datetime.now().isoformat()
        }), 500


# =============================================================================
# ROTA ANTIGA: Validação Completa (Software + Mecânica com ESP32) 
# =============================================================================
@app.route('/api/validate-complete', methods=['POST'])
def api_validate_complete():
    """
    Validação completa de tampinha:
    1. Classificação via SVM
    2. Confirmação mecânica via ESP32
    3. Retorna resultado
    """
    try:
        image = None

        # Processar imagem igual ao /api/classify
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
            
            if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                return jsonify({'error': 'Tipo de arquivo nao permitido'}), 400
            
            file_bytes = file.read()
            nparr = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': 'Envie uma imagem em base64 ou como arquivo'}), 400

        if image is None:
            return jsonify({'error': 'Erro ao processar imagem'}), 400

        # ========== ETAPA 1: Classificação Software ==========
        pred, conf, sat, method = image_classifier.classify_image(image) if image_classifier else (None, None, None, None)
        
        if pred is None:
            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_DESCONHECIDO)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            return jsonify({
                'status': 'erro_classificacao',
                'message': 'Erro ao classificar imagem',
                'timestamp': datetime.now().isoformat()
            }), 500

        is_tampinha = pred == 1
        if not is_tampinha:
            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.REJEITADO)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            # Se não é tampinha, rejeita imediatamente
            logger.warning(f"❌ Item rejeitado: não é tampinha (conf: {conf:.2f})")
            return jsonify({
                'status': 'rejeitado',
                'stage': 'classificacao',
                'message': 'Item rejeitado - Não é tampinha',
                'classification': 'NAO E TAMPINHA',
                'confidence': float(conf) if conf is not None else None,
                'timestamp': datetime.now().isoformat()
            }), 200

        logger.info(f"✅ Classificação OK: TAMPINHA (conf: {conf:.2f})")

        # ========== ETAPA 2: Validação Mecânica (ESP32) ==========
        logger.info("📡 Enviando para validação mecânica no ESP32...")
        
        # Obter sensores do ESP32 ou usar valores do request
        sensors = get_esp32_sensors()
        
        # Se recebeu presenca e peso no request, usar esses valores
        if request.is_json:
            data = request.get_json()
            if 'presenca' in data:
                presenca = data.get('presenca', True)
            elif sensors:
                presenca = sensors.get('presenca', True)
            else:
                presenca = True
                
            if 'peso' in data:
                peso = data.get('peso', 2600)
            elif sensors:
                peso = sensors.get('peso', 2600)
            else:
                peso = 2600
        else:
            if not sensors:
                logger.warning("⚠️ Não conseguiu ler sensores, mas continuando...")
                presenca = True
                peso = 2600
            else:
                presenca = sensors.get('presenca', True)
                peso = sensors.get('peso', 2600)
        
        logger.info(f"📊 Sensores: presença={presenca}, peso={peso}")

        # Verificar condição mecânica
        esp32_check = check_esp32_mechanical(presenca, peso)
        
        if not esp32_check:
            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_MECANICA)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            logger.warning("⚠️ Erro ao verificar condição mecânica")
            return jsonify({
                'status': 'erro_esp32',
                'message': 'Erro ao comunicar com ESP32',
                'timestamp': datetime.now().isoformat()
            }), 500

        # ========== ETAPA 3: Resultado Final ==========
        
        # Confirmar detecção
        confirm_esp32_detection('tampinha', float(conf) if conf is not None else 0.0)

        if db_connection:
            with db_connection as db:
                
                deposit_id = db.save_deposit_data(conf, True, True, 2500, True)

                db.save_interaction(DatabaseConnection.ResultadoInteracao.SUCESSO, deposit_id)

                
        else:
            logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

        logger.info("✅ VALIDAÇÃO COMPLETA: TAMPINHA ACEITA!")
        
        response = {
            'status': 'sucesso',
            'message': 'Tampinha aceita e validada!',
            'stages': {
                'classificacao': {
                    'status': 'sucesso',
                    'is_tampinha': True,
                    'confidence': float(conf) if conf is not None else None,
                    'saturation': float(sat) if sat is not None else None,
                    'method': method
                },
                'mecanica': {
                    'status': 'sucesso',
                    'presenca': presenca,
                    'peso': peso,
                    'esp32_response': esp32_check
                }
            },
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Erro em /validate-complete: {e}", exc_info=True)
        return jsonify({
            'status': 'erro',
            'error': 'Erro interno na validação completa',
            'timestamp': datetime.now().isoformat()
        }), 500


# =============================================================================
# NOVA ROTA: Health Check ESP32 
# =============================================================================
@app.route('/api/esp32-health', methods=['GET'])
def esp32_health():

    try:
        response = requests.get(
            f"{ESP32_API_URL}/api/health",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify({
                'status': 'online',
                'esp32': response.json(),
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'offline',
                'message': f'ESP32 retornou {response.status_code}',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        logger.error(f"❌ Erro ao verificar ESP32: {e}")
        return jsonify({
            'status': 'offline',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


# =============================================================================
# NOVA ROTA: Validação Mecânica (apenas presença e peso - ESP32)
# =============================================================================
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
        pred, conf, sat, method = image_classifier.classify_image(image, is_debug_mode=MODO_DEBUG) if image_classifier else (None, None, None, None)
        
        if pred is None:
            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_DESCONHECIDO)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            return jsonify({
                'error': 'Erro ao analisar a imagem',
                'validation': 'FAIL'
            }), 500
        
        is_tampinha = pred == 1
        
        # Se não é tampinha, rejeitar
        if not is_tampinha:
            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_CLASSIFICACAO)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            return jsonify({
                'status': 'Objeto não é tampinha',
                'validation': 'FAIL',
                'confidence': float(conf) if conf is not None else None,
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
                'confidence': float(conf) if conf is not None else None,
                'message': 'Erro na verificação mecânica. Tente novamente.'
            }), 500
        
        # 5. Verificar resultado mecânico
        presence = esp32_data.get('presence_detected', esp32_data.get('presence', False))
        weight_ok = esp32_data.get('weight_ok', False)
        
        if presence and weight_ok:

            # return {
            #     'plastico_reciclado_g': 0.5,
            #     'co2_evitado_g': 2.3,
            #     'agua_economizada_ml': 15,
            #     'arvores_preservadas_cm2': 8
            # }
            impact = calculate_environmental_impact()
            plastico_reciclado_g = impact.get('plastico_reciclado_g', 0)

            if db_connection:
                with db_connection as db:
                    deposit_id = db.save_deposit_data(conf, presence, weight_ok, esp32_data.get('weight_value', 0), plastico_reciclado_g)

                    db.save_interaction(DatabaseConnection.ResultadoInteracao.SUCESSO, deposit_id)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")

            return jsonify({
                'status': 'Depósito autorizado!',
                'validation': 'OK',
                'mechanical': 'OK',
                'confidence': float(conf) if conf is not None else None,
                'impacto': impact,
                'message': '✅ Tampinha depositada com sucesso!',
                'presence': presence,
                'weight_ok': weight_ok,
                'color': 'green'
            }), 200
        else:
            logger.warning(f"❌ Verificação mecânica falhou: presença={presence}, peso={weight_ok}")

            if db_connection:
                with db_connection as db:
                    db.save_interaction(DatabaseConnection.ResultadoInteracao.ERRO_MECANICA)
            else:
                logger.warning("⚠️ Conexão com o banco de dados não estabelecida")
            
            return jsonify({
                'status': 'Erro na verificação mecânica',
                'validation': 'OK',
                'mechanical': 'FAIL',
                'confidence': float(conf) if conf is not None else None,
                'presence': presence,
                'weight_ok': weight_ok,
                'message': 'Falha ao detectar tampinha no depósito. Tente novamente.',
                'color': 'red'
            }), 400

    except Exception as outer_error:
        logger.error(f"❌ Erro no endpoint /validate_mechanical: {outer_error}", exc_info=True)
        return jsonify({
            'error': 'Erro interno na validação mecânica',
            'validation': 'FAIL',
            'timestamp': datetime.now().isoformat()
        }), 500



def generate_sustainability_speech(use_cache: bool = True) -> str | None:
    """
    Retorna arquivo de áudio sobre sustentabilidade (pré-gerado)
    """
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivo único de áudio pré-gerado com o script completo (~55 segundos)
    audio_file = audio_dir / 'sustainability_speech.wav'
    
    # Se arquivo existe, usar 
    if audio_file.exists():
        logger.info("✅ Usando áudio pré-gerado completo (55s)")
        return str(audio_file)
    
    # Se não, criar placeholder
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


# ============================================================================
# 🔐 AUTENTICAÇÃO - API DE LOGIN ADMIN
# ============================================================================
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            logger.info(f"✅ Login bem-sucedido para usuário: {username}")
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso!',
                'token': 'admin_token'  # Em produção, usar JWT
            }), 200
        else:
            logger.warning(f"❌ Tentativa de login falhada para: {username}")
            return jsonify({
                'success': False,
                'message': 'Usuário ou senha inválidos'
            }), 401
            
    except Exception as e:
        logger.error(f"❌ Erro na autenticação: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao processar autenticação'
        }), 500


@app.route('/api/admin/dashboard', methods=['GET'])
def api_admin_dashboard():
    """
    Retorna dados para o dashboard admin
    """
    try:
        from datetime import timedelta
        
        if db_connection:
            with db_connection as db:
                deposits = db.get_all_deposits()
                num_interactions = db.get_total_interacoes()

        total_tampinhas = num_interactions
        aceitas = len(deposits)
        rejeitadas = num_interactions - aceitas
        
        stats = {
            'total': total_tampinhas,
            'aceitas': aceitas,
            'rejeitadas': rejeitadas,
            'impacto': (sum(deposit['weight_value'] for deposit in deposits) / 1000.0) * 0.002,
            'changeTotal': 0,
            'changeTaxa': 0,
            'changeRejeitadas': 0,
            'today': 0,
            'week': 0,
            'month': 0,
            'year': 0
        }
        
        # Dados de tendência (últimos 7 dias)
        today = datetime.now()
        trend_labels = [(today - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
        trend_values = [random.randint(150, 300) for _ in range(7)]
        trend = {
            'labels': trend_labels,
            'values': trend_values
        }
        
        last_deposits = deposits[-10:]
        
        return jsonify({
            'success': True,
            'stats': stats,
            'trend': trend,
            'deposits': last_deposits
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados do dashboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("="*80)
    print("TOTEM IA - API FLASK")
    print("   Sistema de Deposito Inteligente de Tampinhas")
    print("="*80)
    print()

    image_classifier = ImageClassifier()
    image_classifier.load_classifier()
    
    print("Servidor iniciando em http://0.0.0.0:5003")
    print("   Acesse http://localhost:5003 no navegador")
    print()
    print("="*80)
    print()

    try:
        db_connection = DatabaseConnection()
        db_connection.init_db()
        app.run(host='0.0.0.0', port=5005, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuario.")
    except Exception as e:
        print(f"ERRO: {e}")
        traceback.print_exc()