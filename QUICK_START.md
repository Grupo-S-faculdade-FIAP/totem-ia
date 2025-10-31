╔════════════════════════════════════════════════════════════════════════════════╗
║                     🚀 QUICK START - GUIA RÁPIDO                              ║
╚════════════════════════════════════════════════════════════════════════════════╝


1️⃣ INICIAR O SERVIDOR
═══════════════════════════════════════════════════════════════════════════════

$ cd /Users/caroline/Desktop/FIAP/totem-ia
$ source venv/bin/activate
$ python app.py

✓ Servidor rodando em http://localhost:5003


2️⃣ ACESSAR AS PÁGINAS
═══════════════════════════════════════════════════════════════════════════════

🏠 INICIAL (Intro + Áudio)
   http://localhost:5003/

📷 CÂMERA (Depositar Tampinhas)
   http://localhost:5003/totem_v2.html

🎮 DASHBOARD (Visualizar Pontos)
   http://localhost:5003/rewards

⏱️ PROCESSAMENTO (Automático, 3 segundos)
   http://localhost:5003/processing?points=10&total=60&caps=6


3️⃣ FLUXO DE USO
═══════════════════════════════════════════════════════════════════════════════

A) DEPOSITAR TAMPINHA:
   1. Acesse: /totem_v2.html
   2. Clique em "Iniciar Câmera"
   3. Capture foto da tampinha
   4. Clique em "Classificar Tampinha"
   5. Se ACEITA → Ganha 10 TAMPS → Tela de processamento (3 segundos)

B) VER SALDO E RANKING:
   1. Acesse: /rewards
   2. Visualize saldo em tempo real
   3. Veja ranking de usuários

C) RESGATAR PRÊMIO:
   1. No dashboard /rewards
   2. Escolha um parceiro
   3. Clique "Resgatar"
   4. Se tem pontos suficientes → Resgate confirmado


4️⃣ TESTES AUTOMATIZADOS
═══════════════════════════════════════════════════════════════════════════════

$ python test_rewards_system.py

Resultado esperado:
  ✅ 10/10 testes passando
  ✅ Tempo de execução: ~2-3 segundos
  ✅ Sem erros


5️⃣ EXEMPLOS PRÁTICOS
═══════════════════════════════════════════════════════════════════════════════

$ python exemplos_uso_recompensas.py

Menu interativo com 5 exemplos:
  1. Novo usuário deposita 10 tampinhas
  2. Consultar parceiros e resgatar
  3. Ver ranking com múltiplos usuários
  4. Histórico de transações
  5. Caso de uso completo (simulação)


6️⃣ ENDPOINTS DA API
═══════════════════════════════════════════════════════════════════════════════

POST /api/rewards/add-cap
├─ Body: { "user_id": "user123", "points": 10 }
└─ Retorna: success, message, points_awarded, user_data

GET /api/rewards/user/<user_id>
├─ Params: user_id
└─ Retorna: id, total_points, caps_deposited, created_at

GET /api/rewards/partners
├─ Params: nenhum
└─ Retorna: lista de 6 parceiros com ID, nome, descrição, pontos, ícone

POST /api/rewards/redeem
├─ Body: { "user_id": "user123", "partner_id": "starbucks" }
└─ Retorna: success, reward, remaining_points (ou error)

GET /api/rewards/leaderboard?limit=10
├─ Params: limit (padrão 10)
└─ Retorna: ranking de usuários com pontos e tampinhas


7️⃣ ESTRUTURA DE DADOS
═══════════════════════════════════════════════════════════════════════════════

USUÁRIO:
{
  "user_id": {
    "total_points": 60,
    "caps_deposited": 6,
    "created_at": "2025-10-31T11:30:00..."
  }
}

TRANSAÇÃO:
{
  "user_id": "user_123",
  "type": "deposit" | "redeem",
  "points": 10 | -100,
  "cap_type": "plastic",
  "partner_id": "starbucks",
  "timestamp": "2025-10-31T11:30:00..."
}

PARCEIRO:
{
  "id": "starbucks",
  "name": "Starbucks",
  "description": "Café grátis",
  "points_required": 100,
  "icon": "☕",
  "color": "#00704A"
}


8️⃣ PARCEIROS DISPONÍVEIS
═══════════════════════════════════════════════════════════════════════════════

1. ☕ Starbucks     → 100 TAMPS
2. 🥪 Subway        → 150 TAMPS
3. 🎬 Netflix       → 500 TAMPS
4. 🎵 Spotify       → 400 TAMPS
5. 🍕 Uber Eats     → 120 TAMPS
6. 📦 Amazon        → 250 TAMPS


9️⃣ TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

❌ Servidor não inicia?
   → Porta 5003 está ocupada?
   → Ative env: source venv/bin/activate
   → Instale deps: pip install -r requirements.txt

❌ Câmera não funciona?
   → Verificar permissões do navegador
   → Usar HTTPS ou localhost
   → Testar em /totem_v2.html

❌ API retorna 400?
   → Verificar JSON válido em POST
   → Validar user_id obrigatório
   → Consultar exemplos em exemplos_uso_recompensas.py

❌ Dashboard não carrega?
   → Abrir console (F12) e verificar erros
   → Limpar cache (Ctrl+Shift+Delete)
   → Certificar servidor rodando em 5003

❌ Pontos não persistem?
   → Verificar permissões em data/rewards/
   → Confirmar espaço em disco
   → Checar logs


🔟 ARQUIVOS IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

DOCUMENTAÇÃO:
  📄 SUMARIO_FINAL.md              ← VOCÊ ESTÁ AQUI!
  📄 IMPLEMENTATION_GUIDE.md       ← Guia completo
  📄 REWARDS_SYSTEM_README.md      ← Referência técnica

CÓDIGO:
  🐍 src/rewards_system.py         ← Core
  🐍 app.py                        ← API endpoints
  🐍 test_rewards_system.py        ← Testes
  🐍 exemplos_uso_recompensas.py   ← Exemplos

FRONTEND:
  🌐 templates/totem_v2.html       ← Câmera + integração
  🌐 templates/processing.html     ← Tela 3 segundos
  🌐 templates/rewards_dashboard.html ← Dashboard

DADOS:
  💾 data/rewards/users.json       ← BD usuários
  💾 data/rewards/transactions.json ← Histórico
  💾 data/rewards/partners.json    ← Parceiros


1️⃣1️⃣ COMO ADICIONAR MAIS PARCEIROS
═══════════════════════════════════════════════════════════════════════════════

1. Edite: data/rewards/partners.json
2. Adicione no array "partners":

{
  "id": "novo_parceiro",
  "name": "Nome da Empresa",
  "description": "Descrição do prêmio",
  "points_required": 100,
  "icon": "🎁",
  "color": "#FF5733"
}

3. Salve o arquivo
4. Recarregue o dashboard
5. Novo parceiro aparecerá automaticamente


1️⃣2️⃣ ESCALABILIDADE FUTURA
═══════════════════════════════════════════════════════════════════════════════

CURTO PRAZO (Fácil):
  • Mudar pontos padrão de 10 → 5 ou 20
  • Adicionar mais parceiros
  • Ajustar cores e ícones
  • Criar eventos especiais (dobro de pontos)

MÉDIO PRAZO (Moderado):
  • Migrar JSON → PostgreSQL
  • Adicionar autenticação
  • Sistema de notificações
  • Admin panel

LONGO PRAZO (Complexo):
  • App mobile
  • QR code para resgate
  • Machine Learning para bonificação
  • Integração com sistemas de fidelidade


📞 RESUMO RÁPIDO DOS ENDPOINTS
═══════════════════════════════════════════════════════════════════════════════

cURL examples:

# Criar tampinha
curl -X POST http://localhost:5003/api/rewards/add-cap \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","points":10}'

# Consultar usuário
curl http://localhost:5003/api/rewards/user/user123

# Listar parceiros
curl http://localhost:5003/api/rewards/partners

# Resgatar prêmio
curl -X POST http://localhost:5003/api/rewards/redeem \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","partner_id":"starbucks"}'

# Ranking
curl http://localhost:5003/api/rewards/leaderboard?limit=10


📋 CHECKLIST DE VERIFICAÇÃO
═══════════════════════════════════════════════════════════════════════════════

Antes de usar em produção:

□ Servidor Flask inicia sem erros
□ Câmera funciona em /totem_v2.html
□ Dashboard carrega em /rewards
□ Testes passam: python test_rewards_system.py
□ API responde em todos os 5 endpoints
□ Pontos são atribuídos corretamente
□ Ranking atualiza corretamente
□ Modal de resgate funciona
□ Responsividade em mobile OK
□ Animações suaves (60fps)


✨ RECURSOS ADICIONAIS
═══════════════════════════════════════════════════════════════════════════════

Documentação completa: IMPLEMENTATION_GUIDE.md
Referência técnica: REWARDS_SYSTEM_README.md
Exemplos práticos: python exemplos_uso_recompensas.py
Testes: python test_rewards_system.py


🎯 PRÓXIMOS PASSOS
═══════════════════════════════════════════════════════════════════════════════

1. Ative o servidor e teste em /rewards
2. Deposite algumas tampinhas em /totem_v2.html
3. Veja seus pontos atualizarem no dashboard
4. Tente resgatar uma recompensa
5. Consulte a documentação para customizações


╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    ✨ TUDO PRONTO PARA COMEÇAR! ✨                           ║
║                                                                                ║
║                  O sistema TAMPS está 100% funcional!                         ║
║                                                                                ║
║              Acesse http://localhost:5003/rewards agora!                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
