#!/usr/bin/env python
"""
🎯 QUICK START: Benchmarking ViT vs Random Forest
Script para executar os 3 passos automaticamente
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_header(text):
    """Imprime header formatado."""
    print("\n" + "=" * 80)
    print(f"🎯 {text}")
    print("=" * 80 + "\n")

def print_step(number, text, emoji=""):
    """Imprime step formatado."""
    print(f"\n{emoji} [{number}/3] {text}")
    print("-" * 80)

def check_dependencies():
    """Verifica se todas as dependências estão instaladas."""
    print_header("VERIFICANDO DEPENDÊNCIAS")
    
    dependencies = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("sklearn", "Scikit-learn"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("tqdm", "tqdm"),
        ("numpy", "NumPy")
    ]
    
    missing = []
    for package, name in dependencies:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} NÃO INSTALADO")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Pacotes faltando: {', '.join(missing)}")
        print(f"Execute: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ Todas as dependências instaladas!")
    return True

def check_dataset():
    """Verifica se o dataset existe."""
    print_header("VERIFICANDO DATASET")
    
    paths = [
        "datasets/color-cap/train/images",
        "datasets/color-cap/valid/images",
        "datasets/color-cap/test/images"
    ]
    
    all_exist = True
    for path in paths:
        if os.path.exists(path):
            files = list(Path(path).glob("*.jpg")) + \
                   list(Path(path).glob("*.jpeg")) + \
                   list(Path(path).glob("*.png"))
            print(f"✓ {path}: {len(files)} imagens")
        else:
            print(f"✗ {path}: NÃO ENCONTRADO")
            all_exist = False
    
    if not all_exist:
        print(f"\n❌ Dataset incompleto!")
        return False
    
    print("\n✅ Dataset OK!")
    return True

def run_training(script_name: str, description: str, emoji: str):
    """Executa script de treinamento."""
    print_step(script_name.split("_")[1].upper() == "ML" and 1 or 2, description, emoji)
    
    try:
        print(f"Executando: python {script_name}")
        start = time.time()
        
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=".",
            capture_output=False
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"\n✅ {description} concluído em {elapsed:.2f}s")
            return True
        else:
            print(f"\n❌ {description} falhou (código: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao executar {script_name}: {e}")
        return False

def run_comparison():
    """Executa comparação de modelos."""
    print_step(3, "COMPARANDO MODELOS", "📊")
    
    try:
        result = subprocess.run(
            [sys.executable, "compare_models.py"],
            cwd="."
        )
        
        if result.returncode == 0:
            print(f"\n✅ Comparação concluída!")
            
            # Tenta ler relatório
            if os.path.exists("COMPARISON_REPORT.txt"):
                print("\n" + "=" * 80)
                with open("COMPARISON_REPORT.txt", 'r') as f:
                    print(f.read())
            
            return True
        else:
            print(f"\n❌ Comparação falhou")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao executar comparação: {e}")
        return False

def main():
    """Main function."""
    print_header("🏆 BENCHMARKING: ViT vs Random Forest para Tampinhas Plásticas")
    
    # Verificações iniciais
    if not check_dependencies():
        print("\n❌ Instale as dependências e tente novamente.")
        sys.exit(1)
    
    if not check_dataset():
        print("\n❌ Dataset não encontrado. Verifique a estrutura de pastas.")
        sys.exit(1)
    
    # Confirmação
    print_header("CONFIRMAÇÃO")
    print("Este script vai executar:")
    print("  1. Treinar Random Forest (~30s)")
    print("  2. Fine-tunar ViT (~45-60min)")
    print("  3. Comparar resultados")
    print("\nVocê deseja continuar? (s/n)")
    
    response = input("> ").lower().strip()
    if response not in ['s', 'y', 'sim', 'yes']:
        print("❌ Execução cancelada.")
        sys.exit(0)
    
    # Executar treinamentos
    print_header("INICIANDO TREINAMENTOS")
    
    # Step 1: Random Forest (rápido)
    if not run_training("train_ml.py", "Treinamento Random Forest", "⚡"):
        print("\n⚠️  Random Forest falhou, mas continuando com ViT...")
    
    time.sleep(2)
    
    # Step 2: ViT (lento)
    if not run_training("train_vit.py", "Fine-tuning ViT", "🤖"):
        print("\n⚠️  ViT falhou, mas tentando comparação...")
    
    time.sleep(2)
    
    # Step 3: Comparação
    run_comparison()
    
    print_header("CONCLUÍDO!")
    print("✅ Pipeline de benchmarking concluído!")
    print("\nPróximos passos:")
    print("  1. Verifique COMPARISON_REPORT.txt para os resultados")
    print("  2. Escolha qual modelo usar em produção")
    print("  3. Considere ensemble dos dois modelos para melhor desempenho")

if __name__ == "__main__":
    main()
