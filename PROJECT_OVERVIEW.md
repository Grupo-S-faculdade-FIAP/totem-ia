# 🚀 TOTEM IA — Project Overview

> **Inteligência Artificial para Reciclagem de Tampinhas**
> 
> Um totem interativo que classifica tampinhas de plástico usando IA (SVM), 
> valida mecanicamente via ESP32, registra dados em BD e fornece feedback 
> de sustentabilidade ambiental.

---

## 📊 Visão Geral do Projeto

```
Usuário chega com tampinha
         ↓
    Tira foto
         ↓
    Envia para /api/classify
         ↓
    SVM prediz (tampinha ou não)
         ↓
    ESP32 valida peso/presença
         ↓
    Registra em BD
         ↓
    Toca áudio de sustentabilidade
         ↓
    Tampinha é aceita ✅
```

---

## 🏗️ Stack Técnico

| Camada | Tecnologia | Localização |
|--------|-----------|------------|
| **API** | Flask (Python 3.9+) | `app.py` (969 linhas) |
| **Classificação** | SVM (8 features) | `src/modules/image.py` |
| **Armazenamento** | SQLite | `src/database/db.py` |
| **Hardware** | ESP32 (REST API) | `src/hardware/esp32.py` |
| **Testes** | pytest (261 testes) | `tests/` (100% cobertura) |

---

## 📁 Estrutura do Projeto

```
totem-ia/
├── 🎯 app.py                          ← COMECE AQUI
├── 🧪 tests/ (261 testes)
│   ├── test_routes.py (66 testes)     ← Rotas Flask
│   ├── test_classify.py (17 testes)   ← ML
│   ├── test_database.py (18 testes)   ← BD
│   └── ... (8 mais)
│
├── 🔧 src/
│   ├── modules/image.py               ← Classificador ML (SVM)
│   ├── database/db.py                 ← BD SQLite
│   ├── hardware/esp32.py              ← Comunicação ESP32
│   ├── models_classifiers/            ← Análise offline
│   └── models_trainers/               ← Script de treino
│
├── 📦 models/svm/
│   ├── svm_model_complete.pkl         ← Modelo treinado
│   └── scaler_complete.pkl            ← Normalizador
│
├── 📚 .cursor/rules/
│   ├── project-overview.mdc           ← Este guia (regra)
│   ├── clean-architecture.mdc         ← Arquitetura
│   ├── ml-conventions.mdc             ← ML rules
│   ├── testing.mdc                    ← Testes
│   └── ... (5 mais)
│
└── 📄 README.md, TESTES_README.md, DEBUG_MODE.md
```

---

## 🎯 Principais Conceitos

### 1️⃣ Fluxo de Classificação

**Entrada:** Imagem da tampinha  
**Processamento:**
1. Extrai 8 features (cores BGR + HSV + contraste)
2. Normaliza com StandardScaler
3. Prediz com SVM (tampinha=1, não=0)
4. Aplica lógica de saturação (SAT_HIGH_THRESHOLD=120)

**Saída:** `(prediction, confidence, saturation, method)`

### 2️⃣ Métodos de Decisão (8 possíveis)

```
SAT_HIGH           → Saturação > 120 → Tampinha (conf 0.95)
SAT_VERY_LOW       → Saturação < 30  → Não-tampinha (conf 0.95)
MID_HIGH_SAT       → Sat > 100 + SVM=1 → Tampinha
NORMAL_SAT_TAMPINHA→ Sat 50-100 + SVM=1 → Tampinha
LOW_SAT_FORCE_TAMPINHA → Sat 30-50 → Força tampinha
DEBUG_MODE         → Modo debug ativo → Aceita tudo
ERRO               → Falha no processamento
```

### 3️⃣ Vetor de Features (8 dimensões — CRÍTICO)

```python
[
    0: Mean B,      1: Std B,      2: Median B,      # Canal B (BGR)
    3: Mean G,      4: Std G,      5: Median G,      # Canal G (BGR)
    6: Saturação,                                     # HSV (⭐ importante!)
    7: Contraste                                      # Grayscale
]
```

**Regra de Ouro:** Nunca altere sem retreinar o modelo em `src/models_trainers/svm_complete_classifier.py`

---

## 🧪 Testes: 261 Total, 100% Cobertura

### Distribuição
- **66 testes** em rotas Flask (`test_routes.py`)
- **23 testes** em ESP32 API (`test_esp32_functions.py`)
- **25 testes** em SVM completo (`test_svm_complete_classifier.py`)
- **21 testes** em classificador hybrid (`test_classify_hybrid_v2.py`)
- **18 testes** em BD (`test_database.py`)
- **18 testes** em ESP32 hardware (`test_esp32_hardware.py`)
- **22 testes** em SVM trainer (`test_svm_trainer.py`)
- **22 testes** em integração ESP32 (`test_esp32_integration.py`)
- **29 testes** em servidor ESP32 (`test_esp32_server.py`)
- **17 testes** em classificador (`test_classify.py`)

### Como Rodar
```bash
pytest                                   # Todos
pytest tests/test_routes.py -v          # Um arquivo
pytest -m unit                          # Apenas unitários
python scripts/analyze_coverage.py      # Análise
```

---

## 🔐 Regras de Arquitetura (Clean Architecture)

```
✅ app.py pode importar de src/
❌ src/modules/ NÃO importa de src/database/ ou src/hardware/
❌ Nenhum módulo em src/ importa app.py (ciclo!)
✅ Cada camada é independente
```

**Camadas:**
1. **Apresentação** (`app.py`) — Rotas HTTP
2. **Aplicação** (`src/modules/`) — Lógica de negócio
3. **Infraestrutura** (`src/database/`, `src/hardware/`) — Persistência e hardware

---

## 🚀 Comece Por Aqui

### 1. Entenda o Fluxo
Abra `app.py` e procure por `# ====` para ver as seções principais:
- Linhas 1-50: Setup inicial
- Linhas 100-150: Rotas de apresentação
- Linhas 170-260: Classificação
- Linhas 260-500: Validação
- Linhas 800-900: Admin

### 2. Se Adicionar Funcionalidade
1. Escreva o teste PRIMEIRO em `tests/test_routes.py`
2. Use padrão AAA (Arrange-Act-Assert)
3. Mocke dependências externas
4. Implemente a rota em `app.py`
5. Run `pytest` para validar

### 3. Se Mexer em ML
Leia `.cursor/rules/ml-conventions.mdc`:
- Features devem ser exatamente 8
- Saturação é o índice 6
- Thresholds em `src/modules/image.py`
- Nunca chamar `scaler.fit()` em produção

### 4. Se Tiver Dúvida
Consulte a tabela "Quando você não sabe onde mexer" abaixo

---

## 📋 Quick Reference

### Quando Você Não Sabe Onde Mexer...

| Tarefa | Arquivo | Linhas | Exemplo |
|--------|---------|--------|---------|
| Adicionar rota | `app.py` | 100-900 | `@app.route('/api/nova')` |
| Melhorar ML | `src/modules/image.py` | 1-200 | Alterar thresholds |
| Validação BD | `src/database/db.py` | 1-300 | Adicionar coluna |
| Comunicar ESP32 | `src/hardware/esp32.py` | 1-150 | Nova função |
| Testar rota | `tests/test_routes.py` | 1-450 | Novo `def test_*` |
| Entender ML | `.cursor/rules/ml-conventions.mdc` | — | Vetor de features |
| Debug | `DEBUG_MODE.md` | — | MODO_DEBUG=true |

---

## ✨ Características do Projeto

✅ **261 testes** (pytest, padrão AAA)  
✅ **100% cobertura** estimada  
✅ **Clean Architecture** (camadas bem definidas)  
✅ **Type hints** em funções públicas  
✅ **Logging** com emojis estruturado  
✅ **Docstrings em português**  
✅ **Sem dependências circulares**  
✅ **Pronto para produção**  

---

## 📚 Leia Nesta Ordem

1. Este arquivo (você está aqui)
2. `.cursor/rules/project-overview.mdc` (regra do Cursor)
3. `.cursor/rules/clean-architecture.mdc` (estrutura)
4. `.cursor/rules/ml-conventions.mdc` (se trabalhar com ML)
5. `TESTES_README.md` (como rodar testes)
6. `app.py` (código fonte principal)

---

## 🤝 Contribuindo

```bash
# 1. Criar branch
git checkout -b feature/minha-feature

# 2. Fazer mudança
# 3. Testar
pytest

# 4. Commit
git commit -m "feat: descrição da mudança"

# 5. Push
git push origin feature/minha-feature
```

**Importante:** Sempre escrever teste ANTES da implementação!

---

**Status:** Pronto para Produção ⭐⭐⭐⭐⭐  
**Última atualização:** 2026-03-03  
**Contato:** FIAP — Grupo S
