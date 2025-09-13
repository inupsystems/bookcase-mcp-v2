# Prompt para Testar Agent API-Tester no VS Code

## Prompt Principal para Uso das Ferramentas

```
Olá! Agora temos acesso às ferramentas do JSONPlaceholder API através do sistema MCP. 

Por favor, execute os seguintes testes sequenciais para validar a integração:

## 1. TESTE DE LISTAGEM
Primeiro, liste todos os posts disponíveis para entender a estrutura da API:
- Use a ferramenta "Get all posts" 
- Configure parâmetros opcionais: {"_limit": 5} para limitar os resultados

## 2. TESTE DE BUSCA ESPECÍFICA  
Busque um post específico para validar parâmetros:
- Use a ferramenta "Get a specific post"
- Configure: {"id": 1}

## 3. TESTE DE CRIAÇÃO
Crie um novo post para testar operações POST:
- Use a ferramenta "Create a new post"
- Configure os dados: {
    "title": "Teste via MCP Agent",
    "body": "Este post foi criado através da integração MCP no VS Code",
    "userId": 1
  }

## 4. TESTE DE ATUALIZAÇÃO
Atualize o post criado para testar operações PUT:
- Use a ferramenta "Update a post" 
- Configure: {
    "id": 1,
    "title": "Post Atualizado via MCP",
    "body": "Conteúdo atualizado através do agent",
    "userId": 1
  }

## 5. TESTE DE USUÁRIOS
Liste usuários para validar outro endpoint:
- Use a ferramenta "Get all users"
- Sem parâmetros necessários: {}

## 6. TESTE DE USUÁRIO ESPECÍFICO
Busque um usuário específico:
- Use a ferramenta "Get a specific user"
- Configure: {"id": 1}

## 7. TESTE DE EXCLUSÃO
Por último, teste a exclusão (cuidado: pode não funcionar na API fake):
- Use a ferramenta "Delete a post"
- Configure: {"id": 1}

## VALIDAÇÕES ESPERADAS:
- Todas as ferramentas devem aparecer na lista de ferramentas disponíveis
- As chamadas devem retornar dados JSON válidos
- Os códigos de status HTTP devem ser 200/201 para sucesso
- Erros devem ser tratados adequadamente (ex: ID inexistente)

## RELATÓRIO SOLICITADO:
Após executar todos os testes, forneça um relatório incluindo:
1. Quais ferramentas funcionaram corretamente
2. Quais retornaram erros (se houver)
3. Tempos de resposta observados
4. Qualidade dos dados retornados
5. Sugestões de melhorias na integração

Execute cada teste em sequência e me informe os resultados de cada um.
```

## Prompts Específicos por Ferramenta

### Para Teste Rápido Individual:
```
Execute a ferramenta "Get all posts" com parâmetros {"_limit": 3} e me mostre o resultado formatado.
```

### Para Teste de Criação:
```
Crie um novo post usando a ferramenta "Create a new post" com os dados:
{
  "title": "Post de Teste MCP",
  "body": "Testando integração do agent-api-tester via MCP protocol no VS Code",
  "userId": 10
}
```

### Para Teste de Busca:
```
Busque o post com ID 5 usando a ferramenta "Get a specific post" e analise sua estrutura.
```

### Para Teste de Usuários:
```
Liste todos os usuários usando "Get all users" e depois busque detalhes do usuário ID 2 com "Get a specific user".
```

## Prompt para Análise de Performance:
```
Execute as seguintes operações em sequência e meça o tempo de resposta:

1. Get all posts (limite 10)
2. Get specific post (ID 1)
3. Get all users  
4. Get specific user (ID 1)
5. Create new post
6. Update post (ID 1)

Para cada operação, registre:
- Tempo de execução
- Tamanho da resposta
- Código de status HTTP
- Sucesso/falha

Forneça um relatório de performance ao final.
```

## Prompt para Teste de Robustez:
```
Execute testes de robustez das ferramentas:

1. **Teste com IDs inválidos:**
   - Get specific post com ID 99999
   - Get specific user com ID 99999

2. **Teste com dados inválidos:**
   - Create post sem campos obrigatórios
   - Update post com dados malformados

3. **Teste de limites:**
   - Get all posts com _limit muito alto (1000)
   - Get all posts com _limit negativo (-5)

4. **Teste de tipos incorretos:**
   - Usar string onde espera número
   - Usar array onde espera objeto

Documente todos os comportamentos observados e como a integração MCP lida com erros.
```

## Prompt para Validação de Schema:
```
Para cada ferramenta disponível:

1. Examine o schema de entrada (inputSchema)
2. Execute com dados válidos
3. Execute com dados inválidos  
4. Verifique se as validações estão funcionando
5. Teste campos opcionais vs obrigatórios

Gere um relatório de compatibilidade entre os schemas definidos e o comportamento real da API.
```

## Prompt de Troubleshooting:
```
Se alguma ferramenta não funcionar:

1. Verifique se está na lista de ferramentas disponíveis
2. Confirme o formato dos parâmetros de entrada
3. Execute sem parâmetros opcionais primeiro
4. Verifique logs de erro no console do VS Code
5. Teste conectividade com curl: curl https://jsonplaceholder.typicode.com/posts/1

Reporte qualquer problema encontrado com detalhes técnicos.
```

Estes prompts cobrem desde testes básicos até validações avançadas da integração MCP. Use-os conforme sua necessidade de teste!
