#!/usr/bin/env python3
"""
🐛 TESTE DE MODO DEBUG
Verifica se a flag está funcionando corretamente
"""

import requests
import json
from pathlib import Path

# Config
API_URL = "http://localhost:8000"
DEBUG_ENDPOINT = f"{API_URL}/api/debug-confirm"

print("\n" + "="*70)
print("🐛 TESTE DE MODO DEBUG - TOTEM IA")
print("="*70 + "\n")

# Teste 1: Chamar endpoint com DEBUG
print("1️⃣  Testando endpoint /api/debug-confirm...")
print(f"   URL: {DEBUG_ENDPOINT}\n")

try:
    response = requests.post(DEBUG_ENDPOINT, json={"debug": True}, timeout=5)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ SUCESSO: Endpoint retornou 200")
        data = response.json()
        print(f"\n   Resposta:")
        print(f"   - Status: {data.get('status')}")
        print(f"   - Message: {data.get('message')}")
        print(f"   - Debug Mode: {data.get('debug_mode')}")
        print(f"   - Etapa 1: {data['stages']['classificacao']['method']}")
        print(f"   - Confiança: {data['stages']['classificacao']['confidence']}")
        print(f"   - Peso simulado: {data['stages']['mecanica']['peso']}")
        
    elif response.status_code == 403:
        print("   ⚠️  MODO DEBUG DESATIVADO")
        print("   Para ativar: MODO_DEBUG=true em .env")
        data = response.json()
        print(f"   Resposta: {data.get('message')}")
        
    else:
        print(f"   ❌ ERRO: Status {response.status_code}")
        print(f"   Resposta: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ ERRO: Não conseguiu conectar ao servidor")
    print("   Verifique se Flask está rodando: python app.py")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

print("\n" + "="*70)
print("2️⃣  Verificando .env...")
print("="*70 + "\n")

env_path = Path(".env")
if env_path.exists():
    with open(env_path, 'r') as f:
        content = f.read()
        if "MODO_DEBUG" in content:
            for line in content.split('\n'):
                if "MODO_DEBUG" in line and not line.strip().startswith('#'):
                    print(f"   ✅ Encontrado: {line}")
        else:
            print("   ⚠️  MODO_DEBUG não encontrado em .env")
            print("   Copie .env.example: cp .env.example .env")
else:
    print("   ⚠️  Arquivo .env não encontrado")
    print("   Crie a partir de .env.example: cp .env.example .env")

print("\n" + "="*70)
print("3️⃣  Verificando template...")
print("="*70 + "\n")

template_path = Path("templates/totem_v2.html")
if template_path.exists():
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = {
            "Botão debug HTML": "debugConfirmBtn",
            "Conditional Jinja2": "{% if modo_debug %}",
            "CSS .btn-warning": ".btn-warning",
            "Event listener": "debugConfirmBtn.addEventListener",
            "Chamada API": "/api/debug-confirm"
        }
        
        for check_name, pattern in checks.items():
            if pattern in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name} não encontrado")
else:
    print("   ❌ Template não encontrado")

print("\n" + "="*70)
print("4️⃣  Verificando app.py...")
print("="*70 + "\n")

app_path = Path("app.py")
if app_path.exists():
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = {
            "Flag MODO_DEBUG": "MODO_DEBUG = os.getenv",
            "Verificação if": "if MODO_DEBUG:",
            "Endpoint debug": "@app.route('/api/debug-confirm'",
            "Proteção 403": "return jsonify",
            "Log de aviso": "logger.warning"
        }
        
        for check_name, pattern in checks.items():
            if pattern in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name} não encontrado")
else:
    print("   ❌ app.py não encontrado")

print("\n" + "="*70)
print("✅ RESUMO")
print("="*70)
print("""
Se todos os testes passaram ✅, você pode:

1. Editar .env e adicionar:
   MODO_DEBUG=true

2. Reiniciar Flask:
   python app.py

3. Acessar:
   http://localhost:8000/totem_v2.html

4. Tirar uma foto e clicar em "🐛 Modo Debug Confirmar"

⚠️  Lembre-se: Nunca use em produção!
""")
print("="*70 + "\n")
