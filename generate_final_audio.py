#!/usr/bin/env python3
"""
Script para gerar áudio de sustentabilidade UMA VEZ e salvar de forma permanente
"""

import pyttsx3
import subprocess
import os
from pathlib import Path
from prompts.sustainability_prompts import SCRIPT_TEXTO

def generate_sustainability_audio():
    """Gera áudio completo e o converte para WAV de qualidade"""
    
    # Caminhos
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    temp_aiff = audio_dir / 'temp_sustainability.aiff'
    final_wav = audio_dir / 'sustainability_speech_final.wav'
    
    print(f"📝 Script: {len(SCRIPT_TEXTO)} caracteres")
    print(f"🎙️ Gerando áudio com pyttsx3...")
    
    # Gerar com pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 120)
    engine.setProperty('volume', 0.9)
    
    engine.save_to_file(SCRIPT_TEXTO, str(temp_aiff))
    engine.runAndWait()
    
    import time
    print("⏳ Aguardando conclusão (10s)...")
    time.sleep(10)
    
    if not temp_aiff.exists():
        print(f"❌ Erro: Arquivo AIFF não foi criado!")
        return False
    
    size_aiff = temp_aiff.stat().st_size
    print(f"✅ AIFF criado: {size_aiff} bytes")
    
    # Converter com sox
    print(f"🔄 Convertendo AIFF → WAV com sox...")
    try:
        result = subprocess.run([
            'sox', str(temp_aiff),
            '-r', '22050',
            str(final_wav)
        ], timeout=10, capture_output=True, text=True)
        
        if result.returncode == 0 and final_wav.exists():
            size_wav = final_wav.stat().st_size
            
            # Verificar duração
            duration_result = subprocess.run([
                'ffprobe', '-v', 'error', 
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(final_wav)
            ], capture_output=True, text=True, timeout=5)
            
            duration = duration_result.stdout.strip() if duration_result.returncode == 0 else "?"
            
            print(f"✅ WAV criado: {size_wav} bytes, Duração: {duration}s")
            print(f"📍 Salvo em: {final_wav}")
            
            # Limpar temp
            if temp_aiff.exists():
                temp_aiff.unlink()
            
            return True
        else:
            print(f"❌ Sox falhou: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("GERADOR DE ÁUDIO - SUSTENTABILIDADE")
    print("=" * 70)
    
    success = generate_sustainability_audio()
    
    if success:
        print("\n✅ Áudio gerado com sucesso!")
    else:
        print("\n❌ Falha ao gerar áudio")
