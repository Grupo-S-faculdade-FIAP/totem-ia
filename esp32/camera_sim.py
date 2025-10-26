"""
Simulador de Câmera para ESP32-S3
Como não podemos usar a câmera real em todos os casos,
este módulo simula a captura criando imagens de teste
"""

import random
import time


class CameraSimulator:
    """Simula uma câmera que captura imagens de resíduos"""
    
    def __init__(self):
        self.image_counter = 0
        self.materials = ["plastic", "metal", "paper", "glass"]
        
    def capture_image(self):
        """
        Simula a captura de uma imagem
        Retorna bytes simulados de uma imagem
        """
        print("📸 Simulando captura de imagem...")
        time.sleep(0.5)  # Simula tempo de captura
        
        # Simula dados de imagem (na prática, seria JPEG real)
        material = random.choice(self.materials)
        self.image_counter += 1
        
        # Cria um payload simulado com metadados
        simulated_image = {
            "data": f"SIMULATED_IMAGE_{self.image_counter}",
            "material_hint": material,  # Dica para o backend (em produção não teria isso)
            "timestamp": time.time(),
            "format": "jpeg",
            "resolution": "640x480"
        }
        
        print(f"   Imagem capturada: #{self.image_counter}")
        print(f"   Material simulado: {material}")
        
        return simulated_image
    
    def get_image_bytes(self, simulated_image):
        """
        Converte a imagem simulada em bytes para envio
        Em produção real, seria o JPEG comprimido
        """
        import json
        return json.dumps(simulated_image).encode('utf-8')


# Para ESP32-S3 real com câmera OV2640/OV5640
class ESP32Camera:
    """
    Classe para controlar a câmera real do ESP32-S3
    Requer o módulo 'camera' do MicroPython ESP32
    """
    
    def __init__(self):
        try:
            import camera
            self.camera = camera
            self.init_camera()
            self.available = True
            print("✅ Câmera ESP32-S3 inicializada")
        except ImportError:
            self.available = False
            print("⚠️  Módulo camera não disponível, use CameraSimulator")
    
    def init_camera(self):
        """Inicializa a câmera com configurações otimizadas"""
        self.camera.init(0, format=self.camera.JPEG, fb_location=self.camera.PSRAM)
        self.camera.framesize(self.camera.FRAME_VGA)  # 640x480
        self.camera.quality(10)  # Qualidade JPEG (0-63, menor = melhor)
        
    def capture_image(self):
        """Captura uma imagem real da câmera"""
        if not self.available:
            raise RuntimeError("Câmera não disponível")
        
        print("📸 Capturando imagem da câmera ESP32...")
        buf = self.camera.capture()
        
        if buf:
            print(f"   Imagem capturada: {len(buf)} bytes")
            return buf
        else:
            raise RuntimeError("Falha ao capturar imagem")
    
    def deinit(self):
        """Desliga a câmera para economizar energia"""
        if self.available:
            self.camera.deinit()


def get_camera():
    """
    Factory function - retorna câmera simulada ou real
    baseado na disponibilidade do hardware
    """
    try:
        cam = ESP32Camera()
        if cam.available:
            return cam
    except:
        pass
    
    print("📱 Usando câmera simulada")
    return CameraSimulator()
