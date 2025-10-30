"""
AGENT: Sustainability Content Generator v2.0
==============================================
Agent responsável por gerar conteúdo educativo sobre sustentabilidade
e reciclagem de tampinhas recicláveis para o TOTEM IA.

Estrutura separada em:
- sustainability_agent.py      (este arquivo - orquestração)
- sustainability_prompts.py    (prompts de voz)
- sustainability_config.py     (configurações)
"""

# Importar prompts e configurações
try:
    from .sustainability_prompts import (
        SYSTEM_PROMPT,
        USER_PROMPT,
        USER_PROMPT_ALT,
        USER_PROMPT_KIDS,
        USER_PROMPT_TECHNICAL,
        EXAMPLE_OUTPUTS,
        TAGS,
    )

    from .sustainability_config import (
        OPENAI_CONFIG,
        METADATA,
        CACHE_CONFIG,
        TIMEOUT_CONFIG,
        RETRY_CONFIG,
        LOGGING_CONFIG,
        FALLBACK_CONFIG,
    )
except ImportError:
    # Para execução direta do script
    import sustainability_prompts as prompts_module
    import sustainability_config as config_module
    
    SYSTEM_PROMPT = prompts_module.SYSTEM_PROMPT
    USER_PROMPT = prompts_module.USER_PROMPT
    USER_PROMPT_ALT = prompts_module.USER_PROMPT_ALT
    USER_PROMPT_KIDS = prompts_module.USER_PROMPT_KIDS
    USER_PROMPT_TECHNICAL = prompts_module.USER_PROMPT_TECHNICAL
    EXAMPLE_OUTPUTS = prompts_module.EXAMPLE_OUTPUTS
    TAGS = prompts_module.TAGS
    
    OPENAI_CONFIG = config_module.OPENAI_CONFIG
    METADATA = config_module.METADATA
    CACHE_CONFIG = config_module.CACHE_CONFIG
    TIMEOUT_CONFIG = config_module.TIMEOUT_CONFIG
    RETRY_CONFIG = config_module.RETRY_CONFIG
    LOGGING_CONFIG = config_module.LOGGING_CONFIG
    FALLBACK_CONFIG = config_module.FALLBACK_CONFIG

# Metadados do Agent (compatibilidade com versão anterior)
__version__ = "2.0"
__author__ = "TOTEM IA Team"
__description__ = "Generator de scripts sobre tampinhas recicláveis"


# Funções utilitárias

def get_system_prompt():
    """Retorna o system prompt do agent"""
    return SYSTEM_PROMPT


def get_user_prompt(prompt_type="default"):
    """
    Retorna o user prompt conforme o tipo.
    
    Types:
    - default: Prompt principal
    - alt: Versão com dados técnicos
    - kids: Versão infantil
    - technical: Versão técnica com estatísticas
    """
    prompts = {
        "default": USER_PROMPT,
        "alt": USER_PROMPT_ALT,
        "kids": USER_PROMPT_KIDS,
        "technical": USER_PROMPT_TECHNICAL,
    }
    return prompts.get(prompt_type, USER_PROMPT)


def get_config():
    """Retorna configuração OpenAI"""
    return OPENAI_CONFIG


def get_metadata():
    """Retorna metadados do agent"""
    return METADATA


def get_all_config():
    """Retorna todas as configurações"""
    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": USER_PROMPT,
        "openai_config": OPENAI_CONFIG,
        "metadata": METADATA,
        "cache_config": CACHE_CONFIG,
        "timeout_config": TIMEOUT_CONFIG,
        "retry_config": RETRY_CONFIG,
        "logging_config": LOGGING_CONFIG,
        "fallback_config": FALLBACK_CONFIG,
    }


if __name__ == "__main__":
    print("=" * 70)
    print(f"AGENT: {METADATA['name']}")
    print(f"Versão: {METADATA['version']}")
    print("=" * 70)
    print(f"\nDescrição: {METADATA['description']}")
    print(f"Duração alvo: {METADATA['target_duration_seconds']}s")
    print(f"Focus: {METADATA['focus']}")
    print(f"\nModelo OpenAI: {OPENAI_CONFIG['model']}")
    print(f"Temperatura: {OPENAI_CONFIG['temperature']}")
    print(f"Max tokens: {OPENAI_CONFIG['max_tokens']}")
    print("\n" + "=" * 70)
    print("SYSTEM PROMPT:")
    print("=" * 70)
    print(SYSTEM_PROMPT)
    print("\n" + "=" * 70)
    print("USER PROMPT (Principal):")
    print("=" * 70)
    print(USER_PROMPT)
    print("\n" + "=" * 70)
    print("Prompts Alternativos:")
    print("=" * 70)
    print("• get_user_prompt('alt') - Versão com dados")
    print("• get_user_prompt('kids') - Versão infantil")
    print("• get_user_prompt('technical') - Versão técnica")
    print("\n" + "=" * 70)
    print("EXEMPLOS DE SAÍDA:")
    print("=" * 70)
    for i, example in enumerate(EXAMPLE_OUTPUTS, 1):
        print(f"\nExemplo {i}:")
        print(f"{example}\n")


# System Prompt para o agente de sustentabilidade
SYSTEM_PROMPT = """Você é um assistente educativo especializado em sustentabilidade ambiental e reciclagem."""

# Prompt do usuário para geração de script
USER_PROMPT = """Gere um script de áudio engajante e educativo sobre sustentabilidade e reciclagem de tampinhas de plástico.

O script deve:
- Durar entre 30-45 segundos quando lido em voz alta
- Ser motivador e positivo
- Explicar por que reciclar tampinhas é importante
- Incluir dados/curiosidades sobre impacto ambiental
- Terminar com uma chamada à ação
- Ser apropriado para uso em um totem interativo em espaço público

Apenas retorne o texto do script, sem explicações adicionais."""

# Configuração de parâmetros OpenAI
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,  # Criatividade moderada
    "max_tokens": 300,
}

# Metadados do Agent
METADATA = {
    "name": "Sustainability Script Generator",
    "version": "1.0",
    "description": "Gera scripts de áudio sobre sustentabilidade e reciclagem",
    "target_duration_seconds": "30-45",
    "output_format": "text",
}

# Exemplos de saídas esperadas
EXAMPLE_OUTPUTS = [
    """Olá! Você sabia que cada tampinha de plástico demora mais de 400 anos para se decompor na natureza? 
    Quando você recicla tampinhas, ajuda a reduzir resíduos plásticos nos oceanos e aterros sanitários. 
    Uma tampinha reciclada pode se tornar um novo produto útil, economizando recursos naturais e energia. 
    Cada ação conta! Venha reciclar suas tampinhas agora e faça parte da solução para um planeta mais limpo e sustentável.""",
    
    """Reciclar é um superpoder! Tampinhas de plástico podem ser transformadas em fibras têxteis, 
    móveis sustentáveis e muito mais. Bilhões de tampinhas acabam nos oceanos todos os anos. 
    Ao reciclar, você protege a vida marinha e reduz poluição. Sua contribuição é valiosa! 
    Deposite suas tampinhas aqui e seja parte da mudança ambiental positiva.""",
]

if __name__ == "__main__":
    print("=" * 70)
    print(f"AGENT: {METADATA['name']}")
    print(f"Version: {METADATA['version']}")
    print("=" * 70)
    print(f"\nDescrição: {METADATA['description']}")
    print(f"Duração alvo: {METADATA['target_duration_seconds']}s")
    print(f"Modelo OpenAI: {OPENAI_CONFIG['model']}")
    print(f"Temperatura: {OPENAI_CONFIG['temperature']}")
    print(f"Max tokens: {OPENAI_CONFIG['max_tokens']}")
    print("\n" + "=" * 70)
    print("SYSTEM PROMPT:")
    print("=" * 70)
    print(SYSTEM_PROMPT)
    print("\n" + "=" * 70)
    print("USER PROMPT:")
    print("=" * 70)
    print(USER_PROMPT)
    print("\n" + "=" * 70)
    print("EXEMPLOS DE SAÍDA:")
    print("=" * 70)
    for i, example in enumerate(EXAMPLE_OUTPUTS, 1):
        print(f"\nExemplo {i}:")
        print(f"{example}\n")
