#!/usr/bin/env python3
"""
Menu Principal - Classificação de Tampinhas
Escolha qual modelo usar: SVM, ResNet ou Ensemble
"""

import sys
from pathlib import Path

def show_menu():
    print("\n" + "=" * 70)
    print("🎯 CLASSIFICADOR DE TAMPINHAS - MENU PRINCIPAL")
    print("=" * 70)
    print("\n1. 🟢 SVM com RBF Kernel")
    print("   Rápido, sem GPU, 100% de acurácia em treino")
    print("   ⚠️  Mas: Baixa generalização em imagem6")
    print("\n2. 🔵 ResNet50 Transfer Learning")
    print("   Melhor generalização, mais lento, requer TensorFlow")
    print("   ✅ Esperado: Melhor resultado em imagem6")
    print("\n3. 🟣 Ensemble (SVM + ResNet)")
    print("   Combina força de ambos os modelos")
    print("   ✅ Esperado: Melhor resultado final")
    print("\n4. 📊 Treinar TODOS os modelos")
    print("   Treina SVM, ResNet e prepara Ensemble")
    print("\n5. ℹ️  Ver resumo de modelos")
    print("\n6. 🔄 Comparar resultados")
    print("\n0. ❌ Sair")
    print("\n" + "=" * 70)

def train_svm():
    print("\n🟢 Treinando SVM com RBF Kernel...\n")
    import subprocess
    subprocess.run([sys.executable, "svm_classifier.py"])

def train_resnet():
    print("\n🔵 Treinando ResNet50 Transfer Learning...\n")
    import subprocess
    subprocess.run([sys.executable, "resnet_classifier.py"])

def classify_svm():
    print("\n🟢 Classificando com SVM...\n")
    import subprocess
    subprocess.run([sys.executable, "classify_svm.py"])

def classify_resnet():
    print("\n🔵 Classificando com ResNet...\n")
    import subprocess
    subprocess.run([sys.executable, "classify_resnet.py"])

def classify_ensemble():
    print("\n🟣 Classificando com Ensemble...\n")
    import subprocess
    subprocess.run([sys.executable, "ensemble_classifier.py"])

def show_summary():
    print("\n" + "=" * 70)
    print("📋 RESUMO DE MODELOS")
    print("=" * 70)
    try:
        with open("RESUMO_MODELOS.md", "r") as f:
            print(f.read())
    except:
        print("Arquivo RESUMO_MODELOS.md não encontrado")

def train_all():
    print("\n" + "=" * 70)
    print("📦 TREINANDO TODOS OS MODELOS")
    print("=" * 70)
    
    train_svm()
    
    print("\n" + "=" * 70)
    print("🔄 Agora treinando ResNet (pode demorar ~3-5 minutos)...")
    print("=" * 70)
    train_resnet()

def compare_results():
    print("\n" + "=" * 70)
    print("🔄 COMPARANDO RESULTADOS DOS MODELOS")
    print("=" * 70)
    
    print("\n🟢 CLASSIFICAÇÃO COM SVM:")
    print("-" * 70)
    import subprocess
    subprocess.run([sys.executable, "classify_svm.py"])
    
    print("\n🔵 CLASSIFICAÇÃO COM RESNET (se disponível):")
    print("-" * 70)
    import subprocess
    try:
        subprocess.run([sys.executable, "classify_resnet.py"], timeout=60)
    except:
        print("❌ ResNet não disponível ou não treinado")
    
    print("\n🟣 CLASSIFICAÇÃO COM ENSEMBLE (se ambos disponíveis):")
    print("-" * 70)
    try:
        subprocess.run([sys.executable, "ensemble_classifier.py"], timeout=60)
    except:
        print("❌ Ensemble não disponível (ambos os modelos precisam estar treinados)")

def main():
    while True:
        show_menu()
        choice = input("\n👉 Escolha uma opção: ").strip()
        
        if choice == "1":
            train_svm()
            print("\n✅ Treinamento completo! Agora classificando...")
            classify_svm()
            
        elif choice == "2":
            train_resnet()
            print("\n✅ Treinamento completo! Agora classificando...")
            classify_resnet()
            
        elif choice == "3":
            print("\n⚠️  ResNet e SVM precisam estar treinados!")
            print("\nTreine os modelos primeiro (opções 1 e 2)")
            classify_ensemble()
            
        elif choice == "4":
            train_all()
            
        elif choice == "5":
            show_summary()
            
        elif choice == "6":
            compare_results()
            
        elif choice == "0":
            print("\n👋 Até logo!\n")
            break
            
        else:
            print("\n❌ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
