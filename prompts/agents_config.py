"""
AGENTS CONFIGURATION
====================
Configuração centralizada de todos os agents utilizados no TOTEM IA.

Estrutura:
- agents_config.py         (este arquivo - registry)
- sustainability_agent.py  (agente de sustentabilidade)
- sustainability_prompts.py (prompts de voz)
- sustainability_config.py (configurações)
"""

# Import dos agents
from .sustainability_agent import (
    SYSTEM_PROMPT as SUSTAINABILITY_SYSTEM_PROMPT,
    USER_PROMPT as SUSTAINABILITY_USER_PROMPT,
    OPENAI_CONFIG as SUSTAINABILITY_CONFIG,
    METADATA as SUSTAINABILITY_METADATA,
    get_user_prompt,
    get_all_config,
)

# Registry de agents disponíveis
AGENTS = {
    "sustainability": {
        "system_prompt": SUSTAINABILITY_SYSTEM_PROMPT,
        "user_prompt": SUSTAINABILITY_USER_PROMPT,
        "config": SUSTAINABILITY_CONFIG,
        "metadata": SUSTAINABILITY_METADATA,
        "description": "Gera scripts de áudio sobre sustentabilidade",
    },
}

# Configuração padrão para todos os agents
DEFAULT_CONFIG = {
    "timeout": 30,  # segundos
    "retry_attempts": 3,
    "cache_enabled": True,
    "cache_duration": 86400,  # 24 horas
}

def get_agent(agent_name: str):
    """Retorna configuração de um agent específico"""
    if agent_name not in AGENTS:
        raise ValueError(f"Agent '{agent_name}' não encontrado. Disponíveis: {list(AGENTS.keys())}")
    return AGENTS[agent_name]

def list_agents():
    """Lista todos os agents disponíveis"""
    return {
        name: agent["description"]
        for name, agent in AGENTS.items()
    }

if __name__ == "__main__":
    print("=" * 70)
    print("AGENTES DISPONÍVEIS NO TOTEM IA")
    print("=" * 70)
    
    agents = list_agents()
    for name, description in agents.items():
        print(f"\n📌 {name.upper()}")
        print(f"   {description}")
    
    print("\n" + "=" * 70)
    print("CONFIGURAÇÃO PADRÃO:")
    print("=" * 70)
    for key, value in DEFAULT_CONFIG.items():
        print(f"  {key}: {value}")
