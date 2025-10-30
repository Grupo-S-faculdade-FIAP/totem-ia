"""
Prompts & Agents - TOTEM IA
============================
Pacote centralizado de prompts e agents para o sistema TOTEM IA.

Uso:
    from prompts.agents_config import get_agent
    agent = get_agent("sustainability")
"""

from .agents_config import get_agent, list_agents, AGENTS, DEFAULT_CONFIG

__version__ = "1.0.0"
__author__ = "TOTEM IA Team"
__all__ = ["get_agent", "list_agents", "AGENTS", "DEFAULT_CONFIG"]
