# 📋 Prompts & Agents - TOTEM IA

Organização centralizada de prompts e agents para o sistema TOTEM IA.

## 📁 Estrutura

```
prompts/
├── README.md                      # Este arquivo
├── agents_config.py               # Configuração central de agents
├── sustainability_agent.py        # Agent: Gerador de scripts de sustentabilidade
└── future_agents/                # (Para futuros agents)
    ├── classification_agent.py   # (Futuro) Agent de classificação de imagens
    └── recommendation_agent.py   # (Futuro) Agent de recomendações
```

## 🤖 Agents Disponíveis

### 1. **Sustainability Agent** (`sustainability_agent.py`)

**Propósito:** Gerar scripts de áudio engajantes e educativos sobre sustentabilidade e reciclagem.

**Configuração:**
```python
from prompts.sustainability_agent import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    OPENAI_CONFIG,
)
```

**Parâmetros:**
- **Modelo:** `gpt-3.5-turbo`
- **Temperatura:** 0.7 (criatividade moderada)
- **Max Tokens:** 300
- **Duração alvo:** 30-45 segundos

**Sistema Prompt:**
> "Você é um assistente educativo especializado em sustentabilidade ambiental e reciclagem."

**Requisitos do Script:**
- Motivador e positivo
- Explica importância de reciclar tampinhas
- Inclui dados/curiosidades sobre impacto ambiental
- Chamada à ação no final
- Apropriado para totem em espaço público

## 🚀 Como Usar

### Opção 1: Importar Agent Específico

```python
from prompts.sustainability_agent import SYSTEM_PROMPT, USER_PROMPT, OPENAI_CONFIG

response = openai.ChatCompletion.create(
    model=OPENAI_CONFIG["model"],
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ],
    temperature=OPENAI_CONFIG["temperature"],
    max_tokens=OPENAI_CONFIG["max_tokens"],
)
```

### Opção 2: Usar Agent Config

```python
from prompts.agents_config import get_agent

agent = get_agent("sustainability")
config = agent["config"]
system_prompt = agent["system_prompt"]
user_prompt = agent["user_prompt"]

response = openai.ChatCompletion.create(
    model=config["model"],
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    **{k: v for k, v in config.items() if k != "model"},
)
```

### Opção 3: Listar Agents Disponíveis

```python
from prompts.agents_config import list_agents

available_agents = list_agents()
print(available_agents)
# Output: {'sustainability': 'Gera scripts de áudio sobre sustentabilidade'}
```

## 📝 Executar Agent Diretamente

```bash
# Ver configuração do agent de sustentabilidade
python3 prompts/sustainability_agent.py

# Ver todos os agents disponíveis
python3 prompts/agents_config.py
```

## 🔄 Integração com app.py

Atualize `app.py` para usar os prompts organizados:

```python
from prompts.agents_config import get_agent

def generate_sustainability_script():
    agent = get_agent("sustainability")
    
    response = openai.ChatCompletion.create(
        model=agent["config"]["model"],
        messages=[
            {"role": "system", "content": agent["system_prompt"]},
            {"role": "user", "content": agent["user_prompt"]},
        ],
        temperature=agent["config"]["temperature"],
        max_tokens=agent["config"]["max_tokens"],
    )
    
    return response.choices[0].message.content.strip()
```

## 📊 Exemplos de Saída

O agent de sustentabilidade gera scripts como:

> "Olá! Você sabia que cada tampinha de plástico demora mais de 400 anos para se decompor na natureza? 
> Quando você recicla tampinhas, ajuda a reduzir resíduos plásticos nos oceanos e aterros sanitários. 
> Uma tampinha reciclada pode se tornar um novo produto útil, economizando recursos naturais e energia. 
> Cada ação conta! Venha reciclar suas tampinhas agora e faça parte da solução para um planeta mais limpo e sustentável."

## 🔮 Próximos Agents

- **Classification Agent:** Análise de imagens de tampinhas
- **Recommendation Agent:** Recomendações de ações sustentáveis
- **Analytics Agent:** Análise de dados de reciclagem

## 📄 Versionamento

- **Atual:** Sustainability Agent v1.0
- **Próxima:** Suporte multi-idioma

---

**Last Updated:** 30/10/2025  
**Maintainer:** TOTEM IA Team
