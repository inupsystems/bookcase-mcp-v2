# 🚀 PROMPT DE TESTE - AGENT API TESTER

Use este prompt no chat do VS Code para testar as ferramentas integradas:

---

**TESTE COMPLETO DAS FERRAMENTAS MCP - AGENT API TESTER**

Execute os seguintes testes sequenciais usando as ferramentas disponíveis:

� **Teste 1 - Listar Posts**
- Ferramenta: `list_posts`
- Parâmetros: `{"_limit": 5}`
- Objetivo: Verificar listagem básica

� **Teste 2 - Buscar Post Específico**  
- Ferramenta: `get_post`
- Parâmetros: `{"id": 1}`
- Objetivo: Testar busca por ID

� **Teste 3 - Criar Novo Post**
- Ferramenta: `create_post`
- Parâmetros: `{"title": "Teste MCP", "body": "Post criado via MCP tools", "userId": 1}`
- Objetivo: Testar criação de dados

� **Teste 4 - Atualizar Post**
- Ferramenta: `update_post`
- Parâmetros: `{"id": 1, "title": "Post Atualizado", "body": "Conteúdo modificado", "userId": 1}`
- Objetivo: Testar modificação

� **Teste 5 - Listar Usuários**
- Ferramenta: `list_users`
- Parâmetros: `{}`
- Objetivo: Verificar endpoint sem parâmetros

🔸 **Teste 6 - Buscar Usuário**
- Ferramenta: `get_user`
- Parâmetros: `{"id": 1}`
- Objetivo: Testar busca de usuário

🔸 **Teste 7 - Deletar Post**
- Ferramenta: `delete_post`
- Parâmetros: `{"id": 1}`
- Objetivo: Testar remoção (executar por último)

**PARA CADA TESTE, REPORTE:**
- ✅ Status (sucesso/erro)
- ⏱️ Tempo de resposta
- 📊 Dados retornados (resumo)
- 🔧 Problemas encontrados

**FERRAMENTAS DISPONÍVEIS:**
- list_posts, create_post, get_post, update_post, delete_post
- list_users, get_user

Execute todos os testes e reporte os resultados de forma organizada.

---
