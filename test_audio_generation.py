#!/usr/bin/env python3
"""Script de teste isolado para pyttsx3 + soundfile"""

import sys
import os
sys.path.insert(0, '/Users/caroline/Desktop/FIAP/totem-ia/venv/lib/python3.9/site-packages')

import pyttsx3
import soundfile as sf
import time

OUTPUT_DIR = '/Users/caroline/Desktop/FIAP/totem-ia/static/audio/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Limpar arquivos anteriores
for f in os.listdir(OUTPUT_DIR):
    try:
        os.remove(os.path.join(OUTPUT_DIR, f))
    except:
        pass

script = "Olá! Este é um teste de síntese de fala. Reciclagem é muito importante para o futuro do nosso planeta."

print("\n=== TESTE PYTTSX3 + SOUNDFILE ===\n")

# 1. Criar AIFF
temp_aiff = os.path.join(OUTPUT_DIR, 'temp.aiff')
print(f"1️⃣ Criando AIFF em {temp_aiff}...")

engine = pyttsx3.init()
engine.setProperty('rate', 120)
engine.setProperty('volume', 0.9)
engine.save_to_file(script, temp_aiff)
print(f"   → runAndWait()...")
engine.runAndWait()

print(f"   → Aguardando 2 segundos...")
time.sleep(2)

if os.path.exists(temp_aiff):
    size = os.path.getsize(temp_aiff)
    print(f"   ✅ AIFF criado! Tamanho: {size} bytes")
    
    if size < 2000:
        print(f"   ⚠️ AIFF muito pequeno! Pode estar vazio.")
else:
    print(f"   ❌ AIFF não criado!")
    sys.exit(1)

# 2. Converter AIFF para WAV
output_wav = os.path.join(OUTPUT_DIR, 'sustainability_speech.wav')
print(f"\n2️⃣ Convertendo para WAV...")

try:
    print(f"   → Lendo AIFF...")
    data, sr = sf.read(temp_aiff)
    print(f"   ✅ Lido! Shape: {data.shape}, Taxa: {sr} Hz")
    
    if len(data) == 0:
        print(f"   ⚠️ AIFF vazio! Nenhum áudio foi sintetizado.")
        sys.exit(1)
    
    print(f"   → Escrevendo WAV em {output_wav}...")
    sf.write(output_wav, data, sr, subtype='PCM_16')
    
    if os.path.exists(output_wav):
        size = os.path.getsize(output_wav)
        print(f"   ✅ WAV criado! Tamanho: {size} bytes")
        
        # Verificar formato
        os.system(f"file {output_wav}")
        
        # Limpar temp
        os.remove(temp_aiff)
        print(f"\n✅ SUCESSO! Arquivo pronto em {output_wav}")
    else:
        print(f"   ❌ WAV não foi criado!")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
