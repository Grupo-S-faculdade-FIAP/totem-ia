#!/usr/bin/env python3
"""
Analisa cobertura de testes esperada.

Verifica quais módulos têm testes e estima cobertura.
"""
import os
import ast
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
TESTS_DIR = REPO_ROOT / "tests"
SRC_DIR = REPO_ROOT / "src"


def count_functions_and_classes(filepath: Path) -> tuple[int, int]:
    """Conta funções e classes em um arquivo Python."""
    if not filepath.exists():
        return 0, 0
    
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return 0, 0
    
    functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    
    return functions, classes


def get_test_count(test_file: Path) -> int:
    """Conta testes em um arquivo."""
    try:
        with open(test_file) as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return 0
    
    tests = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )
    return tests


def analyze():
    """Analisa cobertura de testes."""
    print("=" * 80)
    print("📊 ANÁLISE DE COBERTURA DE TESTES — TOTEM IA")
    print("=" * 80)
    print()
    
    # Mapear módulos com testes
    test_mapping = defaultdict(lambda: {"tests": 0, "funcs": 0, "classes": 0})
    
    # Contar testes
    for test_file in sorted(TESTS_DIR.glob("test_*.py")):
        # Inferir módulo pelo nome
        test_name = test_file.stem.replace("test_", "")
        test_count = get_test_count(test_file)
        test_mapping[test_name]["tests"] = test_count
        test_mapping[test_name]["test_file"] = test_file.name
    
    # Contar código fonte
    for src_file in sorted(SRC_DIR.rglob("*.py")):
        if src_file.name == "__pycache__":
            continue
        
        # Mapear nome
        if src_file.name == "image.py":
            module_name = "classify"
        elif src_file.name == "db.py":
            module_name = "database"
        else:
            module_name = src_file.stem
        
        funcs, classes = count_functions_and_classes(src_file)
        if funcs > 0 or classes > 0:
            test_mapping[module_name]["funcs"] += funcs
            test_mapping[module_name]["classes"] += classes
            test_mapping[module_name]["src_file"] = src_file.relative_to(REPO_ROOT)
    
    # Analisar app.py
    app_file = REPO_ROOT / "app.py"
    app_funcs, app_classes = count_functions_and_classes(app_file)
    if app_funcs > 0:
        test_mapping["routes"]["funcs"] += app_funcs
        test_mapping["routes"]["src_file"] = "app.py"
    
    # Imprimir relatório
    print(f"{'Módulo':<20} {'Testes':<8} {'Funcs':<8} {'Classes':<8} {'Ratio':<10} {'Status':<15}")
    print("-" * 80)
    
    total_tests = 0
    total_funcs = 0
    total_classes = 0
    
    for module_name in sorted(test_mapping.keys()):
        info = test_mapping[module_name]
        tests = info.get("tests", 0)
        funcs = info.get("funcs", 0)
        classes = info.get("classes", 0)
        src_file = info.get("src_file", "?")
        
        total_tests += tests
        total_funcs += funcs
        total_classes += classes
        
        # Calcular ratio (aproximado: 1 teste por função é bom)
        ratio = f"{tests}/{funcs}" if funcs > 0 else "N/A"
        
        # Status
        if tests == 0 and funcs > 0:
            status = "❌ Sem testes"
        elif tests >= funcs * 0.8:
            status = "✅ Bom"
        elif tests >= funcs * 0.5:
            status = "⚠️  Incompleto"
        else:
            status = "⚠️  Faltam testes"
        
        print(f"{module_name:<20} {tests:<8} {funcs:<8} {classes:<8} {ratio:<10} {status:<15}")
    
    print("-" * 80)
    print(f"{'TOTAL':<20} {total_tests:<8} {total_funcs:<8} {total_classes:<8}")
    print()
    print("=" * 80)
    print("📝 RECOMENDAÇÕES")
    print("=" * 80)
    print()
    
    missing = [m for m, info in test_mapping.items() if info.get("tests", 0) == 0 and info.get("funcs", 0) > 0]
    if missing:
        print(f"❌ Módulos SEM testes: {', '.join(missing)}")
        print()
    
    low_coverage = [
        (m, info["tests"], info["funcs"])
        for m, info in test_mapping.items()
        if info.get("funcs", 0) > 0 and info.get("tests", 0) < info.get("funcs", 0) * 0.5
    ]
    if low_coverage:
        print("⚠️  Módulos com cobertura < 50%:")
        for m, tests, funcs in low_coverage:
            print(f"  - {m}: {tests}/{funcs} testes")
        print()
    
    print("✅ Para melhorar cobertura:")
    print("  1. Executar: pytest --cov=src --cov=app --cov-report=html")
    print("  2. Abrir: htmlcov/index.html")
    print("  3. Adicionar testes para linhas não cobertas")
    print()


if __name__ == "__main__":
    analyze()
