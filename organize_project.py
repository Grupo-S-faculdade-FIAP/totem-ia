#!/usr/bin/env python3
"""
Script de Organização e Limpeza do Projeto
==========================================

Reorganiza os arquivos do projeto em uma estrutura clara e remove duplicatas
"""

import os
import shutil
from pathlib import Path

# Mapeamento de arquivos para suas pastas corretas
REORGANIZATION_MAP = {
    # ===== TRAINERS (Treinamento de Modelos) =====
    'models_trainers': [
        'models/svm/svm_colorCap_classifier.py',
        'models/svm/svm_complete_classifier.py',
        'resnet_classifier.py',
    ],
    
    # ===== CLASSIFIERS (Classificação) =====
    'models_classifiers': [
        'classify_svm_colorCap.py',
        'classify_hybrid.py',
        'classify_hybrid_v2.py',
    ],
    
    # ===== ANALYSIS (Análise e Exploração) =====
    'analysis': [
        'analyze_svm_results.py',
        'analyze_imagem6.py',
        'analyze_features_comparison.py',
        'compare_models.py',
    ],
    
    # ===== DEPRECATED (Arquivos Antigos/Inúteis) =====
    'deprecated': [
        'evaluate_eligibility_fast.py',
        'classify_all_images.py',
        'classify_resnet.py',
        'classify_svm.py',
        'ensemble_classifier.py',
        'advanced_cap_classifier.py',
        'compare_models.py',
        'svm_classifier.py',
        'resnet_classifier.py',
        'main.py',
        'app_flask.py',
        'run_api.py',
        'resumo_final.py',
    ],
}

# Mapeamento de documentação
DOCS_MAP = {
    'current': [
        'SUMARIO_DATASET_COMPLETO.md',
        'RELATORIO_FINAL_SVM_IMAGEM6.md',
    ],
    
    'deprecated': [
        'ANALISE_FINAL_SVM_COLORCAP.md',
        'FINALIZACAO.md',
        'CHECKLIST.md',
        'GUIA_USO.md',
        'INDICE.md',
        'MODELOS.md',
        'README_MODELOS.md',
        'RESUMO_EXECUTIVO.md',
        'RESUMO_MODELOS.md',
        'STATUS.md',
    ],
}

def organize_project():
    """Reorganiza o projeto"""
    
    print('='*70)
    print('🧹 ORGANIZANDO PROJETO')
    print('='*70)
    
    # Mover arquivos Python
    print('\n🐍 Organizando arquivos Python...')
    
    for category, files in REORGANIZATION_MAP.items():
        for file in files:
            src = Path(file)
            if src.exists():
                if category == 'deprecated':
                    dst = Path('docs/deprecated') / src.name
                else:
                    dst = Path(f'src/{category}') / src.name
                
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.move(str(src), str(dst))
                    print(f'   ✅ {src.name} → {dst.relative_to(".")}')
                except Exception as e:
                    print(f'   ⚠️  {src.name}: {e}')
    
    # Mover documentação
    print('\n📚 Organizando documentação...')
    
    for category, files in DOCS_MAP.items():
        for file in files:
            src = Path(file)
            if src.exists():
                if category == 'deprecated':
                    dst = Path('docs/deprecated') / src.name
                else:
                    dst = Path('docs') / src.name
                
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.move(str(src), str(dst))
                    print(f'   ✅ {src.name} → {dst.relative_to(".")}')
                except Exception as e:
                    print(f'   ⚠️  {src.name}: {e}')
    
    # Remover pastas de modelos antigas
    print('\n🗑️  Removendo pastas de modelos antigas...')
    
    old_model_dirs = [
        'models/corrected-cap-classifier',
        'models/enhanced-fast-classifier',
        'models/fast-cap-classifier',
        'models/ensemble',
        'models/resnet',
    ]
    
    for dir_path in old_model_dirs:
        if Path(dir_path).exists():
            try:
                shutil.rmtree(dir_path)
                print(f'   ✅ Removido: {dir_path}')
            except Exception as e:
                print(f'   ⚠️  {dir_path}: {e}')
    
    # Remover arquivos .webp inúteis em tampinhas
    print('\n🗑️  Limpando arquivos desnecessários...')
    
    webp_files = list(Path('tampinhas').glob('*.webp'))
    for f in webp_files:
        try:
            f.unlink()
            print(f'   ✅ Removido: {f.name}')
        except Exception as e:
            print(f'   ⚠️  {f.name}: {e}')
    
    print('\n' + '='*70)
    print('✅ PROJETO REORGANIZADO COM SUCESSO!')
    print('='*70)

if __name__ == '__main__':
    organize_project()
