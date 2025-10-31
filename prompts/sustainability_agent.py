"""
AGENT: Sustainability Content Generator
========================================
Agent orquestrador para geração de conteúdo de sustentabilidade.
Importa prompts FIXOS de sustainability_prompts.py
"""

# Importar o prompt EXATO e FIXO
from .sustainability_prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    TAGS,
)


def get_system_prompt():
    """Retorna o system prompt"""
    return SYSTEM_PROMPT


def get_user_prompt():
    """Retorna o user prompt FIXO"""
    return USER_PROMPT


def get_tags():
    """Retorna tags para rastreamento"""
    return TAGS


if __name__ == "__main__":
    print("=" * 70)
    print("SUSTAINABILITY AGENT - PROMPT ÚNICO E FIXO")
    print("=" * 70)
    print("\n✅ System Prompt:")
    print(SYSTEM_PROMPT)
    print("\n✅ User Prompt (FIXO - sem alterações):")
    print(USER_PROMPT)
    print("\n" + "=" * 70)
