#!/usr/bin/env python3
"""
Script para gerar áudio de sustentabilidade com pyttsx3
"""

import pyttsx3
import os
from pathlib import Path
from prompts.sustainability_prompts import SCRIPT_TEXTO

print("🎵 Gerando áudio de sustentabilidade...")
print(f"📝 Texto ({len(SCRIPT_TEXTO)} chars): {SCRIPT_TEXTO[:100]}...")

# Criar pasta
audio_dir = Path('static/audio')
audio_dir.mkdir(parents=True, exist_ok=True)

audio_file = audio_dir / 'sustainability_speech.wav'

# Gerar com pyttsx3
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 120)  # Velocidade natural
    engine.setProperty('volume', 0.9)
    
    print(f"\n🔊 Configurações:")
    print(f"   Rate: 120 palavras/min")
    print(f"   Volume: 0.9")
    print(f"   Arquivo: {audio_file}")
    
    print(f"\n⏳ Gerando áudio (pode levar alguns segundos)...")
    engine.save_to_file(SCRIPT_TEXTO, str(audio_file))
    engine.runAndWait()
    
    print(f"\n✅ Arquivo gerado!")
    
    if audio_file.exists():
        size = audio_file.stat().st_size
        print(f"✅ Arquivo existe: {audio_file}")
        print(f"   Tamanho: {size} bytes ({size/1024:.1f}KB)")
        
        # Verificar se é um arquivo WAV válido
        with open(audio_file, 'rb') as f:
            header = f.read(4)
            if header == b'RIFF':
                print(f"✅ Arquivo WAV válido (começa com RIFF)")
            else:
                print(f"⚠️ Arquivo pode não ser WAV válido (header: {header})")
    else:
        print(f"❌ Arquivo NÃO foi criado!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
