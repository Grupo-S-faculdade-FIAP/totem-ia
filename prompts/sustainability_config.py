"""
SUSTAINABILITY AGENT - CONFIGURATION
=====================================
Arquivo de configurações para o agent de sustentabilidade.
Separado de sustainability_prompts.py para melhor organização.
"""

# Configuração de parâmetros OpenAI
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,  # Criatividade moderada
    "max_tokens": 300,
}

# Metadados do Agent
METADATA = {
    "name": "Sustainability Script Generator",
    "version": "2.0",
    "description": "Gera scripts de áudio sobre sustentabilidade e reciclagem de tampinhas",
    "target_duration_seconds": "30-45",
    "output_format": "text",
    "language": "pt-BR",
    "focus": "tampinhas_reciclaveis",
}

# Configuração de cache
CACHE_CONFIG = {
    "enabled": True,
    "duration_seconds": 86400,  # 24 horas
    "storage": "file",  # file, memory, redis
}

# Configuração de timeout
TIMEOUT_CONFIG = {
    "openai_request": 30,  # segundos
    "tts_synthesis": 5,    # segundos
    "total_generation": 60, # segundos
}

# Configuração de retry
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2,  # exponencial
    "retry_on": ["timeout", "rate_limit", "service_error"],
}

# Configuração de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    "file": "logs/sustainability_agent.log",
}

# Configuração de fallback (casos de falha)
FALLBACK_CONFIG = {
    "use_cached_audio": True,
    "use_placeholder_audio": True,
    "placeholder_duration": 3,  # segundos
}

if __name__ == "__main__":
    print("=" * 70)
    print("CONFIGURAÇÃO: Sustainability Agent")
    print("=" * 70)
    print(f"\nNome: {METADATA['name']}")
    print(f"Versão: {METADATA['version']}")
    print(f"Focus: {METADATA['focus']}")
    print(f"\nConfigurações OpenAI:")
    for key, value in OPENAI_CONFIG.items():
        print(f"  {key}: {value}")
    print(f"\nTimeout (segundos):")
    for key, value in TIMEOUT_CONFIG.items():
        print(f"  {key}: {value}")
    print(f"\nRetry:")
    print(f"  Max tentativas: {RETRY_CONFIG['max_attempts']}")
    print(f"  Backoff factor: {RETRY_CONFIG['backoff_factor']}")
