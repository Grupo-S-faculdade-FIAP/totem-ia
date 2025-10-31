#!/usr/bin/env python3
"""
Script ULTRA-RÁPIDO para regenerar áudio (< 5 segundos!)
Usa 'say' nativo do macOS (muito mais rápido que pyttsx3)
Execute: python3 fast_audio.py
"""

import subprocess
import sys
from pathlib import Path
from prompts.sustainability_prompts import SCRIPT_TEXTO

def fast_rebuild():
    """Regenera áudio em menos de 5 segundos"""
    
    print("\n" + "=" * 70)
    print("⚡ ÁUDIO ULTRA-RÁPIDO - SUSTENTABILIDADE")
    print("=" * 70)
    
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    temp_aiff = audio_dir / 'temp_say.aiff'
    final_wav = audio_dir / 'sustainability_speech_final.wav'
    cache_wav = audio_dir / 'sustainability_speech.wav'
    
    print(f"📝 Texto: {len(SCRIPT_TEXTO)} caracteres")
    print(f"🎙️ Gerando com 'say' nativo do macOS...")
    
    try:
        # Usar 'say' do macOS para AIFF (suportado)
        result = subprocess.run([
            'say',
            '-o', str(temp_aiff),
            '-r', '120',  # velocidade NATURAL (palavras/minuto) - 120 é padrão
            SCRIPT_TEXTO
        ], timeout=10, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Erro say: {result.stderr}")
            return False
        
        print(f"✅ AIFF gerado")
        
        # Converter AIFF → WAV com sox
        print(f"🔄 Convertendo AIFF → WAV...")
        sox_result = subprocess.run([
            'sox', str(temp_aiff),
            '-r', '22050',
            str(final_wav)
        ], timeout=10, capture_output=True, text=True)
        
        if sox_result.returncode != 0:
            print(f"❌ Erro sox: {sox_result.stderr}")
            return False
        
        # Copiar para cache
        import shutil
        shutil.copy(str(final_wav), str(cache_wav))
        
        # Verificar duração
        duration_result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(cache_wav)
        ], capture_output=True, text=True, timeout=5)
        
        duration = duration_result.stdout.strip() if duration_result.returncode == 0 else "?"
        size = cache_wav.stat().st_size // 1024
        
        print(f"✅ PRONTO! {size}KB, {duration}s")
        
        # Limpar temp
        if temp_aiff.exists():
            temp_aiff.unlink()
        
        print(f"\n🚀 Reinicie servidor:\n   pkill python; sleep 1; python3 app.py &\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fast_rebuild()
    sys.exit(0 if success else 1)
