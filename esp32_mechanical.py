# esp32_mechanical.py - Código para ESP32 (upload via Thonny ou similar)
import network
import socket
import json
import time
from machine import Pin, ADC

# Configuração WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect('SEU_WIFI', 'SUA_SENHA')

while not wifi.isconnected():
    time.sleep(1)

print('ESP32 conectado:', wifi.ifconfig()[0])

# Simulação de sensores
presence_sensor = Pin(3, Pin.IN, Pin.PULL_DOWN)  # Sensor de presença (PIR)
weight_sensor = ADC(Pin(34))  # Sensor de peso (simulado com potenciômetro)

def check_mechanical():
    """Verifica presença e peso"""
    # Ler sensores
    presence = presence_sensor.value() == 1
    weight_raw = weight_sensor.read()  # 0-4095
    weight_ok = weight_raw > 1500  # Threshold para "peso adequado"
    
    result = {
        'presence': presence,
        'weight_ok': weight_ok,
        'weight_value': weight_raw,
        'timestamp': time.time()
    }
    
    print('Verificação mecânica:', result)
    return result

# Servidor HTTP simples
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Servidor ESP32 rodando na porta 80')
    
    while True:
        cl, addr = s.accept()
        print('Conexão de:', addr)
        
        request = cl.recv(1024).decode()
        
        if 'POST /check_mechanical' in request:
            # Receber sinal de validação
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            
            try:
                data = json.loads(body)
                if data.get('validation') == 'OK':
                    result = check_mechanical()
                    response = json.dumps(result)
                else:
                    response = json.dumps({'error': 'Validação pendente'})
            except:
                response = json.dumps({'error': 'JSON inválido'})
        else:
            response = json.dumps({'status': 'Endpoint não encontrado'})
        
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(response)
        cl.close()

start_server()
