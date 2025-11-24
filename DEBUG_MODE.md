# 🐛 MODO DEBUG - Guia de Uso

## ⚠️ IMPORTANTE
- **Nunca use em produção!**
- Apenas para ambiente de **desenvolvimento local**
- Confirma tampinha automaticamente **sem validação de IA**

---

## Como Ativar

### 1. Editar `.env`
```bash
# Adicionar ou modificar:
MODO_DEBUG=true
```

### 2. Reiniciar o Flask
```bash
python app.py
```

Você verá no console:
```
🐛 ⚠️  MODO DEBUG ATIVADO! Botão de confirmação automática será exibido.
⚠️  NUNCA USE EM PRODUÇÃO!
```

---

## Como Usar

### Na Interface Web

1. **Iniciar Câmera**
   - Clique em "Iniciar Câmera"
   
2. **Tirar Foto**
   - Clique em "Capturar Foto"

3. **Dois Botões Aparecerão**
   - 🟠 **🐛 Modo Debug Confirmar** (novo!)
   - 🔵 **Classificar Tampinha** (padrão)

4. **Clique em "🐛 Modo Debug Confirmar"**
   - ⏭️ Pula toda validação ML
   - ✅ Tampinha é confirmada automaticamente
   - 🎯 Fluxo continua normalmente

---

## O Que Acontece

### Sem Debug (Normal)
```
Foto → Análise ML → Resultado (Aceita/Rejeita)
                      ↓
                  ESP32 Validação
                      ↓
                    Resultado Final
```

### Com Debug Confirmar
```
Foto → 🐛 Clique Debug → Resultado Simulado (Sempre Aceita)
                              ↓
                      ESP32 Validação Simulada
                              ↓
                       Resultado Final (Aceita)
```

---

## Fluxo Completo com Debug

1. **Etapa 1 (Classificação)**
   - Mensagem: "🐛 DEBUG: Classificação simulada..."
   - Tempo: Instantâneo

2. **Etapa 2 (Validação Mecânica)**
   - Mensagem: "🐛 DEBUG: Validação mecânica simulada..."
   - Sensores: Simulados (presença=true, peso=2500)

3. **Etapa 3 (Confirmação)**
   - Mensagem: "🐛 DEBUG: Finalizando..."
   - Resultado: ✅ TAMPINHA CONFIRMADA

---

## Resposta API `/api/debug-confirm`

```json
{
  "status": "sucesso",
  "message": "🐛 DEBUG: Tampinha confirmada automaticamente!",
  "stages": {
    "classificacao": {
      "status": "sucesso",
      "is_tampinha": true,
      "confidence": 0.99,
      "saturation": 95.5,
      "method": "DEBUG_AUTO_CONFIRM"
    },
    "mecanica": {
      "status": "sucesso",
      "presenca": true,
      "peso": 2500,
      "esp32_response": "DEBUG_SIMULATED"
    }
  },
  "debug_mode": true,
  "debug_note": "⚠️  RESPOSTA DE TESTE - NÃO USAR EM PRODUÇÃO",
  "timestamp": "2025-11-23T10:30:45.123456"
}
```

---

## Segurança

### Protegido por:
- ✅ Flag `MODO_DEBUG` no `.env`
- ✅ Verificação no backend: se `MODO_DEBUG=false`, endpoint retorna 403
- ✅ Botão só aparece se flag estiver ativa
- ✅ Endpoint documenta ser apenas para teste

### Não funciona em produção:
```python
if not MODO_DEBUG:
    return {"status": "erro", "message": "Endpoint não disponível"}, 403
```

---

## Desativar Debug

### 1. Editar `.env`
```bash
MODO_DEBUG=false
```

### 2. Reiniciar Flask
```bash
python app.py
```

### 3. Botão Desaparecerá
- Interface volta ao normal
- Apenas botão "Classificar Tampinha" aparecerá

---

## Testes Recomendados

### ✅ Testar com Debug
1. Ativar `MODO_DEBUG=true`
2. Tirar foto (qualquer imagem)
3. Clicar "🐛 Modo Debug Confirmar"
4. Verificar se continua o fluxo normal
5. Verificar screen finalization

### ✅ Testar sem Debug
1. Desativar `MODO_DEBUG=false`
2. Recarregar página
3. Botão debug deve desaparecer
4. Testar classificação normal com IA

### ✅ Testar Segurança
1. Ativar `MODO_DEBUG=true`
2. Ir até console browser
3. Tentar chamar `fetch('/api/debug-confirm')`
4. Deve funcionar

5. Desativar `MODO_DEBUG=false`
6. Tentar chamar API novamente
7. Deve retornar 403 Forbidden

---

## Logs no Console

### Quando clica Debug:
```
🐛 DEBUG: Usuário clicou em 'Modo Debug Confirmar'
⚠️  CONFIRMANDO TAMPINHA AUTOMATICAMENTE (SEM VALIDAÇÃO ML)
🐛 DEBUG: Resposta bem-sucedida do servidor
```

### Quando desativado:
```
❌ Tentativa de acessar /api/debug-confirm sem MODO_DEBUG ativado
```

---

## Troubleshooting

### ❓ Botão não aparece
- Verifique: `MODO_DEBUG=true` em `.env`
- Reinicie Flask: `python app.py`
- Recarregue browser: `Ctrl+F5` (hard refresh)

### ❓ Clique no debug não funciona
- Abra console do browser: `F12`
- Procure por erro
- Verifique se API está rodando

### ❓ Quer testar a API direto
```bash
# Com MODO_DEBUG=true:
curl -X POST http://localhost:8000/api/debug-confirm

# Resposta esperada: 200 OK com JSON

# Com MODO_DEBUG=false:
curl -X POST http://localhost:8000/api/debug-confirm

# Resposta esperada: 403 Forbidden
```

---

## Resumo

| Item | Valor |
|------|-------|
| **Flag** | `MODO_DEBUG` em `.env` |
| **Ativa** | `MODO_DEBUG=true` |
| **Desativa** | `MODO_DEBUG=false` |
| **Endpoint** | `POST /api/debug-confirm` |
| **Resposta** | JSON com "status": "sucesso" |
| **Segurança** | Protegido: só funciona com flag |
| **Produção** | ❌ Nunca use! |

---

*Criado para facilitar desenvolvimento e testes em ambiente local.*
