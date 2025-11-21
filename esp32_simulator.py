#!/usr/bin/env python3
"""
SIMULADOR ESP32 - Servidor HTTP para testar validação mecânica
Simula um ESP32 respondendo com dados de sensores
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime

app_esp32 = Flask(__name__)

# Dados simulados do sensor
sensor_state = {
    'presence_detected': True,
    'weight_ok': True,
    'requests_count': 0
}

@app_esp32.route('/check_mechanical', methods=['POST'])
def check_mechanical():
    """
    Endpoint que simula a resposta do ESP32
    Recebe: {"validation": "OK"}
    Retorna: {"presence_detected": bool, "weight_ok": bool, "timestamp": int}
    """
    try:
        data = request.get_json()
        sensor_state['requests_count'] += 1
        
        # Log
        print(f"[ESP32 Simulator] Requisição #{sensor_state['requests_count']}")
        print(f"  Dados recebidos: {json.dumps(data)}")
        
        # Responder com dados de sensores
        response = {
            'presence_detected': sensor_state['presence_detected'],
            'weight_ok': sensor_state['weight_ok'],
            'timestamp': int(time.time()),
            'sensor_data': {
                'pir_gpio3': sensor_state['presence_detected'],
                'adc_gpio34': 500 if sensor_state['weight_ok'] else 100
            }
        }
        
        print(f"  Respondendo: {json.dumps(response)}")
        print()
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[ESP32 Simulator] ❌ Erro: {e}")
        return jsonify({'error': str(e)}), 400

@app_esp32.route('/status', methods=['GET'])
def status():
    """Status do simulador"""
    return jsonify({
        'status': 'online',
        'presence_detected': sensor_state['presence_detected'],
        'weight_ok': sensor_state['weight_ok'],
        'requests_count': sensor_state['requests_count'],
        'timestamp': datetime.now().isoformat()
    }), 200

@app_esp32.route('/set_sensors', methods=['POST'])
def set_sensors():
    """Alterar estado dos sensores para teste"""
    data = request.get_json()
    
    if 'presence_detected' in data:
        sensor_state['presence_detected'] = bool(data['presence_detected'])
    if 'weight_ok' in data:
        sensor_state['weight_ok'] = bool(data['weight_ok'])
    
    print(f"[ESP32 Simulator] Sensores atualizados:")
    print(f"  Presença: {sensor_state['presence_detected']}")
    print(f"  Peso OK: {sensor_state['weight_ok']}")
    
    return jsonify({'status': 'updated', 'sensor_state': sensor_state}), 200

if __name__ == '__main__':
    print("=" * 70)
    print("🤖 SIMULADOR ESP32")
    print("=" * 70)
    print("\nEndpoints disponíveis:")
    print("  POST /check_mechanical       - Simula verificação de sensores")
    print("  GET  /status                 - Status do simulador")
    print("  POST /set_sensors            - Alterar estado dos sensores")
    print("\nAguardando requisições em: http://localhost:5005")
    print("=" * 70 + "\n")
    
    app_esp32.run(host='0.0.0.0', port=5005, debug=False, use_reloader=False)
