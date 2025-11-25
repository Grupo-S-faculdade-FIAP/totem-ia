# 🔐 Configuração de Login Admin

## Visão Geral
A página de login admin foi criada em `/admin` com a mesma interface visual do TOTEM IA.

## Rotas Disponíveis
- **`/admin`** - Página de login (padrão)
- **`/admin/login`** - Página de login (alternativa)
- **`/admin/dashboard`** - Dashboard admin (após login bem-sucedido)
- **`/api/admin/login`** - Endpoint de autenticação (POST)

## Configuração de Credenciais

### 1. Adicionar variáveis de ambiente ao `.env`

```bash
# Credenciais Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

> ⚠️ **IMPORTANTE**: Em produção, altere essas credenciais e use valores fortes!

### 2. Alternativa: Configuração via variáveis de sistema

```bash
export ADMIN_USERNAME="seu_usuario"
export ADMIN_PASSWORD="sua_senha_forte"
python app.py
```

## Como Usar

### 1. Acessar a página de login
```
http://localhost:5003/admin
```

### 2. Fazer login
- Digite o usuário (padrão: `admin`)
- Digite a senha (padrão: `admin123`)
- Opcional: Marque "Lembrar-me" para salvar o usuário no navegador
- Clique em "Entrar"

### 3. Após login bem-sucedido
- Será redirecionado para `/admin/dashboard`
- Acesso ao painel administrativo

## Funcionalidades Implementadas

✅ **Interface responsiva** - Mesmo design do TOTEM IA
✅ **Validação de formulário** - Campos obrigatórios
✅ **Armazenamento de preferência** - "Lembrar-me" usa localStorage
✅ **Animações suaves** - Transições CSS
✅ **Feedback visual** - Spinner durante autenticação
✅ **Mensagens de erro/sucesso** - Alertas estilizados
✅ **Cores e fontes** - Consistentes com a interface do totem

## Estrutura de Cores (Herdadas do Totem)

```css
Gradiente Principal: #667eea → #764ba2
Fundo: white
Texto: #333
Sucesso: #4CAF50
Erro: #f44336
```

## Próximas Etapas (Recomendadas)

1. **Implementar JWT (JSON Web Tokens)**
   - Substituir token simples por JWT para melhor segurança
   
2. **Adicionar proteção de rotas**
   - Verificar autenticação antes de acessar `/admin/dashboard`
   
3. **Sistema de roles e permissões**
   - Diferentes níveis de acesso (super-admin, moderador, etc.)
   
4. **Hash de senhas**
   - Usar bcrypt ou similar em vez de texto plano
   
5. **Rate limiting**
   - Limitar tentativas de login para evitar força bruta
   
6. **Logging de acesso**
   - Registrar tentativas de login (sucesso e falha)

## Teste de API (curl)

```bash
curl -X POST http://localhost:5003/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Resposta esperada:
```json
{
  "success": true,
  "message": "Login realizado com sucesso!",
  "token": "admin_token"
}
```

## Solução de Problemas

### "Usuário ou senha inválidos"
- Verifique se as credenciais no `.env` estão corretas
- Verifique se a variável de ambiente está sendo carregada

### Página em branco após login
- Verifique se `/admin/dashboard` existe e está funcionando
- Verifique o console do navegador para erros JavaScript

### CSS não está sendo aplicado
- Limpe o cache do navegador (Ctrl+F5 ou Cmd+Shift+R)
- Verifique se Font Awesome está disponível (CDN)

## Arquivos Criados/Modificados

✅ **Novo arquivo**: `templates/admin_login.html` - Página de login
✅ **Modificado**: `app.py` - Adicionadas rotas e API de autenticação
✅ **Novo arquivo**: `ADMIN_LOGIN_SETUP.md` - Este arquivo (documentação)

---

**Última atualização**: Novembro 2025

