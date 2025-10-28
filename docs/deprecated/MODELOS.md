# 🎯 Modelos de Classificação de Tampinhas

Projeto organizado com múltiplos modelos de Machine Learning para classificação de tampinhas (plásticas) vs não-tampinhas.

## 📁 Estrutura do Projeto

```
totem-ia/
├── models/
│   ├── svm/                 # 🟢 Modelo SVM (RBF Kernel) - ATIVO
│   │   ├── svm_model.pkl
│   │   └── scaler.pkl
│   ├── resnet/              # 🔵 Transfer Learning (ResNet50) - EM DESENVOLVIMENTO
│   └── ensemble/            # 🟣 Ensemble (SVM + ResNet) - EM DESENVOLVIMENTO
├── datasets/
│   ├── tampinhas/           # 4 imagens de tampinhas reais
│   ├── nao-tampinhas/       # 14 imagens de não-tampinhas
│   └── color-cap/           # Dataset adicional
├── images/                  # 6 imagens de teste
├── svm_classifier.py        # 🟢 Modelo SVM
├── classify_svm.py          # 🟢 Classificador SVM
├── resnet_classifier.py     # 🔵 Modelo ResNet (em breve)
├── ensemble_classifier.py   # 🟣 Ensemble (em breve)
└── README.md
```

## 🟢 Modelo 1: SVM com RBF Kernel

### Características
- ✅ **RBF Kernel**: Ideal para dados não-lineares
- ✅ **Balanceamento**: Class weight balanceado para dataset desigual
- ✅ **Data Augmentation**: 50 variações por tampinha + 30 por não-tampinha
- ✅ **Validação Cruzada**: 5-Fold para dataset pequeno
- ✅ **Features**: 24 features (cor, forma, textura)
- ✅ **Rápido**: Treina em segundos
- ✅ **Sem GPU**: Roda em CPU

### Como Usar

**1. Treinar o Modelo**
```bash
python svm_classifier.py
```

**2. Classificar Imagens**
```bash
python classify_svm.py
```

**3. Saída Esperada**
```
✅ TAMPINHA (confiança: 0.95)
❌ NÃO É TAMPINHA (confiança: 0.15)
```

## 🔵 Modelo 2: ResNet50 (Transfer Learning)

*Em desenvolvimento - Melhor generalização*

### Características
- Transfer Learning do ImageNet
- Fine-tuning de últimas camadas
- Data Augmentation avançado
- Requer TensorFlow/Keras

### Como Usar (em breve)
```bash
python resnet_classifier.py
python classify_resnet.py
```

## 🟣 Modelo 3: Ensemble (SVM + ResNet)

*Em desenvolvimento - Máxima robustez*

### Características
- Combina SVM (30%) + ResNet (70%)
- Voting para melhor decisão
- Mais confiável que modelos individuais

### Como Usar (em breve)
```bash
python ensemble_classifier.py
python classify_ensemble.py
```

## 📊 Comparação de Modelos

| Aspecto | SVM | ResNet | Ensemble |
|---------|-----|--------|----------|
| Acurácia | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Velocidade | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| GPU Requerida | Não | Sim | Sim |
| Tempo Treino | <1s | ~30s | ~40s |
| Dataset Pequeno | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🧪 Dataset

### Tampinhas (Positivas)
- 4 imagens reais verificadas
- 50 variações sintéticas por imagem
- **Total**: ~200 amostras de treino

### Não-Tampinhas (Negativas)
- 14 imagens variadas (garrafas, latas, frutas, baterias, etc.)
- 30 variações sintéticas por imagem
- **Total**: ~434 amostras de treino

## 🎯 Objetivo

Classificar corretamente imagens de tampinhas plásticas vs outros objetos com confiança > 90%.

## 🔧 Requisitos

```bash
pip install scikit-learn opencv-python numpy joblib matplotlib
# Para ResNet: pip install tensorflow
```

## 📝 Logs

Os modelos geram logs detalhados com:
- Carregamento do dataset
- Informações de treinamento
- Validação cruzada
- Métricas de avaliação
- Tempo de execução

---

**Status**: 🟢 SVM em produção | 🔵 ResNet em desenvolvimento | 🟣 Ensemble em planejamento
