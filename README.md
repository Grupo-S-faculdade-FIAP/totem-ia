# 🎨 Totem Inteligente de Reciclagem - Análise de Tampinhas Plásticas

> Solução de IA para classificação de tampinhas plásticas usando Vision Transformer (ViT) fine-tuned

## 📋 Visão Geral

Este projeto implementa um **totem inteligente de reciclagem** que classifica **tampinhas plásticas por cor** usando deep learning. A solução utiliza um Vision Transformer pré-treinado no ImageNet, fine-tunado com um dataset robusto de 2.400 imagens de tampinhas em diferentes cores.

### 🎯 Objetivo Principal
Classificar tampinhas plásticas com base em sua cor, facilitando a separação automática em processos de reciclagem.

### 🎨 Classes Suportadas (12 cores)
```
0 → Vermelho      1 → Azul          2 → Verde       3 → Amarelo
4 → Branco        5 → Preto         6 → Laranja     7 → Rosa
8 → Roxo          9 → Marrom        10 → Cinza      11 → Transparente
```

---

## 📊 Dataset

**Origem**: Kaggle - `color-cap` dataset
- **Total**: 2.400 imagens
- **Treino**: 2.100 imagens
- **Validação**: 200 imagens
- **Teste**: 100 imagens
- **Formato**: YOLO (object detection)
- **Tamanho médio**: 1920×1080 px
- **Localização**: `datasets/color-cap/`

### Distribuição de Classes
Todas as 12 cores estão representadas no dataset com distribuição balanceada.

---

## 🚀 Quickstart

### 1. Instalação

```bash
# Clonar/navegar para o repositório
cd totem-ia

# Criar ambiente virtual (se necessário)
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Explorar o Dataset

```bash
python explore_dataset.py
```

Isto irá:
- ✓ Analisar estrutura do dataset
- ✓ Validar integridade das imagens
- ✓ Gerar mapeamento de classes
- ✓ Exibir estatísticas

### 3. Fine-tuning do Modelo

```bash
python finetune_caps.py
```

**Configurações padrão:**
- Modelo base: `google/vit-base-patch16-224`
- Épocas: 15
- Batch size: 32
- Learning rate: 1e-4
- Otimizador: AdamW + Linear Scheduler
- Salva em: `models/cap-finetuned/`

**Tempo estimado**: 30-60 minutos (GPU) ou 2-3 horas (CPU)

### 4. Usar o Classificador

```python
from backend.cap_classifier import CapClassifier

# Inicializar com modelo pré-treinado
classifier = CapClassifier(model_path="models/cap-finetuned")

# Classificar uma imagem
result = classifier.classify_image("path/to/tampinha.jpg")
print(result)

# Classificar múltiplas imagens
results = classifier.classify_batch([
    "path/to/cap1.jpg",
    "path/to/cap2.jpg"
])

# Avaliar dataset
stats = classifier.evaluate_dataset("datasets/color-cap/test/images")
```

---

## 📁 Estrutura do Projeto

```
totem-ia/
├── backend/
│   ├── cap_classifier.py         ✅ Classificador de tampinhas
│   ├── ai_models.py              📊 Modelos de IA
│   ├── database.py               💾 Gerenciamento de BD
│   ├── gamification.py           🎮 Sistema de gamificação
│   ├── image_analyzer.py         🖼️  Análise de imagens
│   ├── main.py                   🔌 Lógica principal
│   ├── models.py                 📋 Modelos de dados
│   └── vit_classifier.py         🤖 Classificador ViT genérico
│
├── datasets/
│   └── color-cap/                🎨 Dataset do Kaggle
│       ├── train/
│       │   ├── images/           (2100 imagens)
│       │   └── labels/           (2100 labels YOLO)
│       ├── valid/
│       │   ├── images/           (200 imagens)
│       │   └── labels/           (200 labels)
│       └── test/
│           ├── images/           (100 imagens)
│           └── labels/           (100 labels)
│
├── models/
│   └── cap-finetuned/            🤖 Modelo fine-tuned (após treino)
│       ├── config.json
│       ├── model.safetensors
│       ├── classes.json
│       └── training_history.json
│
├── esp32/                         🔧 Código ESP32
├── images/                        📷 Imagens do projeto
│
├── finetune_caps.py              📚 Script de fine-tuning
├── explore_dataset.py             🔍 Análise do dataset
├── run_totem.py                   🚀 Iniciar aplicação
├── vit_api_server.py              🌐 Servidor API
├── requirements.txt               📦 Dependências
├── .env                          🔐 Configurações locais
└── README.md                      📖 Este arquivo

```

---

## 🛠️ Ferramentas Utilizadas

### Deep Learning
- **Transformers**: `google/vit-base-patch16-224` (224×224 px)
- **Framework**: PyTorch 2.0+
- **Fine-tuning**: Hugging Face Transformers

### Processamento
- **Visão Computacional**: OpenCV, PIL/Pillow
- **Processamento de Imagens**: CUDA (GPU) / CPU

### Banco de Dados
- **SQLite**: `recycling_totem.db`
- **ORM**: SQLAlchemy (se configurado)

### API & Servidor
- **FastAPI** ou **Flask** para exposição de endpoints

---

## 📊 Desempenho Esperado

| Métrica | Esperado |
|---------|----------|
| Acurácia (validação) | 85-95% |
| Acurácia (teste) | 80-90% |
| Confiança média | 70-85% |
| Tempo/imagem | 50-100ms (GPU) |

---

## 🎯 Fluxo de Uso

```
Imagem Tampinha
       ↓
[CapClassifier]
       ↓
[ViT Fine-tuned]
       ↓
Classificação + Confiança
       ↓
[Banco de Dados]
       ↓
[Totem - Feedback ao Usuário]
```

---

## 🔧 Configuração Avançada

### Alterar Tamanho de Batch

Editar `finetune_caps.py`:
```python
train_loader = DataLoader(train_dataset, batch_size=64, ...)  # Aumentar para GPU com mais RAM
```

### Ajustar Taxa de Aprendizado

```python
history = finetuner.train(
    learning_rate=2e-4,  # Aumentar para convergência mais rápida
    num_epochs=20        # Mais épocas para melhor generalização
)
```

### Usar CPU ao invés de GPU

```python
classifier = CapClassifier(device='cpu')
```

---

## 🐛 Troubleshooting

### "CUDA out of memory"
- Reduzir `batch_size` para 16 ou 8
- Usar `device='cpu'`
- Liberar cache: `torch.cuda.empty_cache()`

### "Dataset not found"
- Verificar se `datasets/color-cap/` existe
- Executar `explore_dataset.py` para validar

### "Modelo não classifica corretamente"
- Treinar novamente com `finetune_caps.py`
- Aumentar número de épocas (até 20-30)
- Reduzir `learning_rate` para 5e-5

---

## 📈 Próximos Passos

- [ ] Integração com câmera do totem
- [ ] API REST completa
- [ ] Dashboard de monitoramento
- [ ] Análise de confiança em tempo real
- [ ] Gamificação com feedback do usuário
- [ ] Detecção de tampinhas múltiplas (YOLO v8)

---

## 📝 Referências

- [Vision Transformer (ViT) Paper](https://arxiv.org/abs/2010.11929)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Kaggle color-cap Dataset](https://www.kaggle.com/datasets/your-dataset-link)

---

## 📄 Licença

Este projeto está sob licença [MIT/GPL - especificar].

## 👥 Autores

- **Carol** - Desenvolvedor
- **FIAP** - Instituto de Educação

---

## 📞 Suporte

Para dúvidas ou issues, abrir uma issue no repositório ou contatar os responsáveis.

---

**Última atualização**: Outubro 2025
**Status**: ✅ Em desenvolvimento
