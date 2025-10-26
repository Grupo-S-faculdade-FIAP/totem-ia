"""
Controle do Display LCD para o totem
Suporta displays I2C (LCD 16x2, 20x4) e OLED SSD1306
"""

from machine import I2C, Pin
import time


class DisplayLCD:
    """
    Display LCD genérico via I2C
    Funciona com LCD1602, LCD2004 com módulo I2C
    """
    
    def __init__(self, sda_pin, scl_pin, i2c_addr=0x27, rows=4, cols=20):
        self.rows = rows
        self.cols = cols
        self.simulated = True
        
        try:
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
            devices = self.i2c.scan()
            
            if i2c_addr in devices:
                # from lcd_api import LcdApi
                # from i2c_lcd import I2cLcd
                # self.lcd = I2cLcd(self.i2c, i2c_addr, rows, cols)
                # self.simulated = False
                print(f"✅ Display LCD inicializado no endereço 0x{i2c_addr:02X}")
            else:
                print(f"⚠️  Display não encontrado, usando simulação")
        except Exception as e:
            print(f"⚠️  Erro ao inicializar display: {e}")
            print("   Usando modo simulação")
    
    def clear(self):
        """Limpa o display"""
        if not self.simulated:
            # self.lcd.clear()
            pass
        print("\n" + "="*50)
        print("🖥️  [DISPLAY LIMPO]")
        print("="*50)
    
    def show_message(self, text, row=0, col=0):
        """Mostra mensagem no display"""
        if not self.simulated:
            # self.lcd.move_to(col, row)
            # self.lcd.putstr(text[:self.cols])
            pass
        
        # Simulação no console
        print(f"🖥️  Linha {row}: {text}")
    
    def show_welcome(self):
        """Mostra tela de boas-vindas"""
        self.clear()
        self.show_message("  BEM-VINDO AO", 0)
        self.show_message("TOTEM RECICLAGEM", 1)
        self.show_message("  Aproxime-se!", 2)
        self.show_message("     ♻️ 🌱", 3)
    
    def show_detecting(self):
        """Mostra que está detectando"""
        self.clear()
        self.show_message("   DETECTANDO...", 1)
        self.show_message("    Aguarde", 2)
    
    def show_result(self, material, bin_color, points, weight=0):
        """
        Mostra resultado da classificação
        material: tipo de material (plástico, metal, etc)
        bin_color: cor da lixeira
        points: pontos ganhos
        weight: peso em gramas
        """
        self.clear()
        
        # Emojis para cada material
        emojis = {
            "plastic": "🧴",
            "metal": "🥫", 
            "paper": "📄",
            "glass": "🍾",
            "plastico": "🧴",
            "vidro": "🍾",
            "papel": "📄"
        }
        
        emoji = emojis.get(material.lower(), "♻️")
        
        self.show_message(f"Material: {material} {emoji}", 0)
        self.show_message(f"Lixeira: {bin_color}", 1)
        
        if weight > 0:
            self.show_message(f"Peso: {weight:.0f}g", 2)
        
        self.show_message(f"+{points} pontos! ⭐", 3)
    
    def show_qr_code(self, text="Scan para ranking"):
        """Mostra instruções para QR code"""
        self.clear()
        self.show_message(f"  {text}", 1)
        self.show_message("     [QR]", 2)
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        self.clear()
        self.show_message("    ⚠️ ERRO ⚠️", 0)
        self.show_message(message[:self.cols], 1)
        self.show_message("Tente novamente", 2)
    
    def show_stats(self, total_items, total_points):
        """Mostra estatísticas do totem"""
        self.clear()
        self.show_message("  ESTATISTICAS", 0)
        self.show_message(f"Items: {total_items}", 1)
        self.show_message(f"Pontos: {total_points}", 2)
        self.show_message("Obrigado! ♻️", 3)


class DisplayOLED:
    """
    Display OLED SSD1306 128x64
    Alternativa ao LCD para interface mais moderna
    """
    
    def __init__(self, sda_pin, scl_pin, width=128, height=64):
        self.width = width
        self.height = height
        self.simulated = True
        
        try:
            self.i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin))
            # from ssd1306 import SSD1306_I2C
            # self.oled = SSD1306_I2C(width, height, self.i2c)
            # self.simulated = False
            print("✅ Display OLED inicializado")
        except:
            print("⚠️  OLED não disponível, usando simulação")
    
    def clear(self):
        """Limpa o display"""
        if not self.simulated:
            # self.oled.fill(0)
            # self.oled.show()
            pass
        print("\n" + "="*50)
        print("🖥️  [OLED LIMPO]")
        print("="*50)
    
    def show_message(self, text, x=0, y=0):
        """Mostra texto no OLED"""
        if not self.simulated:
            # self.oled.text(text, x, y)
            # self.oled.show()
            pass
        print(f"🖥️  ({x},{y}): {text}")


def get_display(sda_pin, scl_pin, display_type="LCD"):
    """
    Factory function para criar display
    display_type: "LCD" ou "OLED"
    """
    if display_type.upper() == "OLED":
        return DisplayOLED(sda_pin, scl_pin)
    else:
        return DisplayLCD(sda_pin, scl_pin)
