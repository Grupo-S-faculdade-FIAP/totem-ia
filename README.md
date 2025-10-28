# Totem IA - Sistema de Classificação de Tampinhas

Sistema inteligente de classificação e validação de tampinhas de plástico para reciclagem, usando visão computacional e machine learning.

## ⚠️ **Status Atual: Modelo Necessita Retreinamento**

**IMPORTANTE**: O modelo atual foi treinado com dados inadequados e apresenta classificações incorretas. É necessário retreinar com dados apropriados antes do uso em produção.

### 🎯 **Problema Identificado**
- Modelo treinado assumindo que TODAS as imagens dos datasets são tampinhas positivas
- Dados de treinamento não representam adequadamente tampinhas vs não-tampinhas
- Classificações atuais refletem dados de treinamento inadequados, não a realidade

## Características

- **Ensemble Learning**: Modelo ensemble com Random Forest + Extra Trees
- **Features Avançadas**: 24 features otimizadas (RGB/HSV + forma + textura)
- **API REST**: Flask para integração com sistemas externos
- **ESP32 Ready**: Suporte para dispositivos embarcados

## Arquitetura

```
Camera → Ensemble Model: É tampinha? → Elegível para reciclagem?
         (RF + Extra Trees)              (Sim/Não)
```

## 🚨 **Atenção: Dados de Treinamento**

### ❌ **Problema Atual**
- **Dataset color-cap**: 2100 imagens tratadas como "tampinhas positivas"
- **Amostras negativas**: Criadas sinteticamente (não realistas)
- **Resultado**: Modelo aprende padrões incorretos

### ✅ **Solução Necessária**
Para corrigir, precisamos de:
1. **Imagens reais verificadas de tampinhas** (positivas verdadeiras)
2. **Imagens reais verificadas de NÃO-tampinhas** (objetos diferentes)
3. **Retreinamento** com dados adequados

## Estrutura do Projeto

```
totem-ia/
├── models/
│   ├── enhanced-fast-classifier/    # ⭐ Ensemble: RF + Extra Trees + Calibração (recomendado)
│   │   ├── fast_cap_classifier.pkl
│   │   ├── scaler.pkl
│   │   └── feature_selector.pkl
│   └── vit-cap-finetuned/          # Vision Transformer (experimental)
│       ├── model.safetensors
│       ├── config.json
│       └── ...
│
├── datasets/                        # Dados de treinamento
│   ├── color-cap/                   # Dataset principal (2100 imagens - ⚠️ dados inadequados)
│   └── tampinhas/                   # Dataset adicional (3 imagens reais)
├── images/                          # Imagens para teste
├── esp32/                           # Código para ESP32
├── backend/                         # Código do backend
│
├── evaluate_eligibility_fast.py    # ⚠️ Modelo com dados inadequados (necessita retreinamento)
├── classify_all_images.py          # Classificação completa das imagens
│
├── app_flask.py                    # API REST principal
├── run_api.py                      # Executa API
│
├── analyze_both_models.py          # Compara Ensemble vs ViT
├── compare_models.py               # Análise comparativa de modelos
├── run_benchmark.py                # Benchmark de performance
├── test_api.py                     # Testes da API
│
├── requirements.txt                # Dependências Python
└── .gitignore
```

## Instalação

### 1. Clonar repositório
```bash
git clone <seu-repo>
cd totem-ia
```

### 2. Criar ambiente virtual
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

## � **Como Usar (Status Atual)**

### ⚠️ **Atenção: Modelo com Problemas**
O modelo atual foi treinado com dados inadequados e produz classificações incorretas.

### Classificar Imagens Existentes
```bash
python classify_all_images.py
```
**Resultado atual (INCORRETO):**
```
✅ Tampinhas detectadas: 5
❌ Não são tampinhas: 1
🎉 MAIORIA DAS IMAGENS SÃO TAMPINHAS!
```

**Por que está incorreto:**
- Modelo treinado assumindo que todas as imagens de treinamento são tampinhas
- Não representa a realidade das tampinhas vs não-tampinhas

### 🔧 **Para Corrigir o Modelo:**

1. **Coletar dados adequados:**
   - Imagens reais verificadas de tampinhas (positivas)
   - Imagens reais verificadas de NÃO-tampinhas (negativas)

2. **Retreinar o modelo:**
   ```bash
   # Modificar evaluate_eligibility_fast.py para usar dados corretos
   python evaluate_eligibility_fast.py
   ```

3. **Validar resultados:**
   ```bash
   python classify_all_images.py
   ```

### API REST (Não usar até correção)
```bash
python run_api.py
```
**Status:** Funcional mas com classificações incorretas
```bash
python run_api.py
```
**Endpoint:** `POST /classify`
```json
{
  "image_path": "images/imagem1.jpg"
}
```

**Resposta:**
```json
{
  "is_cap": true,
  "confidence": 0.724,
  "model": "enhanced-ensemble"
}
```

## Uso Rápido

### Classificar uma imagem (Random Forest Rápido)
```python
from evaluate_eligibility_fast import FastCapClassifier

classifier = FastCapClassifier()
is_cap, confidence = classifier.predict_single("images/tampinha.jpg")

print(f"É tampinha? {is_cap} (Confiança: {confidence:.3f})")
# Output: É tampinha? True (Confiança: 1.000)
```

### Executar API REST
```bash
python run_api.py
```

A API estará disponível em `http://localhost:5000`

#### Endpoints principais:
- `POST /classify` - Classifica uma imagem
- `GET /health` - Status da API

## Modelos Disponíveis

### Random Forest Rápido (Recomendado) ⚡⭐
- **Acurácia**: 100% (validação cruzada) / 100% (teste)
- **Velocidade**: Treinamento em 0.47s / Inferência instantânea
- **Dataset**: 2100 imagens reais + 500 sintéticas
- **Features**: 24 features otimizadas
- **Tamanho**: ~2 MB (compacto)
- **Latência**: ~50 ms por imagem
- **Tipo**: Binário otimizado (cap vs non-cap)
- **Status**: ✅ Pronto para produção - mais rápido e preciso!

### Vision Transformer (ViT) 🧠
- **Arquitetura**: Baseado em transformers de visão
- **Dataset**: Treinado com dados de tampinhas
- **Status**: 🧪 Experimental - para comparação avançada

## Treinamento

### Treinar Random Forest (Recomendado) ⚡
```bash
python evaluate_eligibility_fast.py
```
- **Dataset**: Usa dados reais do `datasets/color-cap/`
- **Tempo**: ~2-3 minutos
- **Resultado**: Modelo binário otimizado salvo em `models/fast-cap-classifier/`

### Treinar Vision Transformer (ViT) 🧠
```bash
# Script em desenvolvimento
# Baseado em transformers de visão para comparação avançada
```

## Análise de Modelos

### Comparar RF vs ViT
```bash
python analyze_both_models.py
```

Gera `ANALISE_COMPARATIVA.json` com métricas detalhadas.

## Performance

| Modelo | Acurácia | Tamanho | Latência | Tampinhas Reais |
|--------|----------|---------|----------|-----------------|
| **Random Forest Híbrido** | 98.1% | 5 MB | 123 ms | **100%** ✅ |
| Random Forest Realista | 99.7% | 5 MB | 123 ms | 0% ❌ |
| Vision Transformer | 0% | 327 MB | 3478 ms | 0% ❌ |

**Conclusão**: Random Forest Híbrido é o campeão absoluto!

## Recursos da API

### Classificar imagem
```bash
curl -X POST http://localhost:5000/classify \
  -F "image=@images/tampinha.jpg"
```

### Verificar saúde
```bash
curl http://localhost:5000/health
```

## ESP32

Veja `esp32/` para código embarcado e instruções de deployment.

## Dependências Principais

- **scikit-learn**: Machine Learning (Random Forest)
- **OpenCV (cv2)**: Processamento de imagens
- **NumPy**: Operações numéricas
- **Flask**: API REST
- **Pillow**: Manipulação de imagens
- **transformers**: Vision Transformer

## Troubleshooting

### Erro de modelo não encontrado
```
FileNotFoundError: models/binary-cap-detector/binary_classifier.pkl
```
Solução: Execute `python train_binary_classifier.py` para treinar.

### Imagens rejeitadas como "não-tampinha"
- **Sintomas**: Modelo rejeita imagens que são claramente tampinhas
- **Causa**: Modelo treinado com dados sintéticos vs fotos reais
- **Solução**: Use o modelo híbrido (`binary-cap-detector-hybrid/`)
- **Verificação**: Execute `python test_hybrid_model.py` para testar

### Erro de encoding (Windows)
- Já está tratado com UTF-8
- Se persistir, execute em cmd.exe em vez de PowerShell

## Próximos Passos

- [ ] Coletar dataset real de tampinhas
- [ ] Retrainear modelos com dados reais
- [ ] Integrar com hardware ESP32
- [ ] Deploy em produção
- [ ] Monitoramento de performance em campo

## Licença

FIAP - Desafio Totem IA

## Autor

Desenvolvido como parte do desafio FIAP de Totem Inteligente.
