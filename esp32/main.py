"""
Sistema Principal do Totem de Reciclagem Inteligente
ESP32-S3 com MicroPython

Fluxo:
1. Aguarda detecção de presença (PIR)
2. Captura imagem do resíduo
3. Pesa o material
4. Envia para API de classificação
5. Exibe resultado e pontuação
6. Retorna ao estado inicial
"""

import time
import network
import urequests as requests
import json
from machine import reset

# Importa módulos locais
import config
from camera_sim import get_camera
from sensors import PIRSensor, ScaleSensor
from display import get_display

class RecyclingTotem:
    """Classe principal do totem de reciclagem"""
    
    def __init__(self):
        print("\n" + "="*50)
        print("🌱 TOTEM DE RECICLAGEM INTELIGENTE")
        print("="*50 + "\n")
        
        # Inicializa WiFi
        self.wlan = None
        self.connect_wifi()
        
        # Inicializa componentes
        self.camera = get_camera()
        self.pir = PIRSensor(config.PIR_SENSOR_PIN)
        self.scale = ScaleSensor(config.SCALE_DATA_PIN, config.SCALE_CLOCK_PIN)
        self.display = get_display(config.DISPLAY_SDA_PIN, config.DISPLAY_SCL_PIN)
        
        # Estatísticas
        self.total_items = 0
        self.total_points = 0
        
        print("\n✅ Totem inicializado com sucesso!\n")
    
    def connect_wifi(self):
        """Conecta ao WiFi"""
        print("📡 Conectando ao WiFi...")
        
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        if not self.wlan.isconnected():
            self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            
            timeout = 10
            while not self.wlan.isconnected() and timeout > 0:
                print(f"   Aguardando conexão... ({timeout}s)")
                time.sleep(1)
                timeout -= 1
            
            if self.wlan.isconnected():
                print(f"✅ WiFi conectado!")
                print(f"   IP: {self.wlan.ifconfig()[0]}")
            else:
                print("❌ Falha ao conectar WiFi")
                print("   Continuando em modo offline...")
        else:
            print(f"✅ WiFi já conectado: {self.wlan.ifconfig()[0]}")
    
    def send_to_api(self, image_data, weight):
        """
        Envia imagem para API de classificação
        Retorna dicionário com resultado
        """
        try:
            print("\n📤 Enviando dados para API...")
            
            # Prepara payload
            if isinstance(image_data, dict):
                # Modo simulação
                payload = {
                    "user_id": config.USER_ID,
                    "weight": weight,
                    "simulation": True,
                    "material_hint": image_data.get("material_hint", "unknown")
                }
            else:
                # Modo real (seria multipart/form-data)
                payload = {
                    "user_id": config.USER_ID,
                    "weight": weight,
                    "simulation": False
                }
            
            # Envia requisição
            url = f"{config.API_URL}/classify"
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Resposta recebida da API")
                return result
            else:
                print(f"❌ Erro na API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao comunicar com API: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
    
    def process_waste(self):
        """Processa um resíduo detectado"""
        try:
            self.display.show_detecting()
            
            # 1. Captura imagem
            print("\n📸 Capturando imagem...")
            image_data = self.camera.capture_image()
            time.sleep(1)
            
            # 2. Pesa o material
            print("\n⚖️  Medindo peso...")
            weight = self.scale.read_weight()
            time.sleep(1)
            
            # 3. Envia para classificação
            result = self.send_to_api(image_data, weight)
            
            if result:
                # 4. Processa resultado
                material = result.get("material", "Desconhecido")
                bin_color = result.get("bin_color", "Cinza")
                points = result.get("points", 0)
                confidence = result.get("confidence", 0)
                
                print(f"\n✅ RESULTADO DA CLASSIFICAÇÃO:")
                print(f"   Material: {material}")
                print(f"   Lixeira: {bin_color}")
                print(f"   Confiança: {confidence:.1f}%")
                print(f"   Pontos: +{points}")
                print(f"   Peso: {weight:.1f}g")
                
                # 5. Mostra no display
                self.display.show_result(material, bin_color, points, weight)
                time.sleep(5)
                
                # 6. Atualiza estatísticas
                self.total_items += 1
                self.total_points += points
                
                # 7. Mostra QR code (simulado)
                self.display.show_qr_code()
                time.sleep(3)
                
                return True
            else:
                # Erro na classificação
                self.display.show_error("Erro na classificacao")
                time.sleep(3)
                return False
                
        except Exception as e:
            print(f"❌ Erro ao processar resíduo: {e}")
            self.display.show_error("Erro no sistema")
            time.sleep(3)
            return False
    
    def run(self):
        """Loop principal do totem"""
        print("\n🚀 Iniciando loop principal...\n")
        
        # Mostra tela de boas-vindas
        self.display.show_welcome()
        
        while True:
            try:
                # Aguarda detecção de presença
                print("⏳ Aguardando presença...")
                
                if self.pir.detect_motion():
                    print("\n" + "="*50)
                    print("🎯 NOVO DESCARTE DETECTADO")
                    print("="*50)
                    
                    # Processa o resíduo
                    success = self.process_waste()
                    
                    if success:
                        print("\n✅ Descarte processado com sucesso!")
                    else:
                        print("\n⚠️  Falha no processamento")
                    
                    # Mostra estatísticas
                    print(f"\n📊 Estatísticas do totem:")
                    print(f"   Total de itens: {self.total_items}")
                    print(f"   Total de pontos: {self.total_points}")
                    
                    # Pequeno delay antes de voltar
                    time.sleep(2)
                    
                    # Volta para tela de boas-vindas
                    self.display.show_welcome()
                
                # Pequeno delay para não sobrecarregar CPU
                time.sleep(config.CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Sistema interrompido pelo usuário")
                break
            
            except Exception as e:
                print(f"\n❌ Erro no loop principal: {e}")
                print("   Reiniciando em 5 segundos...")
                time.sleep(5)
                # Em produção, poderia fazer reset()
    
    def shutdown(self):
        """Desliga o totem de forma segura"""
        print("\n🛑 Desligando totem...")
        
        # Mostra estatísticas finais
        self.display.show_stats(self.total_items, self.total_points)
        time.sleep(3)
        
        self.display.clear()
        self.display.show_message("Sistema desligado", 1)
        
        # Desconecta WiFi
        if self.wlan and self.wlan.isconnected():
            self.wlan.disconnect()
        
        print("✅ Totem desligado com segurança")


# Função principal
def main():
    """Ponto de entrada do programa"""
    try:
        totem = RecyclingTotem()
        totem.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  Programa interrompido")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        print("   Reiniciando sistema em 10 segundos...")
        time.sleep(10)
        reset()  # Reinicia o ESP32
    finally:
        if 'totem' in locals():
            totem.shutdown()


# Executa o programa
if __name__ == "__main__":
    main()
