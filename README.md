# TOTEM IA - Sistema de Depósito Inteligente de Tampinhas

Link apresentação: https://youtu.be/LTQljfnJWdM

## 🎯 Challenge FlexMedia - FIAP

**Turma:** Desenvolvimento de Soluções IoT com IA  
**Grupo:** Grupo-S-faculdade-FIAP  
**Sprint:** 1 - Proposta Técnica e Arquitetura Inicial MVP


## 👥 *Integrantes do Grupo*
•⁠  ⁠*Caroline Correa*
•⁠  ⁠*Tiago Lindgren*
•⁠  ⁠*Marcelo Mizuta*
•⁠  ⁠*Gabriel Marques*
•⁠  ⁠*Vinicius Vinha*

---

## 📋 Contexto do Projeto

### Challenge FlexMedia

Este projeto é uma resposta ao desafio proposto pela **FlexMedia**, empresa especializada em soluções digitais inovadoras para experiências interativas em espaços culturais, de lazer e comerciais. O objetivo é desenvolver um **totem inteligente com IA** capaz de integrar diferentes tecnologias, promover personalização e enriquecer a interação dos usuários.

### Visão da FlexMedia

A FlexMedia busca transformar espaços físicos em ambientes inteligentes, aproximando tecnologia e experiência do usuário através de:

- **Soluções acessíveis e interativas** em ambientes culturais e comerciais
- **Personalização de experiências** para diferentes perfis de usuários
- **Coleta e análise de dados** em tempo real para medir engajamento
- **Integração de tecnologias diversas** (sensores, câmeras, IoT, dashboards)
- **Segurança e privacidade** de dados em todas as etapas
- **Apoio à tomada de decisão** por meio da Inteligência Artificial

### Nossa Proposta: TOTEM IA

Desenvolvemos uma solução inovadora de **totem inteligente para depósito de tampinhas** que combina:

- **Inteligência Artificial** para classificação automática de tampinhas
- **Interface touch-friendly** para interação intuitiva
- **Análise ambiental** com cálculo de impacto sustentável
- **Integração multissensorial** (câmera, display, áudio)
- **Dashboard em nuvem** para análise de dados

> 📖 **Leia nossa história completa**: [STORYTELLING.md](STORYTELLING.md) - A jornada de inovação sustentável do TOTEM IA

---

## 🎯 Objetivos da Sprint 1

### Objetivos Principais

1. **Definir integração do totem ao ambiente**
   - Sensores de presença e toque
   - Câmera para captura de imagens
   - Display interativo e alto-falantes

2. **Identificar dados coletados e análise**
   - Perfil do usuário (idade estimada, gênero)
   - Métricas de engajamento (tempo de interação, satisfação)
   - Dados ambientais (quantidade de tampinhas, impacto sustentável)

3. **Estruturar arquitetura técnica**
   - Hardware: ESP32-S3-CAM + touchscreen
   - Software: Flask + OpenCV + Scikit-learn
   - Nuvem: Render para deployment

4. **Garantir segurança e privacidade**
   - Processamento local de imagens
   - Dados anonimizados
   - Conformidade com LGPD

5. **Plano de desenvolvimento**
   - Metodologia ágil (sprints)
   - Divisão de responsabilidades
   - Versionamento com Git

---

## 🏗️ Arquitetura da Solução

### Arquitetura Geral

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interface     │    │   Backend       │    │   Dashboard     │
│   Touchscreen   │◄──►│   Flask API     │◄──►│   Analytics     │
│   (Frontend)    │    │   (Python)      │    │   (Web)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sensores      │    │   IA/ML Model   │    │   Database      │
│   (Hardware)    │    │   (SVM)         │    │   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Diagrama de Arquitetura (PlantUML)

![Diagrama de Componentes do Totem IA](assets/Flexmedia_Diag.png)

<!-- ### Diagrama de Arquitetura (PlantUML)

O projeto inclui um **diagrama completo de componentes** criado em PlantUML (`totem_ia_diagram.puml`) que detalha:

- **Pacotes do Sistema**: Frontend, Backend, IA, Dados e Infraestrutura
- **Componentes**: Interfaces, APIs, modelos de ML, bancos de dados
- **Conexões**: Fluxos de dados e integrações entre componentes
- **Componentes Planejados**: ESP32-S3-CAM marcado como não implementado
- **Notas Explicativas**: Detalhes sobre funcionalidades e status de implementação

**Como visualizar o diagrama:**
```bash
# Instalar PlantUML
brew install plantuml

# Gerar diagrama PNG
plantuml totem_ia_diagram.puml

# Ou usar extensão PlantUML no VS Code
``` -->

### Pipeline de Dados

1. **Captura**: Usuário interage com touchscreen
2. **Aquisição**: Câmera captura imagem da tampinha
3. **Processamento**: OpenCV extrai features da imagem
4. **Classificação**: Modelo SVM classifica (tampinha vs não-tampinha)
5. **Feedback**: Interface mostra resultado + impacto ambiental
6. **Armazenamento**: Dados salvos localmente e enviados para nuvem

### Tecnologias Utilizadas

#### Hardware
- **Computador Principal**: ESP32-S3-CAM (com câmera integrada)
- **Câmera**: Integrada no ESP32-S3-CAM
- **ESP32-S3-CAM**: Módulo câmera WiFi (planejado, não implementado)
- **Display**: Touchscreen 7-10 polegadas
- **Sensores**: PIR (presença), botões capacitivos
- **Áudio**: Alto-falantes integrados

#### Software
- **Backend**: Python 3.12 + Flask
- **Visão Computacional**: OpenCV 4.8+
- **Machine Learning**: Scikit-learn (SVM)
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Database**: SQLite (local) + PostgreSQL (nuvem)
- **Deployment**: Render (PaaS)
- **Diagramas**: PlantUML 1.2025+

#### Inteligência Artificial
- **Modelo**: Support Vector Machine (SVM) com kernel RBF
- **Features**: 24 características (cores, texturas, formas)
- **Dataset**: 4.430 imagens (2.215 tampinhas + 2.215 não-tampinhas)
- **Acurácia**: 100% em treino e validação

#### Serviços em Nuvem
- **Hosting**: Render (Python web service)
- **URL**: https://totem-ia.onrender.com/
- **Analytics**: Dashboard personalizado
- **Backup**: Dados sincronizados automaticamente

### Componentes Planejados (Não Implementados)

#### ESP32-S3-CAM
- **Descrição**: Módulo câmera WiFi com processador ESP32-S3 para captura independente de imagens
- **Objetivo**: Permitir captura remota e processamento distribuído
- **Integração Planejada**: Comunicação MQTT com sistema principal
- **Status**: Especificado na arquitetura, implementação pendente para próximas sprints

---

## 🔒 Segurança e Privacidade

### Estratégias Implementadas

1. **Processamento Local**
   - Imagens processadas no dispositivo
   - Dados não enviados para servidores externos
   - Privacidade garantida

2. **Anonimização de Dados**
   - Não coleta dados pessoais
   - Métricas agregadas apenas
   - Conformidade com LGPD

3. **Segurança de Rede**
   - Comunicação HTTPS
   - Autenticação de API
   - Logs de auditoria

4. **Proteção Física**
   - Case resistente a vandalismo
   - Sistema de travamento
   - Monitoramento remoto

---

## 📊 Coleta e Análise de Dados

### Dados Coletados

#### Dados Ambientais
- Quantidade de tampinhas depositadas
- Tipos de materiais reciclados
- Impacto sustentável calculado

#### Dados de Usuário
- Tempo de interação
- Taxa de sucesso na classificação
- Preferências de interface

#### Dados Técnicos
- Uptime do sistema
- Taxa de erro do modelo
- Performance de hardware

### Análise em Tempo Real

- **Dashboard Local**: Interface administrativa
- **Dashboard Nuvem**: Analytics avançados
- **Relatórios**: Métricas diárias/semanais
- **Alertas**: Manutenção preventiva

---

## 🚀 Plano de Desenvolvimento

### Metodologia
- **Framework**: Scrum adaptado para academia
- **Sprints**: 2 semanas cada
- **Ferramentas**: GitHub Projects, Discord

### Divisão de Responsabilidades

#### Caroline (Líder Técnico)
- Desenvolvimento backend (Flask API)
- Integração de IA/ML
- Deployment e infraestrutura

#### Equipe de Desenvolvimento
- **Frontend**: Interface touchscreen responsiva
- **Hardware**: Integração com sensores
- **Database**: Modelagem e otimização
- **Testing**: QA e validação

### Cronograma Previsto

#### Sprint 1 (Atual) ✅
- [x] Definição de arquitetura
- [x] Prototipagem do modelo IA
- [x] Interface básica
- [x] Documentação inicial

#### Sprint 2 (Próxima)
- [ ] Integração hardware
- [ ] Otimização do modelo
- [ ] Dashboard analytics
- [ ] Testes de usabilidade

#### Sprint 3 (Final)
- [ ] Deployment produção
- [ ] Testes de stress
- [ ] Documentação completa
- [ ] Apresentação final

---

## 🔌 Integração ESP32 - Validação Mecânica

### Visão Geral
O sistema implementa integração bidirecional com API ESP32 para validação mecânica de tampinhas. A arquitetura segue um fluxo de 3 etapas com autenticação JWT:

```
User (Browser)
     ↓
TOTEM IA (Local - Port 8000)
     ↓
Loading Screen (3 etapas com animações)
     ↓
/api/validate-complete
     ├── SVM Classification (Software)
     └── ESP32 Server (Validação Mecânica via JWT)
          ├── /api/sensors (Leitura presença/peso)
          ├── /api/check_mechanical (Validação)
          └── /api/confirm_detection (Confirmação)
     ↓
Result Display (Success/Reject)
```

### Configuração

#### Variáveis de Ambiente (.env)
```bash
# ESP32 Configuration
ESP32_API_URL=https://esp32-totem-server.onrender.com  # Ou localhost:5001
ESP32_DEVICE_KEY=xxxxxxxxx                             # Device ID para JWT
JWT_SECRET=xxxxxxxxx                                    # Secret compartilhado

# Para desenvolvimento local
ESP32_API_URL=http://localhost:5001
```

### Backend - Novas Funções (app.py)

#### 1. `get_esp32_jwt_token()`
Gerencia tokens JWT com caching e validação de expiração:
```python
- Obtém token na primeira chamada
- Cache automático (válido por 24h)
- Refresh automático quando expirado
- Tratamento de erros com fallback
```

#### 2. `call_esp32_api(endpoint, method='GET', data=None)`
Wrapper genérico para todas as chamadas ESP32:
```python
- Autenticação Bearer Token
- Tratamento de timeouts
- Logging detalhado
- Retry automático em falhas
```

#### 3. `get_esp32_sensors()`
Lê sensores do ESP32:
```python
GET /api/sensors
Response: {
  "presenca": bool,
  "peso": int,
  "temperatura": float,
  "timestamp": str
}
```

#### 4. `check_esp32_mechanical(presenca, peso)`
Valida condições mecânicas:
```python
POST /api/check_mechanical
Data: {"presenca": bool, "peso": int}
Response: {"message": str, "timestamp": str}
```

#### 5. `confirm_esp32_detection(detection_type, confidence)`
Confirma detecção com confiança:
```python
POST /api/confirm_detection
Data: {"detection_type": "tampinha", "confidence": 0.95}
Response: {"status": "confirmed", "detection_type": str, "confidence": float}
```

### Novos Endpoints

#### POST /api/validate-complete
Endpoint principal que integra classificação + validação mecânica:
```python
Request: multipart/form-data
  file: image (PNG/JPG)
  
Response: {
  "classification": {
    "result": "tampinha" | "rejected",
    "confidence": float,
    "class": "tampinha" | "não-tampinha"
  },
  "mechanical": {
    "presenca": bool,
    "peso": int,
    "temperature": float,
    "valid": bool
  },
  "overall_result": "accepted" | "rejected"
}
```

#### GET /api/esp32-health
Health check da conexão ESP32:
```
Response: {
  "esp32_status": "online" | "offline",
  "jwt_token_valid": bool,
  "api_url": str,
  "last_check": timestamp
}
```

### Frontend - Loading Screen

#### HTML/CSS/JavaScript
- **Fullscreen Modal**: `display: fixed` com overlay 100%
- **Dual Spinner**: Animação dupla com rotações contrárias
- **3-Step Progress**: 📸 Classificação → ⚙️ Validação → ✓ Confirmação
- **Dynamic Messages**: Mensagens com fade in/out
- **Color Scheme**: Gradiente #667eea → #764ba2 (cores do projeto)

#### Animações CSS
```css
@keyframes spinValidation:
  - Duração: 2s forward, 1.5s reverse
  - FPS: 60fps
  - Suave com cubic-bezier

@keyframes fadeInOut:
  - Opacity: 0.7 → 1.0
  - Duração: variável por etapa
```

#### Eventos JavaScript
- `validateComplete()`: Orquestra todo fluxo
- `showValidationLoading()`: Exibe modal com spinner
- `updateValidationStep(step, message)`: Atualiza etapa
- `hideValidationLoading()`: Fecha modal

### Performance

| Métrica | Valor |
|---------|-------|
| Health Check | < 500ms |
| Classificação SVM | 1-2 segundos |
| Validação Mecânica | 1-2 segundos |
| Tempo Total | 3-4 segundos |
| Timeout API | 15 segundos |
| JWT Expiry | 24 horas |

### Segurança

#### Autenticação JWT
- Endpoint: `POST /api/auth/login`
- Credenciais: `device_id` + `device_key`
- Token Formato: `Bearer eyJhbGci...`
- Validação: Signature HMAC-SHA256 com `JWT_SECRET`

#### Proteção de Endpoints
- Todos endpoints ESP32 requerem Bearer Token
- Headers obrigatórios: `Authorization: Bearer <token>`
- Falha sem token: `401 Unauthorized`
- Falha com token inválido: `403 Forbidden`

#### Variáveis Sensíveis
- Nunca commitar `.env` com valores reais
- Usar `.env.example` como template
- Render: Configurar via dashboard UI (não em arquivo)

### Testes

#### Arquivo: `test_esp32_server.py`
Suite completa com 11 classes de testes:

```python
# Autenticação
TestAuthentication:
  - test_login_sucesso()
  - test_login_falha()
  - test_token_formato_valido()

# Health & Status
TestHealthStatus:
  - test_health_check()
  - test_status_sem_autenticacao()
  - test_status_com_autenticacao()

# Sensores
TestSensors:
  - test_sensors_sem_token()
  - test_sensors_com_token()

# Validação Mecânica
TestMechanical:
  - test_check_mechanical_sem_token()
  - test_check_mechanical_com_token()
  - test_check_mechanical_presenca_verdadeira()
  - test_check_mechanical_presenca_falsa()
  - test_check_mechanical_peso_vario()

# Detecção
TestDetection:
  - test_confirm_detection_sem_token()
  - test_confirm_detection_com_token()
  - test_confirm_detection_tipos()
  - test_confirm_detection_confiancas()

# Telemetria
TestTelemetry:
  - test_telemetry_sem_token()
  - test_telemetry_com_token()

# Estatísticas
TestStatistics:
  - test_statistics_sem_autenticacao()
  - test_statistics_contem_dados()

# WiFi Info
TestWiFiInfo:
  - test_wifi_info()

# Segurança
TestSecurity:
  - test_token_invalido_rejeitado()
  - test_bearer_obrigatorio()
  - test_sem_authorization_header()

# Performance
TestPerformance:
  - test_health_check_rapido()
  - test_sensors_rapido()
  - test_requests_em_serie()

# Integração
TestIntegration:
  - test_fluxo_completo()
```

#### Execução
```bash
pytest test_esp32_server.py -v              # Todos os testes
pytest test_esp32_server.py::TestAuthentication -v  # Uma classe
pytest test_esp32_server.py -v -s           # Com prints
```

#### Arquivo: `test_esp32_integration.py`
Testes de integração TOTEM IA ↔ ESP32:

```python
# Testa:
- Health check do TOTEM IA
- Classificação de imagens
- Validação completa (2 etapas)
- Endpoints protegidos com JWT
- Autenticação e segurança
- Performance (timing assertions)
- Fluxos end-to-end
```

### Deployment

#### Local (Desenvolvimento)
```bash
# Terminal 1: ESP32 Server
cd esp32-totem-server
python app.py
# http://localhost:5001

# Terminal 2: TOTEM IA
cd totem-ia
python app.py
# http://localhost:8000
```

#### Remote (Render)
```bash
# ESP32 Server
https://esp32-totem-server.onrender.com

# TOTEM IA
https://totem-ia.onrender.com

# Variáveis de ambiente no dashboard Render
```

---

## 🛠️ Como Executar o Projeto

### Pré-requisitos
```bash
# Python 3.13+
python --version

# Instalar dependências
pip install -r requirements.txt
```

### Execução Local
```bash
# Treinar modelo (opcional)
python src/models_trainers/svm_complete_classifier.py

# Iniciar servidor
python app.py

# Acessar: http://localhost:8000
```

### Deployment
```bash
# Render (automático via GitHub)
git push origin main

# Ou manual no dashboard Render
```

**URL de Produção**: https://totem-ia.onrender.com/

### Testes
```bash
# Classificação simples
curl -X POST -F "file=@tampinha.jpg" http://localhost:8000/api/classify

# Validação completa (com ESP32)
curl -X POST -F "file=@tampinha.jpg" http://localhost:8000/api/validate-complete

# Health check
curl http://localhost:8000/api/health

# Health check ESP32
curl http://localhost:8000/api/esp32-health
```

---

## 📈 Métricas e Resultados

### Performance do Modelo
- **Acurácia**: 100% (treino) / 100% (validação)
- **Precisão**: 1.0
- **Recall**: 1.0
- **F1-Score**: 1.0

### Dataset
- **Total de imagens**: 4.430
- **Tampinhas**: 2.215 (50%)
- **Não-tampinhas**: 2.215 (50%)
- **Validação**: 200 imagens
- **Fonte**: Dataset customizado + fotos adicionais dos usuários

### Impacto Sustentável
- **Por tampinha**: ~0.5g de plástico reciclado
- **Benefícios**: Redução de CO2, economia de água, preservação de árvores
- **Cálculo automático** na interface

---

## 📁 Arquivos do Projeto

### Estrutura Principal
```
totem-ia/
├── app.py                 # Aplicação Flask principal
├── totem_ia_diagram.puml  # Diagrama de arquitetura PlantUML
├── requirements.txt       # Dependências Python
├── README.md             # Documentação completa
├── start_totem.py        # Script de inicialização
├── test_api.py           # Testes da API
├── test_upload_api.py    # Testes de upload
├── datasets/             # Conjunto de dados
├── src/                  # Código fonte
└── templates/            # Templates HTML
```

### Arquivos Importantes
- **`totem_ia_diagram.puml`**: Diagrama completo da arquitetura em PlantUML
- **`app.py`**: API Flask com endpoints de classificação e interface web
- **`svm_complete_classifier.py`**: Treinamento do modelo SVM
- **`README.md`**: Documentação técnica e de uso

---

## 🤝 Equipe

- **Caroline**: Líder Técnico & Backend Developer
- **Equipe FIAP**: Desenvolvimento colaborativo

---

## 📄 Licença

Este projeto é parte do Challenge FlexMedia - FIAP. Todos os direitos reservados ao grupo de desenvolvimento.

---

## 🎯 Contato

**Repositório GitHub**: [Grupo-S-faculdade-FIAP/totem-ia](https://github.com/Grupo-S-faculdade-FIAP/totem-ia)

---

## 🛠️ Ferramentas de Desenvolvimento

### Ambiente de Desenvolvimento
- **Editor**: Visual Studio Code
- **Versionamento**: Git + GitHub
- **Diagramas**: PlantUML (instalado via Homebrew)
- **Python**: 3.12 (compatível com Render)
- **Virtual Environment**: venv

### Extensões VS Code Recomendadas
- **Python** (Microsoft)
- **PlantUML** (jebbs.plantuml)
- **GitLens** (GitKraken)
- **Prettier** (formatação)

### Comandos Úteis
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py

# Gerar diagrama PlantUML
plantuml totem_ia_diagram.puml

# Validar sintaxe PlantUML
plantuml -checkonly totem_ia_diagram.puml
```

---

*Desenvolvido com ❤️ pela turma de Desenvolvimento de Soluções IoT com IA - FIAP*