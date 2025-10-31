#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/caroline/Desktop/FIAP/totem-ia/venv/lib/python3.9/site-packages')

import pyttsx3
import os
from pathlib import Path

print("=== Testando pyttsx3 ===")

script = "Olá, este é um teste de síntese de fala."
output_file = "/Users/caroline/Desktop/FIAP/totem-ia/static/audio/test_audio.aiff"

# Remover arquivo anterior
if os.path.exists(output_file):
    os.remove(output_file)

print(f"Inicializando engine...")
engine = pyttsx3.init()

print(f"Configurando propriedades...")
engine.setProperty('rate', 120)
engine.setProperty('volume', 0.9)

print(f"Salvando para {output_file}...")
engine.save_to_file(script, output_file)

print(f"Executando...")
engine.runAndWait()

print(f"Verificando arquivo...")
if os.path.exists(output_file):
    size = os.path.getsize(output_file)
    print(f"✅ Arquivo criado! Tamanho: {size} bytes")
    
    # Verificar tipo de arquivo
    os.system(f"file {output_file}")
    
    # Tentar converter com soundfile
    try:
        import soundfile as sf
        print(f"\nTentando ler com soundfile...")
        data, sr = sf.read(output_file)
        print(f"✅ Lido com sucesso! Shape: {data.shape}, Taxa: {sr} Hz")
    except Exception as e:
        print(f"❌ Erro: {e}")
else:
    print(f"❌ Arquivo NÃO foi criado!")
