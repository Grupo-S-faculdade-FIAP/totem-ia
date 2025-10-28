#!/usr/bin/env python3
"""
Script para iniciar a API e manter rodando
"""

import subprocess
import sys
import time

print("=" * 70)
print("🚀 Iniciando API do Totem de Reciclagem")
print("=" * 70)

while True:
    try:
        # Inicia o servidor
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "totem_api_simple:app", 
             "--host", "0.0.0.0", "--port", "8000"],
            check=False
        )
    except KeyboardInterrupt:
        print("\n✅ API finalizada")
        break
    except Exception as e:
        print(f"❌ Erro: {e}")
        time.sleep(2)

print("Até logo!")
