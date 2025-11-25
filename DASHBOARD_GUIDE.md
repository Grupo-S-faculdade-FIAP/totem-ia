# 📊 Guia do Dashboard Admin

## Visão Geral

Dashboard completo e interativo para gerenciar o sistema TOTEM IA com dados em tempo real sobre os depósitos de tampinhas.

## 🎯 Recursos Principais

### 1. **KPI Cards** (4 Cards de Métricas Principais)
- **Total de Tampinhas**: Número total de tampinhas processadas
  - Exibe tendência (% de crescimento)
  - Ícone visual (roxo)

- **Taxa de Aceite**: Percentual de tampinhas aceitas
  - Exibe variação comparada à semana anterior
  - Ícone visual (verde)

- **Rejeitadas**: Número de tampinhas rejeitadas
  - Exibe variação mensal
  - Ícone visual (vermelho)

- **Impacto Ambiental**: Quantidade de plástico reciclado
  - Calculado em kg (estimativa: 2g por tampinha)
  - Ícone visual (amarelo)

### 2. **Gráficos Interativos**

#### Distribuição de Status (Doughnut Chart)
- Visualiza a proporção entre aceitas e rejeitadas
- Cores: Verde (aceitas) e Vermelho (rejeitadas)
- Interativo com hover

#### Depósitos por Dia (Line Chart)
- Mostra tendência dos últimos 7 dias
- Linha suave com pontos interativos
- Eixos com formatação clara

### 3. **Tabela de Últimos Depósitos**
| Campo | Descrição |
|-------|-----------|
| ID | Identificador único do depósito |
| Horário | Hora do depósito |
| Tampinhas | Quantidade de itens |
| Status | Aceita ou Rejeitada (com badge colorido) |
| Confiança | Percentual de confiança da classificação |
| Ações | Botão para visualizar detalhes |

### 4. **Quick Stats**
Resumo de períodos diferentes:
- Hoje
- Esta Semana
- Este Mês
- Este Ano

## 🎨 Design

### Paleta de Cores (Consistente com Interface)
```css
Gradiente Principal:  #667eea → #764ba2 (Header)
Sucesso (Aceitas):    #4CAF50
Erro (Rejeitadas):    #f44336
Aviso:                #FFC107
Fundo:                #f5f7fa
Cards:                white
```

### Componentes
- **Header**: Gradiente roxo/azul com menu de logout
- **Cards**: Box com sombra suave, hover com elevação
- **Gráficos**: Chart.js com temas customizados
- **Tabela**: Responsiva com status badges coloridos
- **Botões**: Gradiente com efeito hover

## 🔗 Rotas

### Frontend
```
GET /admin/dashboard → Página do dashboard
```

### Backend
```
GET /api/admin/dashboard → Retorna dados do dashboard
```

### Resposta da API
```json
{
  "success": true,
  "stats": {
    "total": 5000,
    "aceitas": 4600,
    "rejeitadas": 400,
    "changeTotal": 12,
    "changeTaxa": 5,
    "changeRejeitadas": 8,
    "today": 200,
    "week": 1500,
    "month": 5000,
    "year": 55000
  },
  "trend": {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "values": [200, 220, 210, 240, 250, 230, 200]
  },
  "deposits": [
    {
      "id": 5123,
      "time": "14:35",
      "count": 5,
      "status": "aceita",
      "confidence": 95
    }
  ]
}
```

## 💻 Funcionalidades JavaScript

### Atualização em Tempo Real
- Os dados são atualizados a cada 30 segundos
- Gráficos são recriados com novos dados
- Tabela é atualizada dinamicamente

### Interações
- **Logout**: Botão no header para sair
- **Ver Detalhes**: Clique no ícone de olho na tabela
- **Hover**: Cards elevam-se, tabelas destacam linhas

### Responsividade
- Layout adapta para mobile
- Gráficos mantêm proporção
- Tabela scrollable em telas pequenas

## 📈 Dados Simulados

Os dados atualmente são **simulados** com valores aleatórios realistas:

```javascript
// Exemplo de geração
total_tampinhas = random(4500, 5500)
aceitas = total * 0.92 (92% de aceite)
rejeitadas = total - aceitas (8% de rejeição)
```

### Para Produção

Substitua a geração aleatória por consultas reais:
```python
# Exemplo com banco de dados
def api_admin_dashboard():
    stats = {
        'total': db.count_deposits(),
        'aceitas': db.count_accepted(),
        'rejeitadas': db.count_rejected(),
        # ... mais dados
    }
```

## 🎯 Dados Relevantes para o Negócio

### Métricas Principais
1. **Volume de Processamento**: Total de tampinhas processadas
2. **Taxa de Aceite**: Qualidade do modelo de IA
3. **Rejeições**: Identificar problemas
4. **Impacto Ambiental**: Valor de reciclagem (para marketing)

### Insights Visuais
- Gráfico de distribuição (proporção aceita/rejeitada)
- Tendência ao longo do tempo (acompanhar crescimento)
- Histórico recente (atividade)
- Estatísticas por período (tracking)

## 🔧 Como Customizar

### Alterar Cores
```css
/* Em admin_dashboard.html */
.card-icon.primary {
    color: #sua-cor;
    background: linear-gradient(...);
}
```

### Adicionar Novas Métricas
1. Adicione um novo card no HTML
2. Crie um novo campo em `stats` no app.py
3. Atualize `updateCards()` no JavaScript

### Modificar Atualização
```javascript
// Mudar intervalo de atualização (em ms)
setInterval(loadDashboard, 30000); // Altere o valor
```

## 📱 Responsividade

### Breakpoints
```css
Desktop:   > 768px (Grid completo)
Tablet:    481px - 768px (2 colunas)
Mobile:    ≤ 480px (1 coluna)
```

### Elementos Adaptáveis
- Cards em grid responsivo
- Gráficos com `maintainAspectRatio: true`
- Tabela com scroll horizontal
- Header com flex wrap

## 🔐 Segurança

### Implementar Antes de Produção
- [ ] Validar se usuário está autenticado
- [ ] Usar middleware de proteção de rota
- [ ] Validar token JWT
- [ ] Limitar acesso a dados sensíveis
- [ ] Adicionar logging de acesso
- [ ] Rate limiting na API

## 🚀 Próximas Etapas

### Curto Prazo
- [ ] Conectar a banco de dados real
- [ ] Implementar filtros por período
- [ ] Adicionar export de relatórios (CSV/PDF)

### Médio Prazo
- [ ] Dashboard em tempo real (WebSocket)
- [ ] Gráficos mais avançados
- [ ] Previsões com ML
- [ ] Alertas automáticos

### Longo Prazo
- [ ] Mobile app separado
- [ ] Integração com BI/Analytics
- [ ] Customização por usuário
- [ ] Múltiplos locais/TOTEMs

## 📊 Estatísticas de Implementação

| Métrica | Valor |
|---------|-------|
| Linhas de HTML | ~450 |
| Linhas de CSS | ~400 |
| Linhas de JavaScript | ~300 |
| Bibliotecas | Chart.js 3.9.1 |
| Templates | admin_dashboard.html |
| APIs | /api/admin/dashboard |

## 🎓 Arquitetura

```
Frontend (Client)
├── HTML Structure
│   ├── Header (boas-vindas + logout)
│   ├── KPI Cards (4 métricas)
│   ├── Charts (2 gráficos)
│   ├── Table (últimos depósitos)
│   └── Stats Grid (resumo por período)
├── CSS Styling
│   ├── Responsive Grid
│   ├── Cards com Hover
│   ├── Chart Customization
│   └── Mobile Breakpoints
└── JavaScript
    ├── Data Loading (fetch API)
    ├── Chart Rendering (Chart.js)
    ├── Dynamic Updates (auto-refresh)
    └── User Interactions

Backend (Server)
├── Route: GET /admin/dashboard
│   └── Serve admin_dashboard.html
└── API: GET /api/admin/dashboard
    └── Retorna dados (stats, charts, deposits)
```

## 💡 Dicas

1. **Atualização**: Os dados atualizam a cada 30 segundos automaticamente
2. **Responsivo**: Funciona em qualquer tamanho de tela
3. **Interativo**: Gráficos possuem hover interativo
4. **Seguro**: Validação no backend
5. **Escalável**: Fácil adicionar novas métricas

## 🐛 Solução de Problemas

### Gráficos não aparecem
- Verificar se Chart.js CDN está acessível
- Abrir console do navegador (F12) para erros

### Dados não atualizam
- Verificar se API `/api/admin/dashboard` está respondendo
- Verificar aba Network no DevTools

### Layout quebrado em mobile
- Limpar cache do navegador
- Verificar viewport meta tag

## 📧 Suporte

Consulte também:
- `ADMIN_LOGIN_SETUP.md` - Configuração de login
- `DESIGN_SPEC.md` - Especificação de design
- `QUICK_START_ADMIN.txt` - Guia rápido

---

**Dashboard versão:** 1.0
**Última atualização:** Novembro 2025
**Status:** ✅ Pronto para uso (com dados simulados)

