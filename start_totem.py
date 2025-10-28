#!/usr/bin/env python3
"""
Script para iniciar o TOTEM IA
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("="*80)
    print("🏆 TOTEM IA - INICIALIZADOR")
    print("   Sistema Inteligente de Deposito de Tampinhas")
    print("="*80)
    print()

    # Verificar se o arquivo app.py existe
    if not os.path.exists('app.py'):
        print("❌ Erro: app.py não encontrado!")
        print("   Certifique-se de estar no diretório correto.")
        sys.exit(1)

    # Verificar dependências
    print("📦 Verificando dependências...")
    try:
        import flask
        import cv2
        import numpy
        import sklearn
        print("✅ Todas as dependências instaladas!")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print()
        print("Para instalar as dependências, execute:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    print()
    print("🚀 Iniciando servidor Flask...")
    print("="*80)
    print()
    print("✅ Servidor rodando em: http://localhost:5000")
    print("   Acesse no navegador do totem")
    print()
    print("💡 Pressione CTRL+C para parar o servidor")
    print()
    print("="*80)
    print()

    # Iniciar servidor Flask
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print()
        print()
        print("="*80)
        print("✅ Servidor encerrado")
        print("="*80)

if __name__ == '__main__':
    main()