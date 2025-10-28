#!/usr/bin/env python3
"""
API Flask Simplificada - Totem de Reciclagem
Versão sem complexidades
"""

from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename
import logging
import tempfile
import json
from pathlib import Path
from datetime import datetime
import os

from evaluate_eligibility import CapEligibilityEvaluator

# Setup
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Modelo global
evaluator = None
stats = {
    "total_classifications": 0,
    "last_classification": None
}

def load_model():
    """Carrega o modelo"""
    global evaluator
    if evaluator is None:
        logger.info("🔄 Carregando modelo...")
        try:
            evaluator = CapEligibilityEvaluator()
            logger.info("✅ Modelo pronto!")
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            raise
    return evaluator

@app.route('/', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "✅ Online",
        "service": "Totem de Reciclagem",
        "version": "1.0.0",
        "endpoints": [
            "GET /health",
            "GET /status",
            "POST /classify",
            "POST /batch",
            "POST /esp32/check"
        ]
    }), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Status do sistema"""
    try:
        load_model()
        return jsonify({
            "model_loaded": evaluator is not None,
            "total_classifications": stats["total_classifications"],
            "last_classification": stats["last_classification"]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/classify', methods=['POST'])
def classify():
    """Classifica uma imagem"""
    try:
        load_model()
        
        # Verifica arquivo
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Arquivo sem nome"}), 400
        
        # Salva arquivo temporário
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / f"totem_{datetime.now().timestamp()}_{filename}"
        file.save(str(filepath))
        
        # Classifica
        result = evaluator.classify_image(str(filepath))
        
        # Atualiza stats
        stats["total_classifications"] += 1
        stats["last_classification"] = datetime.now().isoformat()
        
        # Limpa
        filepath.unlink()
        
        logger.info(f"✅ {result['color']}: {result['confidence']:.1%}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/batch', methods=['POST'])
def batch_classify():
    """Classifica múltiplas imagens"""
    try:
        load_model()
        
        if 'files' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        files = request.files.getlist('files')
        results = []
        eligible_count = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            filepath = Path(app.config['UPLOAD_FOLDER']) / f"totem_{datetime.now().timestamp()}_{filename}"
            file.save(str(filepath))
            
            result = evaluator.classify_image(str(filepath))
            results.append(result)
            
            if result['eligible']:
                eligible_count += 1
            
            filepath.unlink()
        
        # Atualiza stats
        stats["total_classifications"] += len(results)
        stats["last_classification"] = datetime.now().isoformat()
        
        rate = (eligible_count / len(results) * 100) if results else 0
        
        logger.info(f"✅ Lote: {len(results)} imagens, {eligible_count} elegíveis ({rate:.1f}%)")
        
        return jsonify({
            "total": len(results),
            "eligible": eligible_count,
            "ineligible": len(results) - eligible_count,
            "rate": rate / 100,
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/esp32/check', methods=['POST'])
def esp32_check():
    """Endpoint otimizado para ESP32"""
    try:
        load_model()
        
        if 'file' not in request.files:
            return jsonify({"error": "Arquivo não enviado"}), 400
        
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / f"esp32_{datetime.now().timestamp()}_{filename}"
        file.save(str(filepath))
        
        result = evaluator.classify_image(str(filepath))
        
        response = {
            "accept": result['eligible'],
            "color": result['color'],
            "confidence": float(result['confidence']),
            "action": "ACCEPT" if result['eligible'] else "REJECT"
        }
        
        filepath.unlink()
        
        logger.info(f"🎯 ESP32: {response['action']} ({result['color']})")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ ESP32 Error: {e}")
        return jsonify({"error": str(e)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Iniciando API do Totem de Reciclagem")
    print(f"📍 http://localhost:5000")
    print(f"📚 Health: http://localhost:5000/")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
