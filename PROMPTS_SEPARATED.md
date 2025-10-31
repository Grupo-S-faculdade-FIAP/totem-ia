# 📝 Prompts Separados em Config + Prompts

## ✅ ESTRUTURA ATUALIZADA

Agora a configuração está separada em **DOIS ARQUIVOS** para melhor organização:

```
prompts/
├── __init__.py                     
├── agents_config.py                (Registry de agents)
├── sustainability_agent.py         (Agent - Orquestração)
├── sustainability_prompts.py       (✨ NOVO - Prompts de voz)
├── sustainability_config.py        (✨ NOVO - Configurações)
└── README.md
```

---

## 📋 SEPARAÇÃO DE RESPONSABILIDADES

### 1. **`sustainability_config.py`** (Configurações)

Contém TODAS as configurações e parâmetros:

```python
OPENAI_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 300,
}

METADATA = {
    "name": "Sustainability Script Generator",
    "version": "2.0",
    "focus": "tampinhas_reciclaveis",  # ← NOVO FOCUS
    ...
}

CACHE_CONFIG = {...}
TIMEOUT_CONFIG = {...}
RETRY_CONFIG = {...}
FALLBACK_CONFIG = {...}
```

**Responsabilidades:**
- ⚙️ Parâmetros OpenAI
- ⚙️ Metadados
- ⚙️ Configurações de cache
- ⚙️ Timeout e retry
- ⚙️ Fallback strategies

---

### 2. **`sustainability_prompts.py`** (Prompts de Voz)

Contém TODOS os prompts para geração de scripts:

```python
SYSTEM_PROMPT = "Você é um assistista educativo especializado em..."

USER_PROMPT = "Gere um script sobre TAMPINHAS RECICLÁVEIS..."

USER_PROMPT_ALT = "Versão alternativa com dados técnicos..."
USER_PROMPT_KIDS = "Versão infantil..."
USER_PROMPT_TECHNICAL = "Versão técnica com estatísticas..."

EXAMPLE_OUTPUTS = [...]
TAGS = ["tampinhas", "recicláveis", ...]
```

**Responsabilidades:**
- 🎤 System prompt
- 🎤 User prompts (4 variações!)
- 🎤 Exemplos de saída
- 🎤 Tags e keywords

---

### 3. **`sustainability_agent.py`** (Agent - Orquestração)

Importa e orquestra prompts + configs:

```python
from .sustainability_prompts import SYSTEM_PROMPT, USER_PROMPT, ...
from .sustainability_config import OPENAI_CONFIG, METADATA, ...

# Funções utilitárias
def get_user_prompt(prompt_type="default"):
    """Retorna prompt específico"""
    prompts = {
        "default": USER_PROMPT,
        "alt": USER_PROMPT_ALT,
        "kids": USER_PROMPT_KIDS,
        "technical": USER_PROMPT_TECHNICAL,
    }
    return prompts.get(prompt_type, USER_PROMPT)
```

**Responsabilidades:**
- 🤖 Orquestração
- 🤖 Funções utilitárias
- 🤖 Interface pública

---

## 🎯 FOCO ATUALIZADO: TAMPINHAS RECICLÁVEIS

O novo prompt está **100% focado em tampinhas recicláveis**:

### Mudanças Principais:

✅ **Antes:**
```
"Crie um texto breve sobre sustentabilidade e reciclagem de tampinhas"
```

✅ **Agora:**
```
"Gere um script especificamente sobre TAMPINHAS RECICLÁVEIS e sua importância"
```

### Destaques do Novo Script:

- 🔄 Tampinhas são **100% recicláveis**
- ⏱️ Demora **400+ anos** para se decompor
- 🏭 Viram **fibras têxteis, móveis, objetos**
- 🌍 **Bilhões acabam nos oceanos**
- 💪 **Chamada à ação persuasiva**

---

## 🎤 MÚLTIPLAS VERSÕES DE PROMPTS

Agora suportamos **4 versões diferentes**:

### 1. **Default** (Principal)
- Geral, equilibrado
- 30-45 segundos
- Para público geral

### 2. **ALT** (Com Dados)
- Foco em estatísticas e dados
- Mais técnico
- Impactante com números

### 3. **KIDS** (Infantil)
- Linguagem divertida
- 20-25 segundos
- Engajamento infantil

### 4. **TECHNICAL** (Técnico)
- Detalhes de composição
- Processos de reciclagem
- Para públicos informados
- 40-50 segundos

### Como Usar:
```python
from prompts.sustainability_agent import get_user_prompt

# Padrão
prompt = get_user_prompt("default")

# Alternativas
prompt = get_user_prompt("alt")        # Com dados
prompt = get_user_prompt("kids")       # Infantil
prompt = get_user_prompt("technical")  # Técnico
```

---

## 📊 BENEFÍCIOS DA SEPARAÇÃO

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Localização Prompts** | Espalhado | `sustainability_prompts.py` |
| **Localização Config** | Misturado | `sustainability_config.py` |
| **Editar Prompt** | Editar agent | Editar prompts.py |
| **Editar Config** | Editar agent | Editar config.py |
| **Reutilização** | Difícil | Fácil |
| **Versões** | 1 | 4 versões! |
| **Manutenção** | Complexa | Simples |

---

## 🚀 PRÓXIMAS VARIAÇÕES

Fácil adicionar mais variações:

```python
# Em sustainability_prompts.py

USER_PROMPT_PORTUGUESE_BR = "..."  # PT-BR
USER_PROMPT_ENGLISH = "..."        # English
USER_PROMPT_SPANISH = "..."        # Español

USER_PROMPT_ANGRY_TONE = "..."     # Tom agressivo
USER_PROMPT_FRIENDLY_TONE = "..."  # Ton amigável

USER_PROMPT_LONG_FORM = "..."      # 60+ segundos
USER_PROMPT_SHORT_FORM = "..."     # 15-20 segundos
```

---

## 📚 ESTRUTURA DE ARQUIVOS

```
prompts/
│
├── __init__.py
│   └── Exporta: get_agent, list_agents, AGENTS, DEFAULT_CONFIG
│
├── agents_config.py
│   └── Registry centralizado de agents
│
├── sustainability_agent.py (v2.0)
│   ├── Importa prompts + config
│   ├── Orquestra componentes
│   └── Exporta funções públicas
│
├── sustainability_prompts.py (✨ NOVO)
│   ├── SYSTEM_PROMPT
│   ├── USER_PROMPT (default)
│   ├── USER_PROMPT_ALT
│   ├── USER_PROMPT_KIDS
│   ├── USER_PROMPT_TECHNICAL
│   ├── EXAMPLE_OUTPUTS
│   └── TAGS
│
├── sustainability_config.py (✨ NOVO)
│   ├── OPENAI_CONFIG
│   ├── METADATA (com focus: "tampinhas_reciclaveis")
│   ├── CACHE_CONFIG
│   ├── TIMEOUT_CONFIG
│   ├── RETRY_CONFIG
│   ├── LOGGING_CONFIG
│   └── FALLBACK_CONFIG
│
└── README.md
    └── Documentação atualizada
```

---

## ✅ TESTES REALIZADOS

```bash
# ✅ Testar prompts
python3 prompts/sustainability_prompts.py

# ✅ Testar configurações
python3 prompts/sustainability_config.py

# ✅ Testar agent
python3 prompts/sustainability_agent.py

# ✅ Testar integração
python3 -c "from prompts.agents_config import get_agent; agent = get_agent('sustainability')"

# ✅ Servidor rodando
curl http://localhost:5003 → ✅ Carregando com novo prompt
```

---

## 🎬 SERVIDOR

✅ **Rodando** em http://localhost:5003  
✅ **Novo prompt** sendo usado automaticamente  
✅ **Áudio gerado** com foco em tampinhas recicláveis  
✅ **Player** funcionando normalmente

---

## 📝 PRÓXIMAS ETAPAS

1. **Testar TTS** com novo prompt
2. **Validar QA** do conteúdo
3. **Medir tempo** de áudio (deve ser 30-45s)
4. **Adicionar mais variações** conforme necessário
5. **Documentar** todas as versões

---

**Status:** ✅ 100% Implementado  
**Data:** 30/10/2025  
**Focus:** 🎯 Tampinhas Recicláveis  
**Versões:** 4️⃣ (default, alt, kids, technical)
