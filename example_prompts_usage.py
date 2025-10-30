#!/usr/bin/env python3
"""
EXEMPLO DE USO: Prompts & Agents
=================================
Demonstra como usar a estrutura de prompts organizada
"""

import sys
import os

# Adicionar pasta do projeto ao path
sys.path.insert(0, '/Users/caroline/Desktop/FIAP/totem-ia')

print("=" * 80)
print("EXEMPLOS DE USO: Prompts & Agents - TOTEM IA")
print("=" * 80)

# ============================================================================
# EXEMPLO 1: Usar Agent Config
# ============================================================================
print("\n\n📌 EXEMPLO 1: Usar Agent Config Centralizada")
print("-" * 80)

from prompts.agents_config import get_agent, list_agents

print("\n✅ Agents disponíveis:")
agents = list_agents()
for name, description in agents.items():
    print(f"   • {name}: {description}")

print("\n✅ Carregando agent 'sustainability':")
agent = get_agent("sustainability")

print(f"\n   Nome: {agent['metadata']['name']}")
print(f"   Versão: {agent['metadata']['version']}")
print(f"   Descrição: {agent['metadata']['description']}")
print(f"   Duração alvo: {agent['metadata']['target_duration_seconds']}s")

print(f"\n   Configuração OpenAI:")
print(f"      • Modelo: {agent['config']['model']}")
print(f"      • Temperatura: {agent['config']['temperature']}")
print(f"      • Max tokens: {agent['config']['max_tokens']}")

# ============================================================================
# EXEMPLO 2: Importar Diretamente
# ============================================================================
print("\n\n📌 EXEMPLO 2: Importar Agent Direto")
print("-" * 80)

from prompts.sustainability_agent import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    OPENAI_CONFIG,
    METADATA,
)

print("\n✅ System Prompt:")
print(f"   {SYSTEM_PROMPT}")

print("\n✅ User Prompt (resumido):")
lines = USER_PROMPT.split('\n')
for line in lines[:3]:
    if line.strip():
        print(f"   {line.strip()}")
print(f"   ... ({len(lines)} linhas total)")

print("\n✅ OpenAI Config:")
for key, value in OPENAI_CONFIG.items():
    print(f"   {key}: {value}")

# ============================================================================
# EXEMPLO 3: Usar em Aplicação (Simulado)
# ============================================================================
print("\n\n📌 EXEMPLO 3: Como Usar em Aplicação Flask")
print("-" * 80)

example_code = """
# Em app.py:
from prompts.agents_config import get_agent
import openai

def generate_sustainability_speech():
    # Obter agent de sustentabilidade
    agent = get_agent("sustainability")
    
    # Chamar OpenAI com configuração do agent
    response = openai.ChatCompletion.create(
        model=agent["config"]["model"],
        messages=[
            {"role": "system", "content": agent["system_prompt"]},
            {"role": "user", "content": agent["user_prompt"]},
        ],
        temperature=agent["config"]["temperature"],
        max_tokens=agent["config"]["max_tokens"],
    )
    
    script = response.choices[0].message.content.strip()
    return script
"""

print(example_code)

# ============================================================================
# EXEMPLO 4: Estrutura Esperada
# ============================================================================
print("\n\n📌 EXEMPLO 4: Estrutura de Retorno do get_agent()")
print("-" * 80)

import json

agent_structure = {
    "system_prompt": "string - prompt do sistema",
    "user_prompt": "string - prompt do usuário",
    "config": {
        "model": "string - modelo OpenAI",
        "temperature": "float - controle de criatividade",
        "max_tokens": "int - limite de tokens",
    },
    "metadata": {
        "name": "string - nome do agent",
        "version": "string - versão",
        "description": "string - descrição",
        "target_duration_seconds": "string - duração alvo",
        "output_format": "string - formato de saída",
    },
    "description": "string - descrição geral",
}

print(json.dumps(agent_structure, indent=2, ensure_ascii=False))

# ============================================================================
# EXEMPLO 5: Adicionar Novo Agent
# ============================================================================
print("\n\n📌 EXEMPLO 5: Como Adicionar Novo Agent")
print("-" * 80)

add_agent_example = """
1. Criar arquivo prompts/novo_agent.py:
   ────────────────────────────────────
   SYSTEM_PROMPT = "Você é um especialista em..."
   USER_PROMPT = "Gere um... com os seguintes requisitos..."
   OPENAI_CONFIG = {"model": "gpt-3.5-turbo", ...}
   METADATA = {"name": "Novo Agent", ...}

2. Atualizar prompts/agents_config.py:
   ───────────────────────────────────
   from .novo_agent import (
       SYSTEM_PROMPT as NOVO_SYSTEM_PROMPT,
       USER_PROMPT as NOVO_USER_PROMPT,
       OPENAI_CONFIG as NOVO_CONFIG,
       METADATA as NOVO_METADATA,
   )
   
   AGENTS = {
       "sustainability": {...},
       "novo_agent": {
           "system_prompt": NOVO_SYSTEM_PROMPT,
           "user_prompt": NOVO_USER_PROMPT,
           "config": NOVO_CONFIG,
           "metadata": NOVO_METADATA,
           "description": "Descrição do novo agent",
       },
   }

3. Usar igual aos outros:
   ──────────────────────
   agent = get_agent("novo_agent")
"""

print(add_agent_example)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 80)
print("✅ RESUMO")
print("=" * 80)

print("""
✅ Prompts organizados em pasta dedica: /prompts
✅ Agents configuráveis e reutilizáveis
✅ Sistema extensível para novos agents
✅ Documentação completa em prompts/README.md
✅ Integrado com app.py
✅ Testável e manutenível

Próximos passos:
- Criar mais agents conforme necessário
- Implementar sistema de versionamento
- Adicionar testes unitários
- Criar dashboard para gerenciar agents
""")

print("=" * 80)
