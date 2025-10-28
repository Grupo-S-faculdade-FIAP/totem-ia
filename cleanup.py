#!/usr/bin/env python3
"""
Script para remover arquivos não utilizados no TOTEM IA
Mantém apenas: app.py, test_api.py, start_totem.py, src/, templates/, models/
"""

import os
import shutil
from pathlib import Path

# Arquivos e pastas UTILIZADOS (manter)
KEEP_FILES = {
    'app.py',
    'test_api.py',
    'start_totem.py',
    'requirements.txt',
    'README.md',
    'TOTEM_README.md',
    'RESUMO_FINAL.md',
    'FASE2_COMPLETA.md',
    'VISAO_GERAL.txt',
    '.git',
    '.gitignore',
    '.venv',
}

KEEP_DIRS = {
    'src',           # Classificador
    'templates',     # Interface web
    'models',        # Modelos treinados
    'datasets',      # Dados de treino
    'images',        # Imagens de teste
    'docs',          # Documentação
}

# Arquivos a REMOVER
REMOVE_FILES = {
    'organize_project.py',
    'main.py',
}

# Pastas a REMOVER
REMOVE_DIRS = {
    'backend',       # Versões antigas
    'esp32',         # Não utilizado
    'tampinhas',     # Dados duplicados
}

def cleanup():
    project_root = Path('.')
    
    print("=" * 80)
    print("LIMPANDO ARQUIVOS NÃO UTILIZADOS")
    print("=" * 80)
    
    # Remover arquivos
    print("\n1. REMOVENDO ARQUIVOS NÃO UTILIZADOS:")
    for file_name in REMOVE_FILES:
        file_path = project_root / file_name
        if file_path.exists():
            file_path.unlink()
            print(f"   ✓ Removido: {file_name}")
        else:
            print(f"   - Não encontrado: {file_name}")
    
    # Remover pastas
    print("\n2. REMOVENDO PASTAS NÃO UTILIZADAS:")
    for dir_name in REMOVE_DIRS:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   ✓ Removido: {dir_name}/")
        else:
            print(f"   - Não encontrado: {dir_name}/")
    
    # Mostrar estrutura final
    print("\n3. ESTRUTURA FINAL DO PROJETO:")
    print("\nARQUIVOS MANTIDOS:")
    for item in sorted(project_root.glob('*')):
        if item.is_file() and item.name not in {'.git', '.gitignore', '.venv'}:
            size_kb = item.stat().st_size / 1024
            print(f"   ├─ {item.name:30} ({size_kb:7.1f} KB)")
    
    print("\nPASTAS MANTIDAS:")
    for item in sorted(project_root.glob('*')):
        if item.is_dir() and item.name in KEEP_DIRS:
            file_count = len(list(item.rglob('*')))
            print(f"   ├─ {item.name}/ ({file_count} items)")
    
    print("\n" + "=" * 80)
    print("LIMPEZA CONCLUÍDA!")
    print("=" * 80)
    
    # Git commit
    print("\n4. FAZENDO GIT COMMIT:")
    os.system('git add -A')
    os.system('git commit -m "Limpeza: Remover códigos não utilizados (backend, esp32, arquivos antigos)"')
    print("   ✓ Commit realizado")
    
    print("\n✅ PROJETO ORGANIZADO E OTIMIZADO!")

if __name__ == '__main__':
    cleanup()
