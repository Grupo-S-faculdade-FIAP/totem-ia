# Configurações do ESP32-S3
# Edite com suas credenciais

# WiFi
WIFI_SSID = "Pepeto"
WIFI_PASSWORD = "Pepetocat"

# API Backend
API_URL = "http://localhost:8080"  # Para executar no PC local (porta 8080)
API_TIMEOUT = 10

# Hardware Pins (ajuste conforme seu hardware)
PIR_SENSOR_PIN = 13
SCALE_DATA_PIN = 4
SCALE_CLOCK_PIN = 5
DISPLAY_SDA_PIN = 21
DISPLAY_SCL_PIN = 22

# Configurações do Sistema
USER_ID = "user_totem_001"  # ID único do totem
CHECK_INTERVAL = 1  # Intervalo de checagem do PIR (segundos)
INACTIVITY_TIMEOUT = 30  # Timeout de inatividade (segundos)

# Simulação de Câmera
CAMERA_SIMULATION = True  # True = usa imagens simuladas
SIMULATION_IMAGES_PATH = "/images"  # Pasta com imagens de teste no ESP32
