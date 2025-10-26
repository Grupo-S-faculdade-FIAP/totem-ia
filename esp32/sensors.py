"""
Módulo de controle de sensores do totem
- Sensor PIR para detecção de presença
- Balança digital (HX711) para pesagem
"""

from machine import Pin
import time
import random


class PIRSensor:
    """Sensor PIR para detectar movimento/presença"""
    
    def __init__(self, pin_number):
        self.pir = Pin(pin_number, Pin.IN)
        self.last_detection = 0
        self.debounce_time = 2  # segundos
        print(f"✅ Sensor PIR inicializado no pino {pin_number}")
    
    def detect_motion(self):
        """
        Verifica se há movimento detectado
        Retorna True se detectar presença
        """
        current_time = time.time()
        
        # Debounce para evitar múltiplas detecções
        if current_time - self.last_detection < self.debounce_time:
            return False
        
        if self.pir.value() == 1:
            self.last_detection = current_time
            print("👤 Presença detectada!")
            return True
        
        return False
    
    def wait_for_motion(self, timeout=60):
        """
        Aguarda detecção de movimento com timeout
        Retorna True se detectou, False se timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.detect_motion():
                return True
            time.sleep(0.1)
        
        return False


class ScaleSensor:
    """
    Balança digital usando sensor HX711
    Simula leitura de peso quando hardware não disponível
    """
    
    def __init__(self, data_pin, clock_pin, calibration_factor=1.0):
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.calibration_factor = calibration_factor
        self.simulated = True
        
        try:
            # Tenta inicializar HX711 real
            # from hx711 import HX711
            # self.scale = HX711(data_pin, clock_pin)
            # self.simulated = False
            # print(f"✅ Balança HX711 inicializada (pinos {data_pin}, {clock_pin})")
            raise ImportError  # Força simulação por enquanto
        except ImportError:
            print("⚠️  HX711 não disponível, usando simulação de peso")
    
    def read_weight(self):
        """
        Lê o peso do objeto na balança
        Retorna peso em gramas
        """
        if self.simulated:
            # Simula peso aleatório entre 10g e 500g
            weight = random.uniform(10, 500)
            print(f"⚖️  Peso simulado: {weight:.1f}g")
            return weight
        else:
            # Leitura real do HX711
            # raw = self.scale.read()
            # weight = raw * self.calibration_factor
            # print(f"⚖️  Peso medido: {weight:.1f}g")
            # return weight
            pass
    
    def tare(self):
        """Zera a balança (tara)"""
        if not self.simulated:
            # self.scale.tare()
            pass
        print("⚖️  Balança zerada")
    
    def calibrate(self, known_weight):
        """
        Calibra a balança com um peso conhecido
        known_weight: peso em gramas
        """
        if not self.simulated:
            # raw = self.scale.read()
            # self.calibration_factor = known_weight / raw
            pass
        print(f"⚖️  Balança calibrada com {known_weight}g")


class ButtonSensor:
    """Botão para interação manual (opcional)"""
    
    def __init__(self, pin_number):
        self.button = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.last_press = 0
        self.debounce_time = 0.3
        print(f"✅ Botão inicializado no pino {pin_number}")
    
    def is_pressed(self):
        """Verifica se o botão foi pressionado"""
        current_time = time.time()
        
        if current_time - self.last_press < self.debounce_time:
            return False
        
        if self.button.value() == 0:  # Pull-up: 0 = pressionado
            self.last_press = current_time
            print("🔘 Botão pressionado")
            return True
        
        return False
