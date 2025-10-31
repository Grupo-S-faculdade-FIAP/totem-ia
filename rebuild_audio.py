#!/usr/bin/env python3
"""
Script rápido para REGENERAR áudio de sustentabilidade
Execute: python3 rebuild_audio.py
"""

import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

# Importar o script atualizado
from prompts.sustainability_prompts import SCRIPT_TEXTO

def rebuild():
    """Regenera áudio completo de forma rápida"""
    
    print("\n" + "=" * 70)
    print("🔄 RECONSTRUINDO ÁUDIO - SUSTENTABILIDADE")
    print("=" * 70)
    
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    temp_aiff = audio_dir / 'temp_rebuild.aiff'
    final_wav = audio_dir / 'sustainability_speech_final.wav'
    cache_wav = audio_dir / 'sustainability_speech.wav'
    
    print(f"📝 Texto: {len(SCRIPT_TEXTO)} caracteres")
    
    # 1. Gerar AIFF
    print(f"🎙️ Gerando áudio com pyttsx3...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 120)
        engine.setProperty('volume', 0.9)
        engine.save_to_file(SCRIPT_TEXTO, str(temp_aiff))
        engine.runAndWait()
        
        print(f"⏳ Aguardando (5s)...")
        time.sleep(5)
        
        if not temp_aiff.exists():
            print(f"❌ Erro: AIFF não gerado!")
            return False
        
        print(f"✅ AIFF: {temp_aiff.stat().st_size // 1024}KB")
    except Exception as e:
        print(f"❌ Erro pyttsx3: {e}")
        return False
    
    # 2. Converter com sox
    print(f"🔄 Convertendo AIFF → WAV...")
    try:
        result = subprocess.run([
            'sox', str(temp_aiff),
            '-r', '22050',
            str(final_wav)
        ], timeout=15, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Sox falhou: {result.stderr}")
            return False
        
        # Verificar duração
        duration_result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(final_wav)
        ], capture_output=True, text=True, timeout=5)
        
        duration = duration_result.stdout.strip() if duration_result.returncode == 0 else "?"
        size = final_wav.stat().st_size // 1024 if final_wav.exists() else 0
        
        print(f"✅ WAV: {size}KB, Duração: {duration}s")
    except Exception as e:
        print(f"❌ Erro conversão: {e}")
        return False
    
    # 3. Copiar para cache
    print(f"📋 Copiando para cache...")
    try:
        shutil.copy(str(final_wav), str(cache_wav))
        print(f"✅ Cache atualizado!")
    except Exception as e:
        print(f"❌ Erro ao copiar: {e}")
        return False
    
    # 4. Limpar temp
    if temp_aiff.exists():
        temp_aiff.unlink()
    
    print(f"\n✅ SUCESSO! Áudio regenerado em 25 segundos")
    print(f"   - Final: {final_wav}")
    print(f"   - Cache: {cache_wav}")
    print(f"\n🚀 Reinicie o servidor para carregar mudanças!\n")
    
    return True

if __name__ == "__main__":
    success = rebuild()
    sys.exit(0 if success else 1)
