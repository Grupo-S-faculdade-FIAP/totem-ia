"""
Script de Execução Completa do Totem
Inicia Backend + Simulador ESP32 de forma integrada
"""

import subprocess
import time
import sys
import os

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*70)
    print(f"🌱 {text}")
    print("="*70 + "\n")

def main():
    """Executa backend e simulador"""
    
    print_header("TOTEM DE RECICLAGEM INTELIGENTE - SIMULAÇÃO COMPLETA")
    
    # Verifica se estamos no diretório certo
    if not os.path.exists("backend/main.py"):
        print("❌ Erro: Execute este script na raiz do projeto")
        sys.exit(1)
    
    # Inicia backend em background
    print("🚀 Iniciando Backend FastAPI...\n")
    backend_process = subprocess.Popen(
        [sys.executable, "backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Aguarda backend iniciar
    print("⏳ Aguardando API ficar online...")
    time.sleep(3)
    
    # Verifica se backend está rodando
    try:
        import requests
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend online!")
            print("📝 Documentação: http://localhost:8080/docs\n")
        else:
            print("❌ Backend não respondeu corretamente")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao conectar ao backend: {e}")
        sys.exit(1)
    
    # Aguarda input do usuário
    print_header("PRONTO PARA SIMULAR")
    print("Simulador Clássico (sem análise de imagem):")
    print("  1. Simular 5 descartes")
    print("  2. Simular 10 descartes")
    print("  3. Simulação contínua\n")
    print("Simulador Avançado (com análise de visão computacional):")
    print("  4. Simular 5 descartes com análise real")
    print("  5. Simular 10 descartes com análise real")
    print("  6. Simulação contínua com análise real")
    print("  7. Simular 5 descartes (modo simples, sem OpenCV)")
    print("  0. Sair\n")
    
    choice = input("Escolha uma opção (0-7): ").strip()
    
    if choice == "0":
        print("\n❌ Encerrando...")
        backend_process.terminate()
        sys.exit(0)
    elif choice == "1":
        cmd = ["python", "esp32_simulator.py", "--count", "5", "--interval", "2"]
    elif choice == "2":
        cmd = ["python", "esp32_simulator.py", "--count", "10", "--interval", "1"]
    elif choice == "3":
        cmd = ["python", "esp32_simulator.py", "--continuous"]
    elif choice == "4":
        cmd = ["python", "esp32_simulator_advanced.py", "--count", "5", "--interval", "2"]
    elif choice == "5":
        cmd = ["python", "esp32_simulator_advanced.py", "--count", "10", "--interval", "1"]
    elif choice == "6":
        cmd = ["python", "esp32_simulator_advanced.py", "--continuous"]
    elif choice == "7":
        cmd = ["python", "esp32_simulator_advanced.py", "--count", "5", "--interval", "2", "--simple"]
    else:
        print("❌ Opção inválida")
        backend_process.terminate()
        sys.exit(1)
    
    # Executa simulador
    try:
        print_header("INICIANDO SIMULAÇÃO ESP32-S3")
        subprocess.run(cmd, check=True)
    
    except KeyboardInterrupt:
        print("\n\n⛔ Simulação interrompida")
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar simulador: {e}")
    
    finally:
        # Encerra backend
        print("\n🛑 Encerrando Backend...")
        backend_process.terminate()
        backend_process.wait(timeout=5)
        print("✅ Backend encerrado\n")

if __name__ == "__main__":
    main()
