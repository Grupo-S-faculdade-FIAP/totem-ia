# 🚀 GUIA DE USO - MODELOS DE CLASSIFICAÇÃO DE TAMPINHAS

## 📋 Índice

1. [Opção 1: Menu Interativo](#opção-1-menu-interativo)
2. [Opção 2: Linha de Comando](#opção-2-linha-de-comando)
3. [Modelos Disponíveis](#modelos-disponíveis)
4. [Troubleshooting](#troubleshooting)

---

## Opção 1: Menu Interativo ⭐ (RECOMENDADO)

### Usar o menu principal para gerenciar tudo de forma fácil

```bash
python main.py
```

**Funcionalidades do Menu:**
- 1️⃣ Treinar e classificar com SVM
- 2️⃣ Treinar e classificar com ResNet
- 3️⃣ Classificar com Ensemble
- 4️⃣ Treinar todos os modelos
- 5️⃣ Ver resumo de modelos
- 6️⃣ Comparar resultados de todos
- 0️⃣ Sair

---

## Opção 2: Linha de Comando

### 🟢 Usar SVM (Rápido)

**Treinar:**
```bash
python svm_classifier.py
```

**Classificar:**
```bash
python classify_svm.py
```

**Resultado esperado:**
```
✅ imagem4.jpg: TAMPINHA (91% confiança)
❌ imagem6.jpg: NÃO É TAMPINHA (8% confiança)
... (6 imagens totais)
```

---

### 🔵 Usar ResNet (Melhor Acurácia)

**Treinar** (leva ~3-5 minutos):
```bash
python resnet_classifier.py
```

**Classificar:**
```bash
python classify_resnet.py
```

---

### 🟣 Usar Ensemble (Melhor Robustez)

**Pré-requisito:** SVM e ResNet devem estar treinados

**Classificar:**
```bash
python ensemble_classifier.py
```

---

## Modelos Disponíveis

### 🟢 SVM com RBF Kernel

| Aspecto | Detalhes |
|---------|----------|
| **Localização** | `svm_classifier.py` |
| **Pasta do modelo** | `models/svm/` |
| **Tempo treino** | <1 segundo |
| **GPU requerida** | Não |
| **Acurácia treino** | 100% |
| **Acurácia real** | 1/6 (16.7%) - baixa generalização |
| **Features** | 24 (cor, forma, textura) |
| **Data augmentation** | 50 variações por tampinha |

**Quando usar:**
- ✅ Testes rápidos
- ✅ Sem GPU disponível
- ❌ Quando precisa de alta acurácia em casos novos

---

### 🔵 ResNet50 Transfer Learning

| Aspecto | Detalhes |
|---------|----------|
| **Localização** | `resnet_classifier.py` |
| **Pasta do modelo** | `models/resnet/` |
| **Tempo treino** | ~3-5 minutos |
| **GPU requerida** | Recomendada (funciona em CPU) |
| **Acurácia treino** | (será calculada) |
| **Features** | Aprendidas automaticamente |
| **Data augmentation** | Avançado (rotações, zoom, iluminação) |
| **Pré-treino** | ImageNet (1M+ imagens) |

**Quando usar:**
- ✅ Quando se importa com generalização
- ✅ Imagens com variações de iluminação/ângulo
- ✅ Dataset pequeno (transfer learning!)

---

### 🟣 Ensemble (SVM + ResNet)

| Aspecto | Detalhes |
|---------|----------|
| **Localização** | `ensemble_classifier.py` |
| **Estratégia** | Voting com pesos |
| **SVM peso** | 40% |
| **ResNet peso** | 60% |
| **Pré-requisito** | Ambos modelos treinados |

**Quando usar:**
- ✅ Máxima robustez
- ✅ Quando ambos os modelos estão disponíveis
- ✅ Quando quer combinar forças

---

## 🧪 Dataset

### Estrutura

```
datasets/
├── tampinhas/           (4 imagens)
│   ├── 585589810838234 (1).jpg
│   ├── tampinhas-plasticas.jpg
│   ├── tampinhas-plasticas_1747253804987.jpg
│   └── TP-PET.webp
│
├── nao-tampinhas/       (14 imagens)
│   ├── 37e316472b3e63a6a1307804e40ec77265e61c571818f.jpg
│   ├── 72154-fv-cerveja-300-std-ab-stp_optimized-300x300.jpg
│   ├── ... (garrafas, latas, frutas, baterias, papel)
│   └── Papel-higienico-300-metros.png
│
└── color-cap/           (2100 imagens - não usado no SVM/ResNet)
```

### Dados de Treino

- **Tampinhas**: 4 reais + 200 variações sintéticas = ~200 amostras
- **Não-tampinhas**: 14 reais + 420 variações sintéticas = ~430 amostras
- **Total**: ~630 amostras

---

## 📊 Comparação Rápida

```
╔═════════════╦═══════════╦══════════╦═════════╗
║   Métrica   ║    SVM    ║  ResNet  ║Ensemble ║
╠═════════════╬═══════════╬══════════╬═════════╣
║  Status     ║ ✅ Pronto │ 🔄 Dev   ║ ⏳ Dev  ║
║  Velocidade ║ ⭐⭐⭐⭐⭐ │ ⭐⭐⭐   ║ ⭐⭐⭐   ║
║ Acurácia    ║ ⭐⭐⭐   │ ⭐⭐⭐⭐⭐ ║ ⭐⭐⭐⭐⭐ ║
║   GPU       ║    Não    │  Recomendado │ Recomendado ║
╚═════════════╩═══════════╩══════════╩═════════╝
```

---

## 🔧 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'tensorflow'"

**Solução:**
```bash
pip install tensorflow
```

### ❌ "SVM Model not found"

**Solução:**
```bash
# Treinar primeiro
python svm_classifier.py

# Depois classificar
python classify_svm.py
```

### ❌ "CUDA out of memory" (ResNet)

**Solução 1:** Usar CPU (mais lento)
```bash
# Já funciona automaticamente, só leva mais tempo
```

**Solução 2:** Reduzir batch size no código

### ❌ "No images found in /images/"

**Verificar:**
- Pasta `images/` existe?
- Arquivos `.jpg` estão lá?
- Comando está sendo rodado no diretório correto?

---

## 📈 Próximos Passos

### Fase 1: Teste rápido
```bash
python main.py
# Escolha opção 1 (SVM)
```

### Fase 2: Teste completo
```bash
python main.py
# Escolha opção 4 (Treinar todos)
# Depois opção 6 (Comparar)
```

### Fase 3: Deploy
```bash
# Escolher melhor modelo
# Integrar com app_flask.py ou esp32
```

---

## 💡 Dicas

1. **Primeiro teste:** Use SVM (< 1 segundo)
2. **Comparação:** Use `main.py > opção 6`
3. **Melhor resultado:** ResNet ou Ensemble
4. **Produção:** Ensemble (mais robusto)

---

## 📝 Logs e Resultados

Cada modelo gera logs detalhados com:
- ✅ Carregamento do dataset
- ✅ Acurácia de treino
- ✅ Validação cruzada
- ✅ Métricas por classe
- ✅ Confiança de predição

Exemplo de saída:
```
🟢 SVM CLASSIFIER - CLASSIFICAÇÃO DE TAMPINHAS
======================================================================
Tampinhas reais: 100%|█████| 4/4 [00:00<00:00, 72.39it/s]
Gerando variações sintéticas de tampinhas...
Dataset final: 98 amostras, 24 features
  Tampinhas: 54, Não-tampinhas: 44
Acurácia CV: 1.000 (+/- 0.000)
ROC-AUC Score: 1.000
✅ Modelo salvo em: models/svm/svm_model.pkl
```

---

**Quer começar?** Execute:
```bash
python main.py
```

**Dúvidas?** Veja `MODELOS.md` ou `RESUMO_MODELOS.md`
